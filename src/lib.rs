use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use tokio::runtime::Runtime;
use axum::{
    Router,
    extract::{State, Request as AxumRequest},
    response::{Response as AxumResponse, IntoResponse},
    http::StatusCode,
    body::Body,
};
use std::net::SocketAddr;
use http_body_util::BodyExt;
use regex::Regex;

#[derive(Clone)]
struct RouteInfo {
    pattern: Regex,
    param_names: Vec<String>,
    methods: Vec<String>,
    handler: Arc<Mutex<Option<PyObject>>>,
}

#[derive(Clone)]
struct AppState {
    routes: Arc<Mutex<Vec<RouteInfo>>>,
}

/// Python Request class
#[pyclass(name = "Request")]
#[derive(Clone)]
struct PyRequest {
    #[pyo3(get)]
    method: String,
    #[pyo3(get)]
    path: String,
    #[pyo3(get)]
    headers: HashMap<String, String>,
    body: Vec<u8>,
    #[pyo3(get)]
    path_params: HashMap<String, String>,
    #[pyo3(get)]
    query_params: HashMap<String, String>,
}

#[pymethods]
impl PyRequest {
    fn json(&self, py: Python) -> PyResult<PyObject> {
        let json_str = String::from_utf8(self.body.clone())
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid UTF-8: {}", e)))?;
        
        let json_module = py.import_bound("json")?;
        let loads = json_module.getattr("loads")?;
        let result = loads.call1((json_str,))?;
        Ok(result.into())
    }

    fn text(&self) -> PyResult<String> {
        String::from_utf8(self.body.clone())
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid UTF-8: {}", e)))
    }

    fn body(&self) -> PyResult<Vec<u8>> {
        Ok(self.body.clone())
    }
}

/// Python Response class
#[pyclass(name = "Response")]
#[derive(Clone)]
struct PyResponse {
    #[pyo3(get)]
    status: u16,
    #[pyo3(get)]
    content_type: String,
    body_data: Vec<u8>,
    #[pyo3(get)]
    headers: HashMap<String, String>,
}

#[pymethods]
impl PyResponse {
    #[new]
    #[pyo3(signature = (body, status=200, headers=None, content_type=None))]
    fn new(
        body: PyObject,
        status: Option<u16>,
        headers: Option<HashMap<String, String>>,
        content_type: Option<String>,
    ) -> PyResult<Self> {
        Python::with_gil(|py| {
            let status = status.unwrap_or(200);
            let headers = headers.unwrap_or_default();
            
            // Handle different body types
            let (body_bytes, detected_content_type) = if let Ok(s) = body.extract::<String>(py) {
                (s.into_bytes(), "text/plain".to_string())
            } else if let Ok(b) = body.extract::<Vec<u8>>(py) {
                (b, "application/octet-stream".to_string())
            } else {
                // Try to serialize as JSON
                let json_module = py.import_bound("json")?;
                let dumps = json_module.getattr("dumps")?;
                let json_str = dumps.call1((body,))?;
                let s: String = json_str.extract()?;
                (s.into_bytes(), "application/json".to_string())
            };

            let content_type = content_type.unwrap_or(detected_content_type);

            Ok(PyResponse {
                status,
                content_type,
                body_data: body_bytes,
                headers,
            })
        })
    }

    #[getter]
    fn body(&self, py: Python) -> PyResult<PyObject> {
        Ok(PyBytes::new_bound(py, &self.body_data).into())
    }

    fn set_header(&mut self, key: String, value: String) {
        self.headers.insert(key, value);
    }
}

/// Main Rupy application class
#[pyclass(name = "Rupy")]
struct PyRupy {
    routes: Arc<Mutex<Vec<RouteInfo>>>,
}

#[pymethods]
impl PyRupy {
    #[new]
    fn new(_module_name: PyObject) -> PyResult<Self> {
        Ok(PyRupy {
            routes: Arc::new(Mutex::new(Vec::new())),
        })
    }

    fn _register_route(&mut self, path: String, methods: Vec<String>, handler: PyObject) -> PyResult<()> {
        let (pattern, param_names) = compile_path_pattern(&path);

        let route_info = RouteInfo {
            pattern,
            param_names,
            methods: methods.iter().map(|m| m.to_uppercase()).collect(),
            handler: Arc::new(Mutex::new(Some(handler))),
        };

        self.routes.lock().unwrap().push(route_info);
        Ok(())
    }

    fn run(&mut self, host: String, port: u16) -> PyResult<()> {
        let routes = self.routes.clone();

        // Create a new Tokio runtime
        let runtime = Runtime::new()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                format!("Failed to create runtime: {}", e)
            ))?;

        runtime.block_on(async move {
            let app_state = AppState {
                routes: routes.clone(),
            };

            let app = Router::new()
                .fallback(handle_request)
                .with_state(app_state);

            let addr: SocketAddr = format!("{}:{}", host, port)
                .parse()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("Invalid address: {}", e)
                ))?;

            println!("Starting Rupy server on http://{}:{}", host, port);

            let listener = tokio::net::TcpListener::bind(addr)
                .await
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Failed to bind: {}", e)
                ))?;

            axum::serve(listener, app)
                .await
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Server error: {}", e)
                ))?;

            Ok::<(), PyErr>(())
        })?;

        Ok(())
    }
}

