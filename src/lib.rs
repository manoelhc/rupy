use axum::{
    extract::Request,
    http::{Method, StatusCode, Uri},
    response::IntoResponse,
    Router,
};
use opentelemetry::{global, KeyValue};
use opentelemetry_sdk::{metrics::SdkMeterProvider, trace::TracerProvider, Resource};
use opentelemetry_semantic_conventions as semcov;
use pyo3::prelude::*;
use pyo3::types::PyTuple;
use pyo3::IntoPyObjectExt;
use serde_json::json;
use std::net::SocketAddr;
use std::sync::{Arc, Mutex};
use std::time::{Instant, SystemTime};
use tower_http::trace::TraceLayer;
use tracing::{error, info, span, warn, Level};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

// Python Request wrapper
#[pyclass]
#[derive(Clone)]
pub struct PyRequest {
    #[pyo3(get)]
    method: String,
    #[pyo3(get)]
    path: String,
    #[pyo3(get)]
    body: String,
}

#[pymethods]
impl PyRequest {
    #[new]
    fn new(method: String, path: String, body: String) -> Self {
        PyRequest { method, path, body }
    }

    fn get_header(&self, _py: Python, _key: String) -> PyResult<Option<String>> {
        // For now, headers are not extracted from the request
        // This is a placeholder for future implementation
        Ok(None)
    }

    fn set_header(&mut self, _py: Python, _key: String, _value: String) -> PyResult<()> {
        // For now, this is a no-op
        // This is a placeholder for future implementation
        Ok(())
    }
}

// Python Response wrapper
#[pyclass]
#[derive(Clone)]
pub struct PyResponse {
    #[pyo3(get)]
    body: String,
    #[pyo3(get)]
    status: u16,
}

#[pymethods]
impl PyResponse {
    #[new]
    #[pyo3(signature = (body, status=200))]
    fn new(body: String, status: Option<u16>) -> Self {
        PyResponse {
            body,
            status: status.unwrap_or(200),
        }
    }
}

// Route information
struct RouteInfo {
    path: String,
    handler: Py<PyAny>,
    path_params: Vec<String>, // e.g., ["username"] for "/user/<username>"
    methods: Vec<String>,     // e.g., ["GET", "POST"]
}

impl Clone for RouteInfo {
    fn clone(&self) -> Self {
        Python::attach(|py| RouteInfo {
            path: self.path.clone(),
            handler: self.handler.clone_ref(py),
            path_params: self.path_params.clone(),
            methods: self.methods.clone(),
        })
    }
}

// Middleware information
struct MiddlewareInfo {
    handler: Py<PyAny>,
}

impl Clone for MiddlewareInfo {
    fn clone(&self) -> Self {
        Python::attach(|py| MiddlewareInfo {
            handler: self.handler.clone_ref(py),
        })
    }
}

// Telemetry configuration
#[derive(Clone)]
struct TelemetryConfig {
    enabled: bool,
    endpoint: Option<String>,
    service_name: String,
}

#[pyclass]
struct Rupy {
    host: String,
    port: u16,
    routes: Arc<Mutex<Vec<RouteInfo>>>,
    middlewares: Arc<Mutex<Vec<MiddlewareInfo>>>,
    telemetry_config: Arc<Mutex<TelemetryConfig>>,
}

#[pymethods]
impl Rupy {
    #[new]
    fn new() -> Self {
        // Check environment variables for initial configuration
        let service_name =
            std::env::var("OTEL_SERVICE_NAME").unwrap_or_else(|_| "rupy".to_string());
        let endpoint = std::env::var("OTEL_EXPORTER_OTLP_ENDPOINT").ok();
        let enabled = std::env::var("OTEL_ENABLED")
            .map(|v| v.to_lowercase() == "true" || v == "1")
            .unwrap_or(false);

        Rupy {
            host: "127.0.0.1".to_string(),
            port: 8000,
            routes: Arc::new(Mutex::new(Vec::new())),
            middlewares: Arc::new(Mutex::new(Vec::new())),
            telemetry_config: Arc::new(Mutex::new(TelemetryConfig {
                enabled,
                endpoint,
                service_name,
            })),
        }
    }

    fn route(&self, path: String, handler: Py<PyAny>, methods: Vec<String>) -> PyResult<()> {
        // Parse path parameters from the route pattern
        // e.g., "/user/<username>" -> path_params = ["username"]
        let path_params = parse_path_params(&path);

        let route_info = RouteInfo {
            path,
            handler,
            path_params,
            methods,
        };

        let mut routes = self.routes.lock().unwrap();
        routes.push(route_info);

        Ok(())
    }

