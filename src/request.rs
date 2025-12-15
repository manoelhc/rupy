use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

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

impl PyRequest {
    pub(crate) fn from_parts(
        method: String,
        path: String,
        body: String,
        headers: HashMap<String, String>,
        cookies: HashMap<String, String>,
    ) -> Self {
        PyRequest {
            method,
            path,
            body,
            headers,
            cookies,
        }
    }
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
        let auth_header = self
            .headers
            .iter()
            .find(|(k, _)| k.eq_ignore_ascii_case("authorization"))
            .map(|(_, v)| v);
        if let Some(auth_header) = auth_header {
            if let Some(token) = auth_header.strip_prefix("Bearer ") {
                return Ok(Some(token.to_string()));
            }
        }
        Ok(None)
    }

    /// Set the auth token in the Authorization header (Bearer token) - property setter
    #[setter(auth_token)]
    fn set_auth_token_property(&mut self, _py: Python, token: String) -> PyResult<()> {
        self.headers
            .insert("authorization".to_string(), format!("Bearer {}", token));
        Ok(())
    }

    /// Set the auth token in the Authorization header (Bearer token) - method
    fn set_auth_token(&mut self, _py: Python, token: String) -> PyResult<()> {
        self.headers
            .insert("authorization".to_string(), format!("Bearer {}", token));
        Ok(())
    }
}

pub fn parse_cookies(cookie_header: &str) -> HashMap<String, String> {
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
