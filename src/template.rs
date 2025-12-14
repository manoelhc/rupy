use handlebars::Handlebars;
use pyo3::prelude::*;
use pyo3::types::PyDict;
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
        let json_value = if let Ok(s) = value.extract::<String>() {
            serde_json::Value::String(s)
        } else if let Ok(i) = value.extract::<i64>() {
            serde_json::Value::Number(i.into())
        } else if let Ok(f) = value.extract::<f64>() {
            match serde_json::Number::from_f64(f) {
                Some(n) => serde_json::Value::Number(n),
                None => serde_json::Value::Null, // NaN/infinity -> null
            }
        } else if let Ok(b) = value.extract::<bool>() {
            serde_json::Value::Bool(b)
        } else if value.is_none() {
            serde_json::Value::Null
        } else {
            serde_json::Value::String(value.to_string())
        };
        context.insert(key_str, json_value);
    }

    Ok(serde_json::Value::Object(context))
}
