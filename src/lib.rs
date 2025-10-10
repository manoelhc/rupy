use pyo3::prelude::*;
use std::net::SocketAddr;
use axum::{
    Router,
    http::{StatusCode, Method, Uri},
    extract::Request,
    response::IntoResponse,
};
use serde_json::json;
use std::time::SystemTime;

#[pyclass]
struct Rupy {
    host: String,
    port: u16,
}

#[pymethods]
impl Rupy {
    #[new]
    fn new() -> Self {
        Rupy {
            host: "127.0.0.1".to_string(),
            port: 8000,
        }
    }

    #[pyo3(signature = (host=None, port=None))]
    fn run(&self, host: Option<String>, port: Option<u16>) -> PyResult<()> {
        let host = host.unwrap_or_else(|| self.host.clone());
        let port = port.unwrap_or(self.port);
        
        // Run the async server in a blocking context
        let runtime = tokio::runtime::Runtime::new().unwrap();
        runtime.block_on(async {
            run_server(&host, port).await
        });
        
        Ok(())
    }
}

async fn run_server(host: &str, port: u16) {
    // Create a router that matches all routes
    let app = Router::new()
        .fallback(handler_404);

    let addr = format!("{}:{}", host, port).parse::<SocketAddr>().unwrap();
    
    println!("Starting Rupy server on http://{}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn handler_404(
    method: Method,
    uri: Uri,
    _request: Request,
) -> impl IntoResponse {
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
    
    (StatusCode::NOT_FOUND, "404 Not Found")
}

#[pymodule]
fn rupy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Rupy>()?;
    Ok(())
}
