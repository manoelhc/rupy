use handlebars::Handlebars;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use std::path::PathBuf;

#[derive(Clone)]
pub struct TemplateConfig {
    pub template_dir: String,
    pub template_dirs: Vec<String>,
}

pub fn render_template_with_dirs(
    template_dirs: &[String],
    template_name: &str,
    context: &serde_json::Value,
) -> Result<String, String> {
    let mut handlebars = Handlebars::new();

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

    handlebars
        .register_template_string("template", template_content)
        .map_err(|e| format!("Failed to parse template: {}", e))?;

    handlebars
        .render("template", context)
        .map_err(|e| format!("Failed to render template: {}", e))
}

pub fn py_dict_to_json(py: Python, py_dict: &Py<PyDict>) -> PyResult<serde_json::Value> {
    let dict = py_dict.bind(py);
    let mut context = serde_json::Map::new();

    for (key, value) in dict.iter() {
        let key_str = key.extract::<String>()?;
        let json_value = py_obj_to_json(py, value)?;
        context.insert(key_str, json_value);
    }

    Ok(serde_json::Value::Object(context))
}

fn py_obj_to_json(_py: Python, obj: pyo3::Bound<'_, PyAny>) -> PyResult<serde_json::Value> {
    // Dict
    if let Ok(dict) = obj.cast::<PyDict>() {
        let mut map = serde_json::Map::new();
        for (k, v) in dict.iter() {
            let key = k.extract::<String>()?;
            let val = py_obj_to_json(_py, v)?;
            map.insert(key, val);
        }
        return Ok(serde_json::Value::Object(map));
    }

    // List
    if let Ok(list) = obj.cast::<PyList>() {
        let mut vec = Vec::with_capacity(list.len());
        for item in list.iter() {
            vec.push(py_obj_to_json(_py, item)?);
        }
        return Ok(serde_json::Value::Array(vec));
    }

    // Tuple
    if let Ok(tuple) = obj.cast::<PyTuple>() {
        let mut vec = Vec::with_capacity(tuple.len());
        for item in tuple.iter() {
            vec.push(py_obj_to_json(_py, item)?);
        }
        return Ok(serde_json::Value::Array(vec));
    }

    // Scalars
    if let Ok(s) = obj.extract::<String>() {
        return Ok(serde_json::Value::String(s));
    }
    if let Ok(i) = obj.extract::<i64>() {
        return Ok(serde_json::Value::Number(i.into()));
    }
    if let Ok(f) = obj.extract::<f64>() {
        if let Some(n) = serde_json::Number::from_f64(f) {
            return Ok(serde_json::Value::Number(n));
        } else {
            return Ok(serde_json::Value::Null);
        }
    }
    if let Ok(b) = obj.extract::<bool>() {
        return Ok(serde_json::Value::Bool(b));
    }
    if obj.is_none() {
        return Ok(serde_json::Value::Null);
    }
    // Try common object conversions: datetimes via `isoformat()`
    if let Ok(iso_obj) = obj.call_method0("isoformat") {
        if let Ok(iso_str) = iso_obj.extract::<String>() {
            return Ok(serde_json::Value::String(iso_str));
        }
    }

    // Try Decimal-like objects: take string repr and parse as f64 if possible
    if let Ok(s) = obj.str() {
        let s = s.to_string();
        if let Ok(f) = s.parse::<f64>() {
            if let Some(n) = serde_json::Number::from_f64(f) {
                return Ok(serde_json::Value::Number(n));
            }
        }
        return Ok(serde_json::Value::String(s));
    }

    // Fallback (should be unreachable): null
    Ok(serde_json::Value::Null)
}