// Helper function to compile path patterns
fn compile_path_pattern(path: &str) -> (Regex, Vec<String>) {
    let mut pattern = String::from("^");
    let mut param_names = Vec::new();

    let param_re = Regex::new(r"<([^>]+)>").unwrap();
    let mut last_end = 0;

    for cap in param_re.captures_iter(path) {
        let match_obj = cap.get(0).unwrap();
        let param_name = cap.get(1).unwrap().as_str();

        // Add literal part before this capture
        pattern.push_str(&regex::escape(&path[last_end..match_obj.start()]));

        // Add capture group for parameter
        pattern.push_str(r"([^/]+)");
        param_names.push(param_name.to_string());

        last_end = match_obj.end();
    }

    // Add remaining literal part
    pattern.push_str(&regex::escape(&path[last_end..]));
    pattern.push('$');

    (Regex::new(&pattern).unwrap(), param_names)
}

async fn handle_request(
    State(state): State<AppState>,
    req: AxumRequest,
) -> impl IntoResponse {
    let method = req.method().to_string();
    let path = req.uri().path().to_string();
    let headers: HashMap<String, String> = req
        .headers()
        .iter()
        .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
        .collect();

    // Parse query parameters
    let query_params: HashMap<String, String> = req
        .uri()
        .query()
        .map(|q| {
            url::form_urlencoded::parse(q.as_bytes())
                .map(|(k, v)| (k.into_owned(), v.into_owned()))
                .collect()
        })
        .unwrap_or_default();

    // Read body
    let body_bytes = match req.into_body().collect().await {
        Ok(collected) => collected.to_bytes().to_vec(),
        Err(_) => Vec::new(),
    };

    // Find matching route and get handler
    let handler_and_params = {
        let routes_guard = state.routes.lock().unwrap();
        eprintln!("DEBUG: Checking {} routes for path: {}, method: {}", routes_guard.len(), path, method);
        routes_guard.iter().find_map(|route| {
            eprintln!("DEBUG: Checking route pattern, methods: {:?}", route.methods);
            if !route.methods.contains(&method.to_uppercase()) {
                eprintln!("DEBUG: Method mismatch");
                return None;
            }

            if let Some(caps) = route.pattern.captures(&path) {
                eprintln!("DEBUG: Pattern matched!");
                let mut path_params = HashMap::new();
                for (i, name) in route.param_names.iter().enumerate() {
                    if let Some(value) = caps.get(i + 1) {
                        path_params.insert(name.clone(), value.as_str().to_string());
                    }
                }

                // Clone the PyObject within the GIL
                let handler_opt = Python::with_gil(|py| {
                    eprintln!("DEBUG: Getting handler");
                    route.handler.lock().unwrap().as_ref().map(|h| h.clone_ref(py))
                });

                eprintln!("DEBUG: Handler found: {}", handler_opt.is_some());
                handler_opt.map(|h| (h, path_params))
            } else {
                eprintln!("DEBUG: Pattern did not match");
                None
            }
        })
    };

    eprintln!("DEBUG: Handler and params found: {}", handler_and_params.is_some());

    if let Some((handler, path_params)) = handler_and_params {
        eprintln!("DEBUG: About to call Python handler");
        // Call Python handler
        let result = Python::with_gil(|py| -> PyResult<AxumResponse> {
            // Create Request object
            let py_request = PyRequest {
                method: method.clone(),
                path: path.clone(),
                headers: headers.clone(),
                body: body_bytes.clone(),
                path_params: path_params.clone(),
                query_params: query_params.clone(),
            };

            // Call handler
            let request_obj = Py::new(py, py_request)?;

            let result = if !path_params.is_empty() {
                // Call with path parameters as keyword arguments
                let kwargs = PyDict::new_bound(py);
                kwargs.set_item("request", request_obj)?;
                for (k, v) in path_params.iter() {
                    kwargs.set_item(k, v)?;
                }
                handler.call_bound(py, (), Some(&kwargs))?
            } else {
                // Call with just request
                handler.call1(py, (request_obj,))?
            };

            // Extract response
            let response: PyRef<PyResponse> = result.extract(py)?;

            // Build Axum response
            let mut axum_response = AxumResponse::builder()
                .status(StatusCode::from_u16(response.status).unwrap_or(StatusCode::OK));

            // Add headers
            for (k, v) in response.headers.iter() {
                axum_response = axum_response.header(k, v);
            }

            // Add content-type
            axum_response = axum_response.header("Content-Type", &response.content_type);

            // Build response with body
            Ok(axum_response
                .body(Body::from(response.body_data.clone()))
                .unwrap())
        });

        return match result {
            Ok(resp) => resp,
            Err(e) => {
                eprintln!("Error calling handler: {:?}", e);
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal Server Error").into_response()
            }
        };
    }

    // No route matched
    (StatusCode::NOT_FOUND, "Not Found").into_response()
}

#[pymodule]
fn rupy_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyRequest>()?;
    m.add_class::<PyResponse>()?;
    m.add_class::<PyRupy>()?;
    Ok(())
}
