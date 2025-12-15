use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::{Arc, Mutex};
use std::time::{Instant, SystemTime};

use axum::{
    extract::Request,
    http::{Method, StatusCode, Uri},
    response::IntoResponse,
    Router,
};
use pyo3::{prelude::*, types::PyTuple, Bound, IntoPyObjectExt};
use tower_http::trace::TraceLayer;
use tracing::{error, info, span, warn, Level};

use crate::request::{parse_cookies, PyRequest};
use crate::response::{build_response, PyResponse};
use crate::routing::{match_route, MiddlewareInfo, RouteInfo};
use crate::telemetry::{init_telemetry, record_metrics, TelemetryConfig, TelemetryGuard};
use crate::template::render_template_with_dirs;
use crate::upload::process_multipart_upload;

pub async fn run_server(
    host: &str,
    port: u16,
    routes: Arc<Mutex<Vec<RouteInfo>>>,
    middlewares: Arc<Mutex<Vec<MiddlewareInfo>>>,
    telemetry_config: Arc<Mutex<TelemetryConfig>>,
    template_config: Arc<Mutex<crate::template::TemplateConfig>>,
) -> Result<(), Box<dyn std::error::Error>> {
    Python::initialize();

    let config = telemetry_config.lock().unwrap().clone();
    let _telemetry_guard: Option<TelemetryGuard> = if config.enabled {
        Some(init_telemetry(&config))
    } else {
        None
    };

    let app = Router::new()
        .fallback(move |method, uri, request| {
            let routes = routes.clone();
            let middlewares = middlewares.clone();
            let telemetry_config = telemetry_config.clone();
            let template_config = template_config.clone();
            async move {
                handler_request(
                    method,
                    uri,
                    request,
                    routes,
                    middlewares,
                    telemetry_config,
                    template_config,
                )
                .await
            }
        })
        .layer(TraceLayer::new_for_http());

    let addr = format!("{}:{}", host, port).parse::<SocketAddr>()?;

    info!("Starting Rupy server on http://{}", addr);
    println!("Starting Rupy server on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .map_err(|e| format!("Failed to bind to {}: {}", addr, e))?;

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    info!("Server shutdown complete");
    println!("Server shutdown complete");
    Ok(())
}

async fn shutdown_signal() {
    use tokio::signal;

    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {
            println!("\nReceived Ctrl+C, shutting down gracefully...");
        },
        _ = terminate => {
            println!("\nReceived terminate signal, shutting down gracefully...");
        },
    }
}

