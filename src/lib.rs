use axum::{
    body::Body,
    extract::Request,
    http::{Method, StatusCode, Uri},
    response::IntoResponse,
    Router,
};
use handlebars::Handlebars;
use multer::Multipart;
use opentelemetry::{global, KeyValue};
use opentelemetry_sdk::{metrics::SdkMeterProvider, trace::SdkTracerProvider, Resource};
use opentelemetry_semantic_conventions as semcov;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};
use pyo3::IntoPyObjectExt;
use serde_json::json;
use std::collections::HashMap;
use std::io::Write;
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::time::{Instant, SystemTime};
use tempfile::NamedTempFile;
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
    headers: HashMap<String, String>,
    cookies: HashMap<String, String>,
}

#[pymethods]
impl PyRequest {
    #[new]
    fn new(method: String, path: String, body: String) -> Self {
        PyRequest {
            method,
            path,
            body,
            headers: HashMap::new(),
            cookies: HashMap::new(),
        }
    }

    fn get_header(&self, _py: Python, key: String) -> PyResult<Option<String>> {
        Ok(self.headers.get(&key).cloned())
    }

    fn set_header(&mut self, _py: Python, key: String, value: String) -> PyResult<()> {
        self.headers.insert(key, value);
        Ok(())
    }

    #[getter]
    fn headers(&self, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        for (key, value) in &self.headers {
            dict.set_item(key, value)?;
        }
        Ok(dict.into())
    }

    /// Get a cookie value by name
    fn get_cookie(&self, _py: Python, name: String) -> PyResult<Option<String>> {
        Ok(self.cookies.get(&name).cloned())
    }

    /// Set a cookie value (for middleware/handler use)
    fn set_cookie(&mut self, _py: Python, name: String, value: String) -> PyResult<()> {
        self.cookies.insert(name, value);
        Ok(())
    }

    /// Get all cookies as a dictionary
    #[getter]
    fn cookies(&self, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        for (key, value) in &self.cookies {
            dict.set_item(key, value)?;
        }
        Ok(dict.into())
    }

    /// Get the auth token from the Authorization header (Bearer token)
    #[getter]
    fn auth_token(&self, _py: Python) -> PyResult<Option<String>> {
        if let Some(auth_header) = self.headers.get("authorization") {
            if let Some(token) = auth_header.strip_prefix("Bearer ") {
                return Ok(Some(token.to_string()));
            }
        }
        Ok(None)
    }

    /// Set the auth token in the Authorization header (Bearer token)
    #[setter(auth_token)]
    fn set_auth_token(&mut self, _py: Python, token: String) -> PyResult<()> {
        self.headers
            .insert("authorization".to_string(), format!("Bearer {}", token));
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
    headers: HashMap<String, String>,
    cookies: Vec<String>, // Store Set-Cookie headers
}

#[pymethods]
impl PyResponse {
    #[new]
    #[pyo3(signature = (body, status=200))]
    fn new(body: String, status: Option<u16>) -> Self {
        PyResponse {
            body,
            status: status.unwrap_or(200),
            headers: HashMap::new(),
            cookies: Vec::new(),
        }
    }

    fn get_header(&self, _py: Python, key: String) -> PyResult<Option<String>> {
        Ok(self.headers.get(&key).cloned())
    }

    fn set_header(&mut self, _py: Python, key: String, value: String) -> PyResult<()> {
        self.headers.insert(key, value);
        Ok(())
    }

    #[getter]
    fn headers(&self, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        for (key, value) in &self.headers {
            dict.set_item(key, value)?;
        }
        Ok(dict.into())
    }

