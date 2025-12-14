use std::sync::{Arc, Mutex};

use pyo3::prelude::*;
use pyo3::types::PyDict;
use tracing::info;

use crate::routing::{parse_path_params, MiddlewareInfo, RouteInfo};
use crate::server::run_server;
use crate::telemetry::TelemetryConfig;
use crate::template::{py_dict_to_json, render_template_with_dirs, TemplateConfig};
use crate::upload::UploadConfig;

#[pyclass]
pub struct Rupy {
    host: String,
    port: u16,
    pub(crate) routes: Arc<Mutex<Vec<RouteInfo>>>,
    pub(crate) middlewares: Arc<Mutex<Vec<MiddlewareInfo>>>,
    pub(crate) telemetry_config: Arc<Mutex<TelemetryConfig>>,
    pub(crate) template_config: Arc<Mutex<TemplateConfig>>,
}

#[pymethods]
impl Rupy {
    #[new]
    fn new() -> Self {
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

    fn set_template_dir(&self, dir: String) -> PyResult<()> {
        let mut config = self.template_config.lock().unwrap();
        config.template_dir = dir.clone();
        config.template_dirs = vec![dir];
        Ok(())
    }

    fn get_template_dir(&self) -> PyResult<String> {
        let config = self.template_config.lock().unwrap();
        Ok(config.template_dir.clone())
    }

    fn add_template_dir(&self, dir: String) -> PyResult<()> {
        let mut config = self.template_config.lock().unwrap();
        if !config.template_dirs.contains(&dir) {
            config.template_dirs.push(dir);
        }
        Ok(())
    }

    fn remove_template_dir(&self, dir: String) -> PyResult<()> {
        let mut config = self.template_config.lock().unwrap();
        config.template_dirs.retain(|d| d != &dir);
        Ok(())
    }

    fn get_template_dirs(&self) -> PyResult<Vec<String>> {
        let config = self.template_config.lock().unwrap();
        Ok(config.template_dirs.clone())
    }

    fn render_template_string(
        &self,
        template_name: String,
        context: Py<PyDict>,
    ) -> PyResult<String> {
        Python::attach(|py| {
            let config = self.template_config.lock().unwrap();
            let dirs = config.template_dirs.clone();
            drop(config);

            let json_context = py_dict_to_json(py, &context)?;

            render_template_with_dirs(&dirs, &template_name, &json_context)
                .map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>)
        })
    }

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

    fn disable_telemetry(&self) -> PyResult<()> {
        let mut config = self.telemetry_config.lock().unwrap();
        config.enabled = false;
        info!("OpenTelemetry telemetry disabled");
        Ok(())
    }

    fn is_telemetry_enabled(&self) -> PyResult<bool> {
        let config = self.telemetry_config.lock().unwrap();
        Ok(config.enabled)
    }

    fn set_service_name(&self, name: String) -> PyResult<()> {
        let mut config = self.telemetry_config.lock().unwrap();
        config.service_name = name;
        Ok(())
    }

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

        py.detach(|| {
            let runtime = tokio::runtime::Runtime::new().unwrap();
            let _ = runtime.block_on(async {
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