async fn handler_request(
    method: Method,
    uri: Uri,
    request: Request,
    routes: Arc<Mutex<Vec<RouteInfo>>>,
    middlewares: Arc<Mutex<Vec<MiddlewareInfo>>>,
    telemetry_config: Arc<Mutex<TelemetryConfig>>,
    template_config: Arc<Mutex<crate::template::TemplateConfig>>,
) -> axum::response::Response {
    let start_time = Instant::now();
    let path = uri.path().to_string();
    let method_str = method.as_str().to_string();

    let headers_map = request.headers().clone();
    let mut headers = HashMap::new();
    for (key, value) in headers_map.iter() {
        if let Ok(value_str) = value.to_str() {
            headers.insert(key.as_str().to_string(), value_str.to_string());
        }
    }

    let user_agent = headers
        .get("user-agent")
        .cloned()
        .unwrap_or_else(|| "unknown".to_string());

    let cookies = if let Some(cookie_header) = headers.get("cookie") {
        parse_cookies(cookie_header)
    } else {
        HashMap::new()
    };

    let span = span!(
        Level::INFO,
        "http_request",
        http.method = %method_str,
        http.route = %path,
        http.scheme = "http",
        http.user_agent = %user_agent,
    );
    let _enter = span.enter();

    info!(
        "Handling request: {} {} - User-Agent: {}",
        method_str, path, user_agent
    );

    let matched_route = {
        let routes_lock = routes.lock().unwrap();
        let mut matched: Option<(RouteInfo, Vec<String>)> = None;

        for route_info in routes_lock.iter() {
            if let Some(param_values) = match_route(&path, &route_info.path) {
                if route_info.methods.iter().any(|m| m == &method_str) {
                    matched = Some((route_info.clone(), param_values));
                    break;
                }
            }
        }
        matched
    };

    // Check if this is an upload route first, but don't process yet
    let is_upload_route = if let Some((ref route_info, _)) = matched_route {
        route_info.is_upload
    } else {
        false
    };

    // For upload routes, we need to process middleware before consuming the body
    // For non-upload routes, we read the body first
    let (body, request_body) = if is_upload_route {
        // Don't consume the body yet for upload routes
        (String::new(), Some(request))
    } else if method == Method::POST
        || method == Method::PUT
        || method == Method::PATCH
        || method == Method::DELETE
    {
        // TODO: make it configurable via app method
        const MAX_BODY_SIZE: usize = 10 * 1024 * 1024; // 10MB default
        match axum::body::to_bytes(request.into_body(), MAX_BODY_SIZE).await {
            Ok(bytes) => (String::from_utf8_lossy(&bytes).to_string(), None),
            Err(e) => {
                error!("Body read error: {}", e);
                let duration = start_time.elapsed();
                record_metrics(&telemetry_config, &method_str, &path, 413, duration);
                return (StatusCode::PAYLOAD_TOO_LARGE, "Request body too large").into_response();
            }
        }
    } else {
        (String::new(), None)
    };

    // Now handle upload routes with middleware applied
    if let Some((ref route_info, _)) = matched_route {
        if route_info.is_upload {
            let request_body = match request_body {
                Some(body) => body,
                None => {
                    error!("Upload route missing request body");
                    let duration = start_time.elapsed();
                    record_metrics(&telemetry_config, &method_str, &path, 500, duration);
                    return (StatusCode::INTERNAL_SERVER_ERROR, "Internal Server Error")
                        .into_response();
                }
            };

            // Process middleware for upload routes
            let middleware_result_upload = {
                let middlewares_lock = middlewares.lock().unwrap();
                let middlewares_list = middlewares_lock.clone();
                drop(middlewares_lock);

                Python::attach(|py| {
                    let mut py_request = PyRequest::from_parts(
                        method_str.clone(),
                        path.clone(),
                        String::new(), // No body for upload routes in middleware
                        headers.clone(),
                        cookies.clone(),
                    );

                    for middleware_info in middlewares_list.iter() {
                        let result = middleware_info.handler.call1(py, (py_request.clone(),));

                        match result {
                            Ok(response) => {
                                if let Ok(py_response) = response.extract::<PyResponse>(py) {
                                    let status_u16 = py_response.status;
                                    return Ok((build_response(py_response), status_u16));
                                }
                                if let Ok(updated_request) = response.extract::<PyRequest>(py) {
                                    py_request = updated_request;
                                }
                            }
                            Err(e) => {
                                error!("Error calling middleware: {:?}", e);
                                return Ok((
                                    (StatusCode::INTERNAL_SERVER_ERROR, "Middleware Error")
                                        .into_response(),
                                    500,
                                ));
                            }
                        }
                    }

                    // Return the modified request
                    Err(py_request)
                })
            };

            // Check if middleware returned an early response
            let py_request_after_middleware = match middleware_result_upload {
                Ok((response, status_code)) => {
                    let duration = start_time.elapsed();
                    record_metrics(&telemetry_config, &method_str, &path, status_code, duration);
                    info!(
                        "Request completed: {} - Duration: {:?}",
                        status_code, duration
                    );
                    return response;
                }
                Err(modified_request) => modified_request,
            };

            let content_type = headers.get("content-type").cloned().unwrap_or_default();

            let boundary = if let Some(boundary_start) = content_type.find("boundary=") {
                let boundary_str = &content_type[boundary_start + 9..];
                let boundary_str = boundary_str.trim();
                if boundary_str.starts_with('"') && boundary_str.contains('"') {
                    let end_quote = boundary_str[1..]
                        .find('"')
                        .unwrap_or(boundary_str.len() - 1);
                    boundary_str[1..=end_quote].to_string()
                } else {
                    boundary_str
                        .split(';')
                        .next()
                        .unwrap_or(boundary_str)
                        .trim()
                        .to_string()
                }
            } else {
                error!("Missing boundary in multipart/form-data request");
                let duration = start_time.elapsed();
                record_metrics(&telemetry_config, &method_str, &path, 400, duration);
                return (StatusCode::BAD_REQUEST, "Missing boundary in Content-Type")
                    .into_response();
            };

            let upload_config = route_info.upload_config.as_ref().unwrap();

            match process_multipart_upload(request_body.into_body(), boundary, upload_config).await
            {
                Ok(uploaded_files) => {
                    let resp = Python::attach(|py| {
                        // Use the modified request from middleware
                        let py_request = py_request_after_middleware.clone();

                        let py_files = pyo3::types::PyList::empty(py);
                        for file in uploaded_files {
                            let py_file = Bound::new(py, file).unwrap();
                            let _ = py_files.append(py_file);
                        }

                        let result = route_info.handler.call1(py, (py_request, py_files.clone()));

                        match result {
                            Ok(response) => {
                                if let Ok(py_response) = response.extract::<PyResponse>(py) {
                                    let status_u16 = py_response.status;
                                    (build_response(py_response), status_u16)
                                } else if let Ok(response_str) = response.extract::<String>(py) {
                                    ((StatusCode::OK, response_str).into_response(), 200)
                                } else {
                                    error!("Invalid response from upload handler");
                                    (
                                        (
                                            StatusCode::INTERNAL_SERVER_ERROR,
                                            "Invalid response from handler",
                                        )
                                            .into_response(),
                                        500,
                                    )
                                }
                            }
                            Err(e) => {
                                error!("Error calling Python upload handler: {:?}", e);
                                (
                                    (StatusCode::INTERNAL_SERVER_ERROR, "Internal Server Error")
                                        .into_response(),
                                    500,
                                )
                            }
                        }
                    });

                    let duration = start_time.elapsed();
                    record_metrics(&telemetry_config, &method_str, &path, resp.1, duration);
                    info!("Request completed: {} - Duration: {:?}", resp.1, duration);
                    return resp.0;
                }
                Err(e) => {
                    error!("Upload error: {}", e);
                    let duration = start_time.elapsed();
                    record_metrics(&telemetry_config, &method_str, &path, 400, duration);
                    return (StatusCode::BAD_REQUEST, format!("Upload error: {}", e))
                        .into_response();
                }
            }
        }
    }

    // Process middleware and get either an early response or modified request
    let middleware_result = {
        let middlewares_lock = middlewares.lock().unwrap();
        let middlewares_list = middlewares_lock.clone();
        drop(middlewares_lock);

        Python::attach(|py| {
            let mut py_request = PyRequest::from_parts(
                method_str.clone(),
                path.clone(),
                body.clone(),
                headers.clone(),
                cookies.clone(),
            );

            for middleware_info in middlewares_list.iter() {
                let result = middleware_info.handler.call1(py, (py_request.clone(),));

                match result {
                    Ok(response) => {
                        if let Ok(py_response) = response.extract::<PyResponse>(py) {
                            let status_u16 = py_response.status;
                            return Ok((build_response(py_response), status_u16));
                        }
                        if let Ok(updated_request) = response.extract::<PyRequest>(py) {
                            py_request = updated_request;
                        }
                    }
                    Err(e) => {
                        error!("Error calling middleware: {:?}", e);
                        return Ok((
                            (StatusCode::INTERNAL_SERVER_ERROR, "Middleware Error").into_response(),
                            500,
                        ));
                    }
                }
            }

            // Return the modified request wrapped in Err to distinguish from early responses
            Err(py_request)
        })
    };

    // Check if middleware returned an early response
    let py_request_after_middleware = match middleware_result {
        Ok((response, status_code)) => {
            let duration = start_time.elapsed();
            record_metrics(&telemetry_config, &method_str, &path, status_code, duration);
            info!(
                "Request completed: {} - Duration: {:?}",
                status_code, duration
            );
            return response;
        }
        Err(modified_request) => modified_request,
    };

    let (response, status_code) = if let Some((route_info, param_values)) = matched_route {
        let handler_span =
            span!(Level::INFO, "handler_execution", handler.route = %route_info.path);
        let _handler_enter = handler_span.enter();

        let resp = Python::attach(|py| {
            // Use the modified request from middleware instead of creating a new one
            let py_request = py_request_after_middleware.clone();

            let result = if param_values.is_empty() {
                route_info.handler.call1(py, (py_request,))
            } else {
                let py_request_bound = Bound::new(py, py_request).unwrap();
                let mut args: Vec<Bound<PyAny>> = vec![py_request_bound.into_any()];
                for param in param_values {
                    args.push(param.into_bound_py_any(py).unwrap());
                }
                let py_tuple = PyTuple::new(py, &args).unwrap();
                route_info.handler.call1(py, py_tuple)
            };

            match result {
                Ok(response) => {
                    if route_info.is_template {
                        if let Ok(py_dict) = response.cast_bound::<pyo3::types::PyDict>(py) {
                            let mut context = serde_json::Map::new();
                            for (key, value) in py_dict.iter() {
                                if let Ok(key_str) = key.extract::<String>() {
                                    let json_value = if let Ok(s) = value.extract::<String>() {
                                        serde_json::Value::String(s)
                                    } else if let Ok(i) = value.extract::<i64>() {
                                        serde_json::Value::Number(i.into())
                                    } else if let Ok(f) = value.extract::<f64>() {
                                        if let Some(n) = serde_json::Number::from_f64(f) {
                                            serde_json::Value::Number(n)
                                        } else {
                                            serde_json::Value::String(f.to_string())
                                        }
                                    } else if let Ok(b) = value.extract::<bool>() {
                                        serde_json::Value::Bool(b)
                                    } else if value.is_none() {
                                        serde_json::Value::Null
                                    } else {
                                        serde_json::Value::String(value.to_string())
                                    };
                                    context.insert(key_str, json_value);
                                }
                            }

                            let template_dirs =
                                template_config.lock().unwrap().template_dirs.clone();
                            let template_name = route_info.template_name.as_ref().unwrap();

                            match render_template_with_dirs(
                                &template_dirs,
                                template_name,
                                &serde_json::Value::Object(context),
                            ) {
                                Ok(rendered) => {
                                    let mut response =
                                        axum::response::Response::new(rendered.into());
                                    response.headers_mut().insert(
                                        axum::http::header::CONTENT_TYPE,
                                        axum::http::HeaderValue::from_str(&route_info.content_type)
                                            .unwrap(),
                                    );
                                    (response, 200)
                                }
                                Err(e) => {
                                    error!("Template rendering error: {:?}", e);
                                    (
                                        (
                                            StatusCode::INTERNAL_SERVER_ERROR,
                                            format!("Template rendering error: {}", e),
                                        )
                                            .into_response(),
                                        500,
                                    )
                                }
                            }
                        } else {
                            error!("Template handler must return a dict");
                            (
                                (
                                    StatusCode::INTERNAL_SERVER_ERROR,
                                    "Template handler must return a dict",
                                )
                                    .into_response(),
                                500,
                            )
                        }
                    } else if let Ok(py_response) = response.extract::<PyResponse>(py) {
                        let status_u16 = py_response.status;
                        (build_response(py_response), status_u16)
                    } else if let Ok(response_str) = response.extract::<String>(py) {
                        ((StatusCode::OK, response_str).into_response(), 200)
                    } else {
                        error!("Invalid response from handler");
                        (
                            (
                                StatusCode::INTERNAL_SERVER_ERROR,
                                "Invalid response from handler",
                            )
                                .into_response(),
                            500,
                        )
                    }
                }
                Err(e) => {
                    error!("Error calling Python handler: {:?}", e);
                    (
                        (StatusCode::INTERNAL_SERVER_ERROR, "Internal Server Error")
                            .into_response(),
                        500,
                    )
                }
            }
        });

        resp
    } else {
        let resp = handler_404(Uri::from_maybe_shared(path.clone()).unwrap()).await;
        (resp, 404)
    };

    let duration = start_time.elapsed();
    record_metrics(&telemetry_config, &method_str, &path, status_code, duration);

    info!(
        "Request completed: {} - Duration: {:?}",
        status_code, duration
    );

    response
}

async fn handler_404(uri: Uri) -> axum::response::Response {
    let timestamp = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_secs();

    warn!(
        path = %uri.path(),
        status = 404,
        "Route not found"
    );

    let log_entry = serde_json::json!({
        "timestamp": timestamp,
        "path": uri.path(),
        "status": 404,
        "message": "Not Found"
    });

    println!("{}", log_entry);

    (StatusCode::NOT_FOUND, "404 Not Found").into_response()
}
