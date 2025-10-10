use axum::{
    extract::Request,
    http::{Method, StatusCode, Uri},
    response::IntoResponse,
    Router,
};
use pyo3::prelude::*;
use pyo3::types::PyTuple;
use serde_json::json;
use std::net::SocketAddr;
use std::sync::{Arc, Mutex};
use std::time::SystemTime;

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
    handler: PyObject,
    path_params: Vec<String>, // e.g., ["username"] for "/user/<username>"
    methods: Vec<String>, // e.g., ["GET", "POST"]
}

impl Clone for RouteInfo {
    fn clone(&self) -> Self {
        Python::with_gil(|py| RouteInfo {
            path: self.path.clone(),
            handler: self.handler.clone_ref(py),
            path_params: self.path_params.clone(),
            methods: self.methods.clone(),
        })
    }
}

#[pyclass]
struct Rupy {
    host: String,
    port: u16,
    routes: Arc<Mutex<Vec<RouteInfo>>>,
}

#[pymethods]
impl Rupy {
    #[new]
    fn new() -> Self {
        Rupy {
            host: "127.0.0.1".to_string(),
            port: 8000,
            routes: Arc::new(Mutex::new(Vec::new())),
        }
    }

    fn route(&self, path: String, handler: PyObject, methods: Vec<String>) -> PyResult<()> {
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

    #[pyo3(signature = (host=None, port=None))]
    fn run(&self, py: Python, host: Option<String>, port: Option<u16>) -> PyResult<()> {
        let host = host.unwrap_or_else(|| self.host.clone());
        let port = port.unwrap_or(self.port);
        let routes = self.routes.clone();

        // Release the GIL before running the async server
        py.allow_threads(|| {
            // Run the async server in a blocking context
            let runtime = tokio::runtime::Runtime::new().unwrap();
            runtime.block_on(async { run_server(&host, port, routes).await });
        });

        Ok(())
    }
}

async fn run_server(host: &str, port: u16, routes: Arc<Mutex<Vec<RouteInfo>>>) {
    // Prepare Python for freethreaded access
    pyo3::prepare_freethreaded_python();

    // Create a router that matches all routes
    let app = Router::new().fallback(move |method, uri, request| {
        let routes = routes.clone();
        async move { handler_request(method, uri, request, routes).await }
    });

    let addr = format!("{}:{}", host, port).parse::<SocketAddr>().unwrap();

    println!("Starting Rupy server on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
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

async fn handler_request(
    method: Method,
    uri: Uri,
    request: Request,
    routes: Arc<Mutex<Vec<RouteInfo>>>,
) -> axum::response::Response {
    let path = uri.path().to_string();
    let method_str = method.as_str();

    // Extract body for methods that support it (POST, PUT, PATCH, DELETE)
    let body = if method == Method::POST 
        || method == Method::PUT 
        || method == Method::PATCH 
        || method == Method::DELETE {
        match axum::body::to_bytes(request.into_body(), usize::MAX).await {
            Ok(bytes) => String::from_utf8_lossy(&bytes).to_string(),
            Err(_) => String::new(),
        }
    } else {
        String::new()
    };

    // Try to find a matching route
    let matched_route = {
        let routes_lock = routes.lock().unwrap();
        let mut matched: Option<(RouteInfo, Vec<String>)> = None;

        for route_info in routes_lock.iter() {
            // Check if path matches
            if let Some(param_values) = match_route(&path, &route_info.path) {
                // Check if method is supported by this route
                if route_info.methods.iter().any(|m| m == method_str) {
                    matched = Some((route_info.clone(), param_values));
                    break;
                }
            }
        }
        matched
    }; // routes_lock is dropped here

    // Now handle the matched route outside the lock
    if let Some((route_info, param_values)) = matched_route {
        let response = Python::with_gil(|py| {
            // Create PyRequest with method, path, and body
            let py_request =
                PyRequest::new(method_str.to_string(), path.clone(), body);

            // Call the handler with the request and path parameters
            let result = if param_values.is_empty() {
                // No parameters, just pass the request
                route_info.handler.call1(py, (py_request,))
            } else {
                // Pass request and parameters
                let mut args = vec![py_request.into_py(py)];
                for param in param_values {
                    args.push(param.into_py(py));
                }
                let py_tuple = PyTuple::new_bound(py, args);
                route_info.handler.call1(py, py_tuple)
            };

            match result {
                Ok(response) => {
                    // Extract the response
                    if let Ok(py_response) = response.extract::<PyResponse>(py) {
                        let status_code =
                            StatusCode::from_u16(py_response.status).unwrap_or(StatusCode::OK);
                        (status_code, py_response.body).into_response()
                    } else {
                        // Try to convert to string
                        if let Ok(response_str) = response.extract::<String>(py) {
                            (StatusCode::OK, response_str).into_response()
                        } else {
                            (
                                StatusCode::INTERNAL_SERVER_ERROR,
                                "Invalid response from handler",
                            )
                                .into_response()
                        }
                    }
                }
                Err(e) => {
                    eprintln!("Error calling Python handler: {:?}", e);
                    (StatusCode::INTERNAL_SERVER_ERROR, "Internal Server Error").into_response()
                }
            }
        });

        return response;
    }

    // No route matched or method not supported, return 404
    handler_404(method, Uri::from_maybe_shared(path).unwrap(), Request::default()).await
}

async fn handler_404(method: Method, uri: Uri, _request: Request) -> axum::response::Response {
    // Log the request in JSON format
    let timestamp = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_secs();

    let log_entry = json!({
        "timestamp": timestamp,
        "method": method.as_str(),
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