    fn middleware(&self, handler: Py<PyAny>) -> PyResult<()> {
        let middleware_info = MiddlewareInfo { handler };

        let mut middlewares = self.middlewares.lock().unwrap();
        middlewares.push(middleware_info);

        Ok(())
    }

    /// Enable OpenTelemetry tracing, metrics, and logging
    #[pyo3(signature = (endpoint=None, service_name=None))]
    fn enable_telemetry(
        &self,
        endpoint: Option<String>,
        service_name: Option<String>,
    ) -> PyResult<()> {
        let mut config = self.telemetry_config.lock().unwrap();
        config.enabled = true;
        if let Some(ep) = endpoint {
            config.endpoint = Some(ep);
        }
        if let Some(name) = service_name {
            config.service_name = name;
        }
        info!("OpenTelemetry telemetry enabled");
        Ok(())
    }

    /// Disable OpenTelemetry telemetry
    fn disable_telemetry(&self) -> PyResult<()> {
        let mut config = self.telemetry_config.lock().unwrap();
        config.enabled = false;
        info!("OpenTelemetry telemetry disabled");
        Ok(())
    }

    /// Get current telemetry status
    fn is_telemetry_enabled(&self) -> PyResult<bool> {
        let config = self.telemetry_config.lock().unwrap();
        Ok(config.enabled)
    }

    /// Set the OpenTelemetry service name
    fn set_service_name(&self, name: String) -> PyResult<()> {
        let mut config = self.telemetry_config.lock().unwrap();
        config.service_name = name;
        Ok(())
    }

    /// Set the OpenTelemetry exporter endpoint
    fn set_telemetry_endpoint(&self, endpoint: String) -> PyResult<()> {
        let mut config = self.telemetry_config.lock().unwrap();
        config.endpoint = Some(endpoint);
        Ok(())
    }

    #[pyo3(signature = (host=None, port=None))]
    fn run(&self, py: Python, host: Option<String>, port: Option<u16>) -> PyResult<()> {
        let host = host.unwrap_or_else(|| self.host.clone());
        let port = port.unwrap_or(self.port);
        let routes = self.routes.clone();
        let middlewares = self.middlewares.clone();
        let telemetry_config = self.telemetry_config.clone();

        // Release the GIL before running the async server
        py.detach(|| {
            // Run the async server in a blocking context
            let runtime = tokio::runtime::Runtime::new().unwrap();
            runtime.block_on(async {
                run_server(&host, port, routes, middlewares, telemetry_config).await
            });
        });

        Ok(())
    }
}

// Initialize OpenTelemetry
fn init_telemetry(config: &TelemetryConfig) -> TelemetryGuard {
    let service_name = config.service_name.clone();

    // Create resource with service name
    let resource = Resource::new(vec![KeyValue::new(
        semcov::resource::SERVICE_NAME,
        service_name.clone(),
    )]);

    // Create basic tracer provider
    let tracer_provider = TracerProvider::builder()
        .with_resource(resource.clone())
        .build();

    global::set_tracer_provider(tracer_provider);

    // Create basic meter provider
    let meter_provider = SdkMeterProvider::builder().with_resource(resource).build();
    global::set_meter_provider(meter_provider);

    // Initialize tracing subscriber with basic layers (no OpenTelemetry layer for now to avoid version conflicts)
    let env_filter = std::env::var("RUST_LOG").unwrap_or_else(|_| "info".to_string());

    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(env_filter))
        .with(tracing_subscriber::fmt::layer().with_target(false).json())
        .init();

    info!("OpenTelemetry initialized with service: {}", service_name);

    TelemetryGuard
}

// Guard to ensure telemetry is properly shut down
struct TelemetryGuard;

impl Drop for TelemetryGuard {
    fn drop(&mut self) {
        info!("Shutting down telemetry");
    }
}