    /// Set a cookie on the response
    ///
    /// Args:
    ///     name: Cookie name
    ///     value: Cookie value
    ///     max_age: Optional max age in seconds
    ///     path: Optional cookie path (default: "/")
    ///     domain: Optional domain
    ///     secure: Whether cookie should only be sent over HTTPS
    ///     http_only: Whether cookie should be HTTP-only (not accessible via JavaScript)
    ///     same_site: SameSite attribute ("Strict", "Lax", or "None")
    #[pyo3(signature = (name, value, max_age=None, path=None, domain=None, secure=false, http_only=false, same_site=None))]
    #[allow(clippy::too_many_arguments)]
    fn set_cookie(
        &mut self,
        _py: Python,
        name: String,
        value: String,
        max_age: Option<i64>,
        path: Option<String>,
        domain: Option<String>,
        secure: bool,
        http_only: bool,
        same_site: Option<String>,
    ) -> PyResult<()> {
        let mut cookie = format!("{}={}", name, value);

        if let Some(age) = max_age {
            cookie.push_str(&format!("; Max-Age={}", age));
        }

        cookie.push_str(&format!(
            "; Path={}",
            path.unwrap_or_else(|| "/".to_string())
        ));

        if let Some(d) = domain {
            cookie.push_str(&format!("; Domain={}", d));
        }

        if secure {
            cookie.push_str("; Secure");
        }

        if http_only {
            cookie.push_str("; HttpOnly");
        }

        if let Some(ss) = same_site {
            cookie.push_str(&format!("; SameSite={}", ss));
        }

        self.cookies.push(cookie);
        Ok(())
    }

    /// Delete a cookie by setting it to expire immediately
    #[pyo3(signature = (name, path=None, domain=None))]
    fn delete_cookie(
        &mut self,
        _py: Python,
        name: String,
        path: Option<String>,
        domain: Option<String>,
    ) -> PyResult<()> {
        let mut cookie = format!("{}=; Max-Age=0", name);

        cookie.push_str(&format!(
            "; Path={}",
            path.unwrap_or_else(|| "/".to_string())
        ));

        if let Some(d) = domain {
            cookie.push_str(&format!("; Domain={}", d));
        }

        self.cookies.push(cookie);
        Ok(())
    }
}

// Python UploadFile wrapper
#[pyclass]
#[derive(Clone)]
pub struct PyUploadFile {
    #[pyo3(get)]
    filename: String,
    #[pyo3(get)]
    content_type: String,
    #[pyo3(get)]
    size: u64,
    #[pyo3(get)]
    path: String,
}

#[pymethods]
impl PyUploadFile {
    #[new]
    fn new(filename: String, content_type: String, size: u64, path: String) -> Self {
        PyUploadFile {
            filename,
            content_type,
            size,
            path,
        }
    }

    /// Get the file name
    fn get_filename(&self) -> PyResult<String> {
        Ok(self.filename.clone())
    }

    /// Get the content type (MIME type)
    fn get_content_type(&self) -> PyResult<String> {
        Ok(self.content_type.clone())
    }

    /// Get the file size in bytes
    fn get_size(&self) -> PyResult<u64> {
        Ok(self.size)
    }

