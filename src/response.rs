use axum::http::StatusCode;
use axum::response::IntoResponse;
use percent_encoding::{utf8_percent_encode, NON_ALPHANUMERIC};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

#[pyclass]
#[derive(Clone)]
pub struct PyResponse {
    #[pyo3(get)]
    pub body: String,
    #[pyo3(get)]
    pub status: u16,
    pub headers: HashMap<String, String>,
    pub cookies: Vec<String>,
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
        let encoded_value = utf8_percent_encode(&value, NON_ALPHANUMERIC).to_string();
        let mut cookie = format!("{}={}", name, encoded_value);

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

pub fn build_response(py_response: PyResponse) -> axum::response::Response {
    use axum::http::header::{HeaderMap, HeaderName, HeaderValue};

    let status_code = StatusCode::from_u16(py_response.status).unwrap_or(StatusCode::OK);
    let body = py_response.body;

    let mut header_map = HeaderMap::new();
    for (key, value) in py_response.headers.iter() {
        if let Ok(header_name) = HeaderName::from_bytes(key.as_bytes()) {
            if let Ok(header_value) = HeaderValue::from_str(value) {
                header_map.insert(header_name, header_value);
            }
        }
    }

    for cookie in py_response.cookies.iter() {
        if let Ok(cookie_value) = HeaderValue::from_str(cookie) {
            header_map.append("set-cookie", cookie_value);
        }
    }

    (status_code, header_map, body).into_response()
}
