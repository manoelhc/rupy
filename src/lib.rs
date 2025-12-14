mod app;
mod request;
mod response;
mod routing;
mod server;
mod telemetry;
mod template;
mod upload;

pub use app::Rupy;
pub use request::PyRequest;
pub use response::PyResponse;
pub use upload::PyUploadFile;

use pyo3::prelude::*;
use pyo3::Bound;

#[pymodule]
fn rupy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Rupy>()?;
    m.add_class::<PyRequest>()?;
    m.add_class::<PyResponse>()?;
    m.add_class::<PyUploadFile>()?;
    Ok(())
}
