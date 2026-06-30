use indexmap::IndexMap;
use percent_encoding::percent_decode_str;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;
use std::sync::Arc;

/// Helper function to decode query string values
/// Handles both "+" as space and percent-encoded values
fn decode_query_value(s: &str) -> Option<String> {
    // First replace + with space, then percent decode
    let with_spaces = s.replace('+', " ");
    percent_decode_str(&with_spaces)
        .decode_utf8()
        .ok()
        .map(|s| s.to_string())
}

#[pyclass(from_py_object)]
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
    parsed_query_params: Arc<IndexMap<String, String>>,
}

impl PyRequest {
    pub(crate) fn from_parts(
        method: String,
        path: String,
        body: String,
        headers: HashMap<String, String>,
        cookies: HashMap<String, String>,
    ) -> Self {
        let parsed_query_params = Arc::new(parse_query_string(&path));
        PyRequest {
            method,
            path,
            body,
            headers,
            cookies,
            parsed_query_params,
        }
    }
}

#[pymethods]
impl PyRequest {
    #[new]
    fn new(method: String, path: String, body: String) -> Self {
        let parsed_query_params = Arc::new(parse_query_string(&path));
        PyRequest {
            method,
            path,
            body,
            headers: HashMap::new(),
            cookies: HashMap::new(),
            parsed_query_params,
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

    /// Get query string keys from the path
    ///
    /// Returns a list of query parameter keys, URL-decoded.
    /// Handles both parameters with values (e.g., `?key=value`) and
    /// flag parameters without values (e.g., `?flag`).
    ///
    /// # Returns
    /// * `Vec<String>` - List of decoded query parameter keys
    ///
    /// # Example
    /// For path `/search?q=rust&page=1&debug`, returns `["q", "page", "debug"]`
    fn get_query_keys(&self, _py: Python) -> PyResult<Vec<String>> {
        Ok(self.parsed_query_params.keys().cloned().collect())
    }

    /// Get the path without query string
    ///
    /// Returns the path component of the URL with the query string removed.
    /// If there is no query string, returns the original path.
    ///
    /// # Returns
    /// * `String` - Path without query string
    ///
    /// # Example
    /// For path `/search?q=rust`, returns `/search`
    fn get_path_without_query(&self, _py: Python) -> PyResult<String> {
        if let Some(query_start) = self.path.find('?') {
            Ok(self.path[..query_start].to_string())
        } else {
            Ok(self.path.clone())
        }
    }

    /// Get a query parameter value by key
    ///
    /// Returns the URL-decoded value of a specific query parameter.
    /// If the key doesn't exist, returns `None`.
    /// If the key appears multiple times, returns the last value.
    /// Flag parameters (without values) return an empty string.
    ///
    /// # Arguments
    /// * `key` - The query parameter key to look up
    ///
    /// # Returns
    /// * `Option<String>` - The decoded parameter value, or `None` if not found
    ///
    /// # Example
    /// For path `/search?q=rust+programming&page=2`,
    /// `get_query_param("q")` returns `Some("rust programming")`
    fn get_query_param(&self, _py: Python, key: String) -> PyResult<Option<String>> {
        Ok(self.parsed_query_params.get(&key).cloned())
    }

    /// Get all query parameters as a dictionary
    ///
    /// Returns all query parameters as a Python dictionary with URL-decoded
    /// keys and values. If a key appears multiple times, the last value is kept.
    /// Flag parameters (without values) have an empty string as the value.
    ///
    /// # Returns
    /// * `Py<PyDict>` - Dictionary of decoded query parameters
    ///
    /// # Example
    /// For path `/search?q=rust&page=2&debug`, returns:
    /// `{"q": "rust", "page": "2", "debug": ""}`
    #[getter]
    fn query_params(&self, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        for (key, value) in self.parsed_query_params.iter() {
            dict.set_item(key, value)?;
        }
        Ok(dict.into())
    }
}

pub fn parse_query_string(path: &str) -> IndexMap<String, String> {
    let mut params = IndexMap::new();
    if let Some(query_start) = path.find('?') {
        let query_string = &path[query_start + 1..];
        if query_string.len() > 100_000 {
            return params; // short circuit for excessively long queries
        }
        for (i, param) in query_string.split('&').enumerate() {
            if i >= 1000 {
                break; // short circuit for too many parameters
            }
            if param.is_empty() {
                continue;
            }
            if let Some(eq_pos) = param.find('=') {
                let key = &param[..eq_pos];
                let value = &param[eq_pos + 1..];
                if let (Some(decoded_key), Some(decoded_value)) =
                    (decode_query_value(key), decode_query_value(value))
                {
                    // Intentionally "last wins" as insert overwrites existing keys
                    params.insert(decoded_key, decoded_value);
                }
            } else if let Some(decoded_key) = decode_query_value(param) {
                // Intentionally "last wins" as insert overwrites existing keys
                params.insert(decoded_key, String::new());
            }
        }
    }
    params
}

pub fn parse_cookies(cookie_header: &str) -> HashMap<String, String> {
    // Estimate capacity based on typical cookie size
    let estimated_cookies = cookie_header.matches(';').count() + 1;
    let mut cookies = HashMap::with_capacity(estimated_cookies);

    for cookie in cookie_header.split(';') {
        let cookie = cookie.trim();
        if let Some(eq_pos) = cookie.find('=') {
            let name = cookie[..eq_pos].trim();
            // Only insert if name is not empty to avoid malformed cookies
            if !name.is_empty() {
                let value = cookie[eq_pos + 1..].trim();
                cookies.insert(name.to_string(), value.to_string());
            }
        }
    }
    cookies
}
