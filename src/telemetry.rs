use opentelemetry::{global, KeyValue};
use opentelemetry_sdk::{metrics::SdkMeterProvider, trace::SdkTracerProvider, Resource};
use opentelemetry_semantic_conventions as semcov;
use std::sync::{Arc, Mutex};
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[derive(Clone)]
pub struct TelemetryConfig {
    pub enabled: bool,
    pub endpoint: Option<String>,
    pub service_name: String,
}

pub struct TelemetryGuard {
    tracer_provider: Option<SdkTracerProvider>,
}

impl Drop for TelemetryGuard {
    fn drop(&mut self) {
        if let Some(provider) = self.tracer_provider.take() {
            info!("Shutting down telemetry");
            let _ = provider.shutdown();
        }
    }
}

pub fn init_telemetry(config: &TelemetryConfig) -> TelemetryGuard {
    let service_name = config.service_name.clone();

    let resource = Resource::builder()
        .with_attribute(KeyValue::new(
            semcov::resource::SERVICE_NAME,
            service_name.clone(),
        ))
        .build();

    let tracer_provider = opentelemetry_sdk::trace::SdkTracerProvider::builder()
        .with_resource(resource.clone())
        .build();

    global::set_tracer_provider(tracer_provider.clone());

    let meter_provider = SdkMeterProvider::builder().with_resource(resource).build();
    global::set_meter_provider(meter_provider);

    let env_filter = std::env::var("RUST_LOG").unwrap_or_else(|_| "info".to_string());

    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(env_filter))
        .with(tracing_subscriber::fmt::layer().with_target(false).json())
        .init();

    info!("OpenTelemetry initialized with service: {}", service_name);

    TelemetryGuard {
        tracer_provider: Some(tracer_provider),
    }
}

pub fn record_metrics(
    telemetry_config: &Arc<Mutex<TelemetryConfig>>,
    method_str: &str,
    path: &str,
    status_code: u16,
    duration: std::time::Duration,
) {
    let config = telemetry_config.lock().unwrap();
    if config.enabled {
        // Use a fixed meter name or cache the meter elsewhere
        let meter = global::meter("rupy");
        let counter = meter
            .u64_counter("http.server.requests")
            .with_description("Total number of HTTP requests")
            .build();
        let histogram = meter
            .f64_histogram("http.server.duration")
            .with_description("HTTP request duration in seconds")
            .with_unit("s")
            .build();

        counter.add(
            1,
            &[
                KeyValue::new("http.method", method_str.to_string()),
                KeyValue::new("http.route", path.to_string()),
                KeyValue::new("http.status_code", status_code as i64),
            ],
        );

        histogram.record(
            duration.as_secs_f64(),
            &[
                KeyValue::new("http.method", method_str.to_string()),
                KeyValue::new("http.route", path.to_string()),
                KeyValue::new("http.status_code", status_code as i64),
            ],
        );
    }
}