    /// Get the temporary file path where the file is stored
    fn get_path(&self) -> PyResult<String> {
        Ok(self.path.clone())
    }
}

// Upload configuration
#[derive(Clone)]
struct UploadConfig {
    accepted_mime_types: Vec<String>,
    max_size: Option<u64>,
    upload_dir: String,
}

// Route information
struct RouteInfo {
    path: String,
    handler: Py<PyAny>,
    path_params: Vec<String>, // e.g., ["username"] for "/user/<username>"
    methods: Vec<String>,     // e.g., ["GET", "POST"]
    is_template: bool,        // Whether this route is a template route
    template_name: Option<String>, // Template file name (e.g., "index.tpl")
    content_type: String,     // Content type for the response
    is_upload: bool,          // Whether this route handles file uploads
    upload_config: Option<UploadConfig>, // Upload configuration
}

impl Clone for RouteInfo {
    fn clone(&self) -> Self {
        Python::attach(|py| RouteInfo {
            path: self.path.clone(),
            handler: self.handler.clone_ref(py),
            path_params: self.path_params.clone(),
            methods: self.methods.clone(),
            is_template: self.is_template,
            template_name: self.template_name.clone(),
            content_type: self.content_type.clone(),
            is_upload: self.is_upload,
            upload_config: self.upload_config.clone(),
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

// Template configuration
#[derive(Clone)]
struct TemplateConfig {
    template_dir: String,
    template_dirs: Vec<String>,
}

#[pyclass]
struct Rupy {
    host: String,
    port: u16,
    routes: Arc<Mutex<Vec<RouteInfo>>>,
    middlewares: Arc<Mutex<Vec<MiddlewareInfo>>>,
    telemetry_config: Arc<Mutex<TelemetryConfig>>,
    template_config: Arc<Mutex<TemplateConfig>>,
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
            template_config: Arc::new(Mutex::new(TemplateConfig {
                template_dir: "./template".to_string(),
                template_dirs: vec!["./template".to_string()],
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
            is_template: false,
            template_name: None,
            content_type: "text/html".to_string(),
            is_upload: false,
            upload_config: None,
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

    /// Register a template route
    fn route_template(
        &self,
        path: String,
        handler: Py<PyAny>,
        methods: Vec<String>,
        template_name: String,
        content_type: String,
    ) -> PyResult<()> {
        let path_params = parse_path_params(&path);

        let route_info = RouteInfo {
            path,
            handler,
            path_params,
            methods,
            is_template: true,
            template_name: Some(template_name),
            content_type,
            is_upload: false,
            upload_config: None,
        };

        let mut routes = self.routes.lock().unwrap();
        routes.push(route_info);

        Ok(())
    }

    /// Register an upload route
    #[pyo3(signature = (path, handler, methods, accepted_mime_types=None, max_size=None, upload_dir=None))]
    fn route_upload(
        &self,
        path: String,
        handler: Py<PyAny>,
        methods: Vec<String>,
        accepted_mime_types: Option<Vec<String>>,
        max_size: Option<u64>,
        upload_dir: Option<String>,
    ) -> PyResult<()> {
        let path_params = parse_path_params(&path);

        let upload_config = UploadConfig {
            accepted_mime_types: accepted_mime_types.unwrap_or_default(),
            max_size,
            upload_dir: upload_dir.unwrap_or_else(|| {
                // Use a more secure default than /tmp
                std::env::temp_dir()
                    .join("rupy-uploads")
                    .to_string_lossy()
                    .to_string()
            }),
        };

        let route_info = RouteInfo {
            path,
            handler,
            path_params,
            methods,
            is_template: false,
            template_name: None,
            content_type: "application/json".to_string(),
            is_upload: true,
            upload_config: Some(upload_config),
        };

        let mut routes = self.routes.lock().unwrap();
        routes.push(route_info);

        Ok(())
    }

    /// Set the template directory
    fn set_template_dir(&self, dir: String) -> PyResult<()> {
        let mut config = self.template_config.lock().unwrap();
        config.template_dir = dir.clone();
        // Also clear and set the template_dirs to only this directory
        config.template_dirs = vec![dir];
        Ok(())
    }

    /// Get the template directory
    fn get_template_dir(&self) -> PyResult<String> {
        let config = self.template_config.lock().unwrap();
        Ok(config.template_dir.clone())
    }

    /// Add a template directory to the search path
    fn add_template_dir(&self, dir: String) -> PyResult<()> {
        let mut config = self.template_config.lock().unwrap();
        if !config.template_dirs.contains(&dir) {
            config.template_dirs.push(dir);
        }
        Ok(())
    }

    /// Remove a template directory from the search path
    fn remove_template_dir(&self, dir: String) -> PyResult<()> {
        let mut config = self.template_config.lock().unwrap();
        config.template_dirs.retain(|d| d != &dir);
        Ok(())
    }

    /// Get all template directories
    fn get_template_dirs(&self) -> PyResult<Vec<String>> {
        let config = self.template_config.lock().unwrap();
        Ok(config.template_dirs.clone())
    }

    /// Render a template with context data
    fn render_template_string(
        &self,
        template_name: String,
        context: Py<PyDict>,
    ) -> PyResult<String> {
        Python::attach(|py| {
            let config = self.template_config.lock().unwrap();
            let dirs = config.template_dirs.clone();
            drop(config); // Release lock before rendering

            // Convert Python dict to JSON value
            let json_context = py_dict_to_json(py, &context)?;

            // Try to render the template
            render_template_with_dirs(&dirs, &template_name, &json_context)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))
        })
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
        let template_config = self.template_config.clone();

        // Release the GIL before running the async server
        py.detach(|| {
            // Run the async server in a blocking context
            let runtime = tokio::runtime::Runtime::new().unwrap();
            runtime.block_on(async {
                run_server(
                    &host,
                    port,
                    routes,
                    middlewares,
                    telemetry_config,
                    template_config,
                )
                .await
            });
        });

        Ok(())
    }
}

// Initialize OpenTelemetry
fn init_telemetry(config: &TelemetryConfig) -> TelemetryGuard {
    let service_name = config.service_name.clone();

    // Create resource with service name
    let resource = Resource::builder()
        .with_attribute(KeyValue::new(
            semcov::resource::SERVICE_NAME,
            service_name.clone(),
        ))
        .build();

    // Create basic tracer provider
    let tracer_provider = SdkTracerProvider::builder()
        .with_resource(resource.clone())
        .build();

    global::set_tracer_provider(tracer_provider.clone());

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

    TelemetryGuard {
        tracer_provider: Some(tracer_provider),
    }
}

// Guard to ensure telemetry is properly shut down
struct TelemetryGuard {
    tracer_provider: Option<SdkTracerProvider>,
}

impl Drop for TelemetryGuard {
    fn drop(&mut self) {
        if let Some(provider) = self.tracer_provider.take() {
            info!("Shutting down telemetry");
            let _ = provider.shutdown();
        }
    }
}

async fn run_server(
    host: &str,
    port: u16,
    routes: Arc<Mutex<Vec<RouteInfo>>>,
    middlewares: Arc<Mutex<Vec<MiddlewareInfo>>>,
    telemetry_config: Arc<Mutex<TelemetryConfig>>,
    template_config: Arc<Mutex<TemplateConfig>>,
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

    // Telemetry shutdown is handled by the Drop implementation of TelemetryGuard
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
    // Supports wildcard path parameters like <param:path> that match remaining segments

    let route_parts: Vec<&str> = route_pattern.split('/').collect();
    let request_parts: Vec<&str> = request_path.split('/').collect();

    let mut params = Vec::new();
    let mut route_idx = 0;
    let mut request_idx = 0;

    while route_idx < route_parts.len() {
        let route_part = route_parts[route_idx];
        
        if route_part.starts_with('<') && route_part.ends_with('>') {
            // This is a parameter
            let param_content = &route_part[1..route_part.len()-1];
            
            // Check if it's a wildcard path parameter (e.g., <filepath:path>)
            if param_content.contains(":path") {
                // Match all remaining request parts
                if request_idx < request_parts.len() {
                    let remaining = &request_parts[request_idx..];
                    params.push(remaining.join("/"));
                    request_idx = request_parts.len();
                    route_idx += 1;
                } else {
                    // No remaining parts to match
                    params.push(String::new());
                    route_idx += 1;
                }
            } else {
                // Regular parameter - match one segment
                if request_idx < request_parts.len() {
                    params.push(request_parts[request_idx].to_string());
                    request_idx += 1;
                    route_idx += 1;
                } else {
                    // Not enough request parts
                    return None;
                }
            }
        } else {
            // Literal part must match exactly
            if request_idx >= request_parts.len() || route_part != request_parts[request_idx] {
                return None;
            }
            request_idx += 1;
            route_idx += 1;
        }
    }

    // All route parts matched; check if all request parts were consumed
    if request_idx == request_parts.len() {
        Some(params)
    } else {
        None
    }
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

// Parse cookies from Cookie header
fn parse_cookies(cookie_header: &str) -> HashMap<String, String> {
    let mut cookies = HashMap::new();
    for cookie in cookie_header.split(';') {
        let cookie = cookie.trim();
        if let Some(eq_pos) = cookie.find('=') {
            let name = cookie[..eq_pos].trim().to_string();
            let value = cookie[eq_pos + 1..].trim().to_string();
            cookies.insert(name, value);
        }
    }
    cookies
}

// Build an axum response from PyResponse with headers and cookies
fn build_response(py_response: PyResponse) -> axum::response::Response {
    use axum::http::header::{HeaderMap, HeaderName, HeaderValue};
    use axum::response::IntoResponse;

    let status_code = StatusCode::from_u16(py_response.status).unwrap_or(StatusCode::OK);
    let body = py_response.body;

    // Build header map
    let mut header_map = HeaderMap::new();
    for (key, value) in py_response.headers.iter() {
        if let Ok(header_name) = HeaderName::from_bytes(key.as_bytes()) {
            if let Ok(header_value) = HeaderValue::from_str(value) {
                header_map.insert(header_name, header_value);
            }
        }
    }

    // Add Set-Cookie headers
    for cookie in py_response.cookies.iter() {
        if let Ok(cookie_value) = HeaderValue::from_str(cookie) {
            header_map.append("set-cookie", cookie_value);
        }
    }

    (status_code, header_map, body).into_response()
}

// Render a template using Handlebars with multiple directory support
fn render_template_with_dirs(
    template_dirs: &[String],
    template_name: &str,
    context: &serde_json::Value,
) -> Result<String, String> {
    let mut handlebars = Handlebars::new();

    // Try to find and read the template file from the list of directories
    let mut template_content = None;
    let mut tried_paths = Vec::new();

    for template_dir in template_dirs {
        let template_path = PathBuf::from(template_dir).join(template_name);
        tried_paths.push(template_path.display().to_string());

        if let Ok(content) = std::fs::read_to_string(&template_path) {
            template_content = Some(content);
            break;
        }
    }

    let template_content = template_content.ok_or_else(|| {
        format!(
            "Failed to read template file '{}'. Tried paths: {}",
            template_name,
            tried_paths.join(", ")
        )
    })?;

    // Register the template
    handlebars
        .register_template_string("template", template_content)
        .map_err(|e| format!("Failed to parse template: {}", e))?;

    // Render the template
    handlebars
        .render("template", context)
        .map_err(|e| format!("Failed to render template: {}", e))
}

// Render a template using Handlebars (backward compatibility)
fn render_template(
    template_dir: &str,
    template_name: &str,
    context: &serde_json::Value,
) -> Result<String, String> {
    render_template_with_dirs(&[template_dir.to_string()], template_name, context)
}

// Helper function to convert Python dict to JSON
fn py_dict_to_json(py: Python, py_dict: &Py<PyDict>) -> PyResult<serde_json::Value> {
    let dict = py_dict.bind(py);
    let mut context = serde_json::Map::new();

    for (key, value) in dict.iter() {
        let key_str = key.extract::<String>()?;
        let json_value = if let Ok(s) = value.extract::<String>() {
            serde_json::Value::String(s)
        } else if let Ok(i) = value.extract::<i64>() {
            serde_json::Value::Number(i.into())
        } else if let Ok(f) = value.extract::<f64>() {
            serde_json::Value::Number(
                serde_json::Number::from_f64(f)
                    .unwrap_or_else(|| serde_json::Number::from(0)),
            )
        } else if let Ok(b) = value.extract::<bool>() {
            serde_json::Value::Bool(b)
        } else if value.is_none() {
            serde_json::Value::Null
        } else {
            // Try to convert to string as fallback
            serde_json::Value::String(value.to_string())
        };
        context.insert(key_str, json_value);
    }

    Ok(serde_json::Value::Object(context))
}

// Process multipart file upload
async fn process_multipart_upload(
    body: Body,
    boundary: String,
    upload_config: &UploadConfig,
) -> Result<Vec<PyUploadFile>, String> {
    // Convert Body to Stream for multer
    let stream = body.into_data_stream();
    let mut multipart = Multipart::new(stream, boundary);
    let mut uploaded_files = Vec::new();

    while let Some(mut field) = multipart
        .next_field()
        .await
        .map_err(|e| format!("Error reading multipart field: {}", e))?
    {
        let filename = field
            .file_name()
            .map(|s| s.to_string())
            .unwrap_or_else(|| "unknown".to_string());

        let content_type = field
            .content_type()
            .map(|s| s.to_string())
            .unwrap_or_else(|| "application/octet-stream".to_string());

        // Check if MIME type is accepted
        if !upload_config.accepted_mime_types.is_empty() {
            let mime_accepted = upload_config.accepted_mime_types.iter().any(|accepted| {
                // Support wildcard matching (e.g., "image/*")
                if accepted.ends_with("/*") {
                    let prefix = &accepted[..accepted.len() - 2];
                    content_type.starts_with(prefix)
                } else {
                    &content_type == accepted
                }
            });

            if !mime_accepted {
                return Err(format!(
                    "File type '{}' not accepted. Accepted types: {:?}",
                    content_type, upload_config.accepted_mime_types
                ));
            }
        }

        // Create a temporary file in the upload directory
        let upload_dir = PathBuf::from(&upload_config.upload_dir);
        std::fs::create_dir_all(&upload_dir)
            .map_err(|e| format!("Failed to create upload directory: {}", e))?;

        let mut temp_file = NamedTempFile::new_in(&upload_dir)
            .map_err(|e| format!("Failed to create temp file: {}", e))?;

        let mut total_size: u64 = 0;

        // Stream the file data to disk without loading it all into memory
        while let Some(chunk) = field
            .chunk()
            .await
            .map_err(|e| format!("Error reading file chunk: {}", e))?
        {
            let chunk_size = chunk.len() as u64;
            total_size += chunk_size;

            // Check size limit
            if let Some(max_size) = upload_config.max_size {
                if total_size > max_size {
                    // Clean up the temp file (it will be deleted when temp_file is dropped)
                    return Err(format!(
                        "File size ({} bytes) exceeds maximum allowed size ({} bytes)",
                        total_size, max_size
                    ));
                }
            }

            temp_file
                .write_all(&chunk)
                .map_err(|e| format!("Failed to write to temp file: {}", e))?;
        }

        temp_file
            .flush()
            .map_err(|e| format!("Failed to flush temp file: {}", e))?;

        // Persist the temp file (prevent it from being deleted)
        let persisted_path = temp_file
            .into_temp_path()
            .keep()
            .map_err(|e| format!("Failed to persist temp file: {}", e))?;

        let upload_file = PyUploadFile {
            filename,
            content_type,
            size: total_size,
            path: persisted_path.to_string_lossy().to_string(),
        };

        uploaded_files.push(upload_file);
    }

    Ok(uploaded_files)
}

async fn handler_request(
    method: Method,
    uri: Uri,
    request: Request,
    routes: Arc<Mutex<Vec<RouteInfo>>>,
    middlewares: Arc<Mutex<Vec<MiddlewareInfo>>>,
    telemetry_config: Arc<Mutex<TelemetryConfig>>,
    template_config: Arc<Mutex<TemplateConfig>>,
) -> axum::response::Response {
    let start_time = Instant::now();
    let path = uri.path().to_string();
    let method_str = method.as_str().to_string();

    // Extract headers from the request before consuming the body
    let headers_map = request.headers().clone();
    let mut headers = HashMap::new();
    for (key, value) in headers_map.iter() {
        if let Ok(value_str) = value.to_str() {
            headers.insert(key.as_str().to_string(), value_str.to_string());
        }
    }

    // Get User-Agent for logging
    let user_agent = headers
        .get("user-agent")
        .cloned()
        .unwrap_or_else(|| "unknown".to_string());

    // Parse cookies from Cookie header
    let cookies = if let Some(cookie_header) = headers.get("cookie") {
        parse_cookies(cookie_header)
    } else {
        HashMap::new()
    };

    // Create a span for this request
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

    // Try to find a matching route early to check if it's an upload route
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

    // Handle upload routes specially to avoid loading entire body into memory
    if let Some((ref route_info, _)) = matched_route {
        if route_info.is_upload {
            // This is an upload route, handle multipart data
            let content_type = headers.get("content-type").cloned().unwrap_or_default();

            // Extract boundary from content-type header
            // Parse boundary more robustly, handling quotes and spaces
            let boundary = if let Some(boundary_start) = content_type.find("boundary=") {
                let boundary_str = &content_type[boundary_start + 9..];
                // Remove quotes if present and trim whitespace
                let boundary_str = boundary_str.trim();
                if boundary_str.starts_with('"') && boundary_str.contains('"') {
                    // Remove surrounding quotes
                    let end_quote = boundary_str[1..]
                        .find('"')
                        .unwrap_or(boundary_str.len() - 1);
                    boundary_str[1..=end_quote].to_string()
                } else {
                    // Take until semicolon or end of string
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

            // Process the multipart upload
            match process_multipart_upload(request.into_body(), boundary, upload_config).await {
                Ok(uploaded_files) => {
                    let resp = Python::attach(|py| {
                        // Create PyRequest with method, path, and headers
                        let py_request = PyRequest {
                            method: method_str.clone(),
                            path: path.clone(),
                            body: String::new(),
                            headers: headers.clone(),
                            cookies: cookies.clone(),
                        };

                        // Convert uploaded files to Python objects
                        let py_files = pyo3::types::PyList::empty(py);
                        for file in uploaded_files {
                            let py_file = Bound::new(py, file).unwrap();
                            let _ = py_files.append(py_file);
                        }

                        // Call the handler with request and files
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

    // Extract body for non-upload methods that support it (POST, PUT, PATCH, DELETE)
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
            // Create PyRequest with method, path, body, headers, and cookies
            let mut py_request = PyRequest {
                method: method_str.clone(),
                path: path.clone(),
                body: body.clone(),
                headers: headers.clone(),
                cookies: cookies.clone(),
            };

            // Execute each middleware in order
            for middleware_info in middlewares_list.iter() {
                let result = middleware_info.handler.call1(py, (py_request.clone(),));

                match result {
                    Ok(response) => {
                        // Check if middleware returned a Response (early termination)
                        if let Ok(py_response) = response.extract::<PyResponse>(py) {
                            let status_u16 = py_response.status;
                            return Some((build_response(py_response), status_u16));
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
        info!(
            "Request completed: {} - Duration: {:?}",
            status_code, duration
        );
        return response;
    }

    // Now handle the matched route outside the lock
    let (response, status_code) = if let Some((route_info, param_values)) = matched_route {
        let handler_span =
            span!(Level::INFO, "handler_execution", handler.route = %route_info.path);
        let _handler_enter = handler_span.enter();

        let resp = Python::attach(|py| {
            // Create PyRequest with method, path, body, headers, and cookies
            let py_request = PyRequest {
                method: method_str.clone(),
                path: path.clone(),
                body,
                headers: headers.clone(),
                cookies: cookies.clone(),
            };

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
                    // Check if this is a template route
                    if route_info.is_template {
                        // Handler should return a dict for template rendering
                        if let Ok(py_dict) = response.cast_bound::<PyDict>(py) {
                            // Convert PyDict to serde_json::Value
                            let mut context = serde_json::Map::new();
                            for (key, value) in py_dict.iter() {
                                if let Ok(key_str) = key.extract::<String>() {
                                    // Try to extract different types
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
                                        // Fallback to string representation
                                        serde_json::Value::String(value.to_string())
                                    };
                                    context.insert(key_str, json_value);
                                }
                            }

                            // Render the template
                            let template_dirs = template_config.lock().unwrap().template_dirs.clone();
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
                    } else {
                        // Extract the response for non-template routes
                        if let Ok(py_response) = response.extract::<PyResponse>(py) {
                            let status_u16 = py_response.status;
                            (build_response(py_response), status_u16)
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
    m.add_class::<PyUploadFile>()?;
    Ok(())
}
