# Rupy

A high-performance web framework for Python, powered by Rust and Axum.

## Features

- ✅ High-performance Rust backend with Axum web framework
- ✅ Simple and intuitive Python API
- ✅ Support for all standard HTTP methods (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
- ✅ Dynamic route parameters (e.g., `/user/<username>`)
- ✅ Request body parsing for POST, PUT, PATCH, and DELETE
- ✅ Async/await support
- ✅ JSON-formatted request logging
- ✅ OpenTelemetry support for metrics, tracing, and logging

## Installation

### Adding as a Dependency

To add Rupy as a dependency to your project using the GitHub repository, add the following to your `pyproject.toml`:

```toml
[project]
dependencies = [
    "rupy @ git+https://github.com/manoelhc/rupy.git"
]
```

Or for a specific branch, tag, or commit:

```toml
[project]
dependencies = [
    # Using a specific branch
    "rupy @ git+https://github.com/manoelhc/rupy.git@main",
    
    # Using a specific tag
    "rupy @ git+https://github.com/manoelhc/rupy.git@v0.1.0",
    
    # Using a specific commit
    "rupy @ git+https://github.com/manoelhc/rupy.git@abc123",
]
```

Then install the dependencies:

```bash
pip install .
```

## Building from Source

### Prerequisites

- Python 3.8+
- Rust 1.56+
- maturin

### Build Steps

1. Install maturin:
```bash
pip install maturin
```

2. Build the project:
```bash
maturin build --release
```

3. Install the wheel:
```bash
pip install target/wheels/rupy-*.whl
```

Or build and install in development mode:
```bash
maturin develop
```

## Usage

### Basic Example

```python
from rupy import Rupy, Request, Response

app = Rupy()

@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Hello, World!")

@app.route("/user/<username>", methods=["GET"])
def get_user(request: Request, username: str) -> Response:
    return Response(f"User: {username}")

@app.route("/echo", methods=["POST"])
def echo(request: Request) -> Response:
    return Response(f"Echo: {request.body}")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
```

### Supported HTTP Methods

Rupy supports all standard HTTP methods:

- **GET**: Retrieve resources
- **POST**: Create new resources or submit data
- **PUT**: Update/replace resources
- **PATCH**: Partially update resources
- **DELETE**: Remove resources
- **HEAD**: Retrieve headers only
- **OPTIONS**: Get supported methods for a resource

Example with different HTTP methods:

```python
from rupy import Rupy, Request, Response

app = Rupy()

# GET request
@app.route("/items", methods=["GET"])
def list_items(request: Request) -> Response:
    return Response("List of items")

# POST request - create new item
@app.route("/items", methods=["POST"])
def create_item(request: Request) -> Response:
    return Response(f"Created: {request.body}")

# PUT request - update entire item
@app.route("/items/<item_id>", methods=["PUT"])
def update_item(request: Request, item_id: str) -> Response:
    return Response(f"Updated item {item_id}: {request.body}")

# PATCH request - partial update
@app.route("/items/<item_id>", methods=["PATCH"])
def patch_item(request: Request, item_id: str) -> Response:
    return Response(f"Patched item {item_id}: {request.body}")

# DELETE request
@app.route("/items/<item_id>", methods=["DELETE"])
def delete_item(request: Request, item_id: str) -> Response:
    return Response(f"Deleted item {item_id}")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
```

### Dynamic Route Parameters

You can define dynamic segments in your routes using angle brackets:

```python
@app.route("/user/<username>/post/<post_id>", methods=["GET"])
def get_user_post(request: Request, username: str, post_id: str) -> Response:
    return Response(f"Post {post_id} by {username}")
```

### Testing Your Application

Run the example:
```bash
python example.py
```

Test with curl:
```bash
# GET request
curl http://127.0.0.1:8000/

# GET with parameter
curl http://127.0.0.1:8000/user/alice

# POST request
curl -X POST -d '{"name": "test"}' http://127.0.0.1:8000/echo

# PUT request
curl -X PUT -d '{"name": "updated"}' http://127.0.0.1:8000/items/1

# PATCH request
curl -X PATCH -d '{"status": "active"}' http://127.0.0.1:8000/items/1

# DELETE request
curl -X DELETE http://127.0.0.1:8000/items/1
```

## OpenTelemetry Support

Rupy includes built-in support for OpenTelemetry, providing comprehensive observability through metrics, tracing, and logging.

### Enabling OpenTelemetry

You can enable OpenTelemetry in two ways:

#### 1. Programmatically

```python
from rupy import Rupy, Request, Response

app = Rupy()

# Enable telemetry with optional endpoint and service name
app.enable_telemetry(
    endpoint="http://localhost:4317",  # Optional: OTLP gRPC endpoint
    service_name="my-service"           # Optional: Service name for traces
)

@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Hello, World!")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
```

#### 2. Using Environment Variables

Set these environment variables before running your application:

```bash
# Enable OpenTelemetry
export OTEL_ENABLED=true

# Set the service name (default: "rupy")
export OTEL_SERVICE_NAME=my-service

# Set the OTLP endpoint (optional)
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Set the log level (optional)
export RUST_LOG=info

# Run your application
python app.py
```

### OpenTelemetry Methods

Rupy provides several methods to control OpenTelemetry:

```python
app = Rupy()

# Enable telemetry
app.enable_telemetry(endpoint="http://localhost:4317", service_name="my-service")

# Disable telemetry
app.disable_telemetry()

# Check if telemetry is enabled
is_enabled = app.is_telemetry_enabled()

# Set service name
app.set_service_name("my-new-service")

# Set OTLP endpoint
app.set_telemetry_endpoint("http://localhost:4317")
```

### Collected Metrics

Rupy automatically collects the following metrics:

- **`http.server.requests`**: Counter for total number of HTTP requests
  - Labels: `http.method`, `http.route`, `http.status_code`

- **`http.server.duration`**: Histogram for HTTP request duration in seconds
  - Labels: `http.method`, `http.route`, `http.status_code`

### Tracing

Each HTTP request creates a span with the following attributes:
- `http.method`: The HTTP method (GET, POST, etc.)
- `http.route`: The matched route pattern
- `http.scheme`: The protocol scheme (http/https)

Spans are nested for handler execution, allowing you to trace the complete request lifecycle.

### Logging

All logs are emitted in JSON format and include:
- Timestamp
- Log level
- Message
- Request details (method, path, status)
- Handler execution information

### Integration with Observability Platforms

Rupy's OpenTelemetry implementation works with any OTLP-compatible backend:

- **Jaeger**: For distributed tracing
- **Prometheus**: For metrics collection
- **Grafana**: For visualization
- **OpenTelemetry Collector**: For data processing and export
- **Datadog, New Relic, Honeycomb**: Commercial observability platforms

Example with OpenTelemetry Collector:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  jaeger:
    endpoint: "jaeger:14250"

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      exporters: [prometheus]
```

Run the collector:
```bash
docker run -d \
  -v $(pwd)/otel-collector-config.yaml:/etc/otel-collector-config.yaml \
  -p 4317:4317 \
  -p 8889:8889 \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-collector-config.yaml
```

Then configure Rupy to send data to it:
```python
app.enable_telemetry(endpoint="http://localhost:4317", service_name="my-service")
```

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_ENABLED` | Enable/disable OpenTelemetry | `false` |
| `OTEL_SERVICE_NAME` | Service name for telemetry | `rupy` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP gRPC endpoint | None |
| `RUST_LOG` | Log level (trace, debug, info, warn, error) | `info` |

## Architecture

- **Rust Backend**: Uses Axum web framework for high-performance HTTP handling
- **Python Bindings**: PyO3 provides seamless Python-Rust interoperability
- **Async Runtime**: Tokio powers the asynchronous server
- **Observability**: OpenTelemetry integration for metrics, tracing, and logging

## License

MIT License - see LICENSE file for details