async fn run_server(
    host: &str,
    port: u16,
    routes: Arc<Mutex<Vec<RouteInfo>>>,
    middlewares: Arc<Mutex<Vec<MiddlewareInfo>>>,
    telemetry_config: Arc<Mutex<TelemetryConfig>>,
) {
    // Prepare Python for freethreaded access
    Python::initialize();

    // Initialize telemetry if enabled
    let config = telemetry_config.lock().unwrap().clone();
    let _telemetry_guard = if config.enabled {
        Some(init_telemetry(&config))
    } else {
        None
    };

    // Create a router that matches all routes
    let app = Router::new()
        .fallback(move |method, uri, request| {
            let routes = routes.clone();
            let middlewares = middlewares.clone();
            let telemetry_config = telemetry_config.clone();
            async move {
                handler_request(method, uri, request, routes, middlewares, telemetry_config).await
            }
        })
        .layer(TraceLayer::new_for_http());

    let addr = format!("{}:{}", host, port).parse::<SocketAddr>().unwrap();

    info!("Starting Rupy server on http://{}", addr);
    println!("Starting Rupy server on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();

    // Setup graceful shutdown signal handler
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await
        .unwrap();

    info!("Server shutdown complete");
    println!("Server shutdown complete");

    // Shutdown telemetry
    if config.enabled {
        global::shutdown_tracer_provider();
    }
}

// Handle shutdown signals (Ctrl+C)
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

// Parse path parameters from route pattern
// e.g., "/user/<username>" -> ["username"]
fn parse_path_params(path: &str) -> Vec<String> {
    let mut params = Vec::new();
    let mut in_param = false;
    let mut current_param = String::new();

    for c in path.chars() {
        match c {
            '<' => {
                in_param = true;
                current_param.clear();
            }
            '>' => {
                if in_param {
                    params.push(current_param.clone());
                    in_param = false;
                }
            }
            _ => {
                if in_param {
                    current_param.push(c);
                }
            }
        }
    }

    params
}

// Match request path against route patterns and extract parameters
fn match_route(request_path: &str, route_pattern: &str) -> Option<Vec<String>> {
    // Simple string matching for exact paths and basic parameter extraction

    let route_parts: Vec<&str> = route_pattern.split('/').collect();
    let request_parts: Vec<&str> = request_path.split('/').collect();

    if route_parts.len() != request_parts.len() {
        return None;
    }

    let mut params = Vec::new();

    for (route_part, request_part) in route_parts.iter().zip(request_parts.iter()) {
        if route_part.starts_with('<') && route_part.ends_with('>') {
            // This is a parameter
            params.push(request_part.to_string());
        } else if route_part != request_part {
            // Literal parts must match exactly
            return None;
        }
    }

    Some(params)
}

// Helper function to record metrics
fn record_metrics(
    telemetry_config: &Arc<Mutex<TelemetryConfig>>,
    method_str: &str,
    path: &str,
    status_code: u16,
    duration: std::time::Duration,
) {
    let is_enabled = {
        let config = telemetry_config.lock().unwrap();
        config.enabled
    };

    if is_enabled {
        let service_name = {
            let config = telemetry_config.lock().unwrap();
            config.service_name.clone()
        };

        // Get meter and record metrics (leak the string to get 'static lifetime)
        let meter = global::meter(Box::leak(service_name.into_boxed_str()));
        let counter = meter
            .u64_counter("http.server.requests")
            .with_description("Total number of HTTP requests")
            .build();
        let histogram = meter
            .f64_histogram("http.server.duration")
            .with_description("HTTP request duration in seconds")
            .with_unit("s")
            .build();

        counter.add(
            1,
            &[
                KeyValue::new("http.method", method_str.to_string()),
                KeyValue::new("http.route", path.to_string()),
                KeyValue::new("http.status_code", status_code as i64),
            ],
        );

        histogram.record(
            duration.as_secs_f64(),
            &[
                KeyValue::new("http.method", method_str.to_string()),
                KeyValue::new("http.route", path.to_string()),
                KeyValue::new("http.status_code", status_code as i64),
            ],
        );
    }
}

async fn handler_request(
    method: Method,
    uri: Uri,
    request: Request,
    routes: Arc<Mutex<Vec<RouteInfo>>>,
    middlewares: Arc<Mutex<Vec<MiddlewareInfo>>>,
    telemetry_config: Arc<Mutex<TelemetryConfig>>,
) -> axum::response::Response {
    let start_time = Instant::now();
    let path = uri.path().to_string();
    let method_str = method.as_str().to_string();

    // Create a span for this request
    let span = span!(
        Level::INFO,
        "http_request",
        http.method = %method_str,
        http.route = %path,
        http.scheme = "http",
    );
    let _enter = span.enter();

    info!("Handling request: {} {}", method_str, path);

    // Extract body for methods that support it (POST, PUT, PATCH, DELETE)
    let body = if method == Method::POST
        || method == Method::PUT
        || method == Method::PATCH
        || method == Method::DELETE
    {
        match axum::body::to_bytes(request.into_body(), usize::MAX).await {
            Ok(bytes) => String::from_utf8_lossy(&bytes).to_string(),
            Err(_) => String::new(),
        }
    } else {
        String::new()
    };

    // Execute middlewares
    let middleware_result = {
        let middlewares_lock = middlewares.lock().unwrap();
        let middlewares_list = middlewares_lock.clone();
        drop(middlewares_lock);

        Python::attach(|py| {
            // Create PyRequest with method, path, and body
            let mut py_request = PyRequest::new(method_str.clone(), path.clone(), body.clone());

            // Execute each middleware in order
            for middleware_info in middlewares_list.iter() {
                let result = middleware_info.handler.call1(py, (py_request.clone(),));

                match result {
                    Ok(response) => {
                        // Check if middleware returned a Response (early termination)
                        if let Ok(py_response) = response.extract::<PyResponse>(py) {
                            let status_code =
                                StatusCode::from_u16(py_response.status).unwrap_or(StatusCode::OK);
                            let status_u16 = status_code.as_u16();
                            return Some(((status_code, py_response.body).into_response(), status_u16));
                        }
                        // Otherwise, middleware might have modified the request
                        // Try to extract updated request
                        if let Ok(updated_request) = response.extract::<PyRequest>(py) {
                            py_request = updated_request;
                        }
                    }
                    Err(e) => {
                        error!("Error calling middleware: {:?}", e);
                        return Some((
                            (StatusCode::INTERNAL_SERVER_ERROR, "Middleware Error").into_response(),
                            500,
                        ));
                    }
                }
            }

            // No middleware returned early, pass the (possibly modified) request forward
            None
        })
    };

    // If middleware returned a response, return it
    if let Some((response, status_code)) = middleware_result {
        let duration = start_time.elapsed();
        record_metrics(&telemetry_config, &method_str, &path, status_code, duration);
        info!("Request completed: {} - Duration: {:?}", status_code, duration);
        return response;
    }

    // Try to find a matching route
    let matched_route = {
        let routes_lock = routes.lock().unwrap();
        let mut matched: Option<(RouteInfo, Vec<String>)> = None;

        for route_info in routes_lock.iter() {
            // Check if path matches
            if let Some(param_values) = match_route(&path, &route_info.path) {
                // Check if method is supported by this route
                if route_info.methods.iter().any(|m| m == &method_str) {
                    matched = Some((route_info.clone(), param_values));
                    break;
                }
            }
        }
        matched
    }; // routes_lock is dropped here

    // Now handle the matched route outside the lock
    let (response, status_code) = if let Some((route_info, param_values)) = matched_route {
        let handler_span =
            span!(Level::INFO, "handler_execution", handler.route = %route_info.path);
        let _handler_enter = handler_span.enter();

        let resp = Python::attach(|py| {
            // Create PyRequest with method, path, and body
            let py_request = PyRequest::new(method_str.clone(), path.clone(), body);

            // Call the handler with the request and path parameters
            let result = if param_values.is_empty() {
                // No parameters, just pass the request
                route_info.handler.call1(py, (py_request,))
            } else {
                // Pass request and parameters
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
                    // Extract the response
                    if let Ok(py_response) = response.extract::<PyResponse>(py) {
                        let status_code =
                            StatusCode::from_u16(py_response.status).unwrap_or(StatusCode::OK);
                        let status_u16 = status_code.as_u16();
                        ((status_code, py_response.body).into_response(), status_u16)
                    } else {
                        // Try to convert to string
                        if let Ok(response_str) = response.extract::<String>(py) {
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
        // No route matched or method not supported, return 404
        let resp = handler_404(Uri::from_maybe_shared(path.clone()).unwrap()).await;
        (resp, 404)
    };

    // Record metrics
    let duration = start_time.elapsed();
    record_metrics(&telemetry_config, &method_str, &path, status_code, duration);

    info!(
        "Request completed: {} - Duration: {:?}",
        status_code, duration
    );

    response
}

async fn handler_404(uri: Uri) -> axum::response::Response {
    // Log the request in JSON format
    let timestamp = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_secs();

    warn!(
        path = %uri.path(),
        status = 404,
        "Route not found"
    );

    let log_entry = json!({
        "timestamp": timestamp,
        "path": uri.path(),
        "status": 404,
        "message": "Not Found"
    });

    println!("{}", log_entry);

    (StatusCode::NOT_FOUND, "404 Not Found").into_response()
}

#[pymodule]
fn rupy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Rupy>()?;
    m.add_class::<PyRequest>()?;
    m.add_class::<PyResponse>()?;
    Ok(())
}
