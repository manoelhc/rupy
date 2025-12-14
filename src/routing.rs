use pyo3::prelude::*;

pub struct RouteInfo {
    pub path: String,
    pub handler: Py<PyAny>,
    pub path_params: Vec<String>,
    pub methods: Vec<String>,
    pub is_template: bool,
    pub template_name: Option<String>,
    pub content_type: String,
    pub is_upload: bool,
    pub upload_config: Option<crate::upload::UploadConfig>,
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

pub struct MiddlewareInfo {
    pub handler: Py<PyAny>,
}

impl Clone for MiddlewareInfo {
    fn clone(&self) -> Self {
        Python::attach(|py| MiddlewareInfo {
            handler: self.handler.clone_ref(py),
        })
    }
}

pub fn parse_path_params(path: &str) -> Vec<String> {
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

pub fn match_route(request_path: &str, route_pattern: &str) -> Option<Vec<String>> {
    let route_parts: Vec<&str> = route_pattern.split('/').collect();
    let request_parts: Vec<&str> = request_path.split('/').collect();

    let mut params = Vec::new();
    let mut route_idx = 0;
    let mut request_idx = 0;

    while route_idx < route_parts.len() {
        let route_part = route_parts[route_idx];

        if route_part.starts_with('<') && route_part.ends_with('>') {
            let param_content = &route_part[1..route_part.len() - 1];

            if param_content.contains(":path") {
                if request_idx < request_parts.len() {
                    let remaining = &request_parts[request_idx..];
                    params.push(remaining.join("/"));
                    request_idx = request_parts.len();
                    route_idx += 1;
                } else {
                    params.push(String::new());
                    route_idx += 1;
                }
            } else if request_idx < request_parts.len() {
                params.push(request_parts[request_idx].to_string());
                request_idx += 1;
                route_idx += 1;
            } else {
                return None;
            }
        } else {
            if request_idx >= request_parts.len() || route_part != request_parts[request_idx] {
                return None;
            }
            request_idx += 1;
            route_idx += 1;
        }
    }

    if request_idx == request_parts.len() {
        Some(params)
    } else {
        None
    }
}
