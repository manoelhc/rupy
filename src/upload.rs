use axum::body::Body;
use multer::Multipart;
use pyo3::prelude::*;
use std::io::Write;
use std::path::PathBuf;
use tempfile::NamedTempFile;

#[pyclass]
#[derive(Clone)]
pub struct PyUploadFile {
    #[pyo3(get)]
    pub filename: String,
    #[pyo3(get)]
    content_type: String,
    #[pyo3(get)]
    pub size: u64,
    #[pyo3(get)]
    pub path: String,
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

    fn get_filename(&self) -> PyResult<String> {
        Ok(self.filename.clone())
    }

    fn get_content_type(&self) -> PyResult<String> {
        Ok(self.content_type.clone())
    }

    fn get_size(&self) -> PyResult<u64> {
        Ok(self.size)
    }

    fn get_path(&self) -> PyResult<String> {
        Ok(self.path.clone())
    }
}

#[derive(Clone)]
pub struct UploadConfig {
    pub accepted_mime_types: Vec<String>,
    pub max_size: Option<u64>,
    pub upload_dir: String,
}

pub async fn process_multipart_upload(
    body: Body,
    boundary: String,
    upload_config: &UploadConfig,
) -> Result<Vec<PyUploadFile>, String> {
    let stream = body.into_data_stream();
    let mut multipart = Multipart::new(stream, boundary);
    let mut uploaded_files: std::vec::Vec<PyUploadFile> = Vec::new();

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

        if !upload_config.accepted_mime_types.is_empty() {
            let mime_accepted = upload_config.accepted_mime_types.iter().any(|accepted| {
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

        let upload_dir = PathBuf::from(&upload_config.upload_dir);
        std::fs::create_dir_all(&upload_dir)
            .map_err(|e| format!("Failed to create upload directory: {}", e))?;

        let mut temp_file = NamedTempFile::new_in(&upload_dir)
            .map_err(|e| format!("Failed to create temp file: {}", e))?;

        let mut total_size: u64 = 0;

        while let Some(chunk) = field
            .chunk()
            .await
            .map_err(|e| format!("Error reading file chunk: {}", e))?
        {
            let chunk_size = chunk.len() as u64;
            total_size += chunk_size;

            if let Some(max_size) = upload_config.max_size {
                if total_size > max_size {
                    // Clean up any files already persisted in this request
                    for uploaded in &uploaded_files {
                        let _ = std::fs::remove_file(&uploaded.path);
                    }
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
