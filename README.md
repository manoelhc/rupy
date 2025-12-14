# Rupy

A high-performance web framework for Python, powered by Rust and Axum.

## Features

- ✅ High-performance Rust backend with Axum web framework
- ✅ Simple and intuitive Python API
- ✅ Support for all standard HTTP methods (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
- ✅ Convenient method-specific decorators (`@app.get()`, `@app.post()`, etc.)
- ✅ Dynamic route parameters (e.g., `/user/<username>`)
- ✅ Request body parsing for POST, PUT, PATCH, and DELETE
- ✅ Async/await support
- ✅ JSON-formatted request logging
- ✅ OpenTelemetry support for metrics, tracing, and logging
- ✅ Middleware support for request/response processing
- ✅ Cookie support (get/set cookies in requests and responses)
- ✅ Authentication token support (Bearer token helper)
- ✅ Static file serving via decorators
- ✅ Reverse proxy support via decorators
- ✅ OpenAPI/Swagger JSON endpoint
- ✅ File upload support with streaming (memory-efficient)
- ✅ Template rendering with Handlebars
- ✅ Template class for programmatic rendering
- ✅ Multiple template directories with flexible lookup


## Installation

### Installing from PyPI

Once released, you can install Rupy from PyPI:

```bash
pip install rupy-api
```

Or add it to your `pyproject.toml`:

```toml
[project]
dependencies = [
    "rupy-api>=0.0.1"
]
```

### Adding as a Dependency from GitHub

To add Rupy as a dependency to your project using the GitHub repository, add the following to your `pyproject.toml`:

```toml
[project]
dependencies = [
    "rupy-api @ git+https://github.com/manoelhc/rupy.git"
]
```

Or for a specific branch, tag, or commit:

```toml
[project]
dependencies = [
    # Using a specific branch
    "rupy-api @ git+https://github.com/manoelhc/rupy.git@main",
    
    # Using a specific tag
    "rupy-api @ git+https://github.com/manoelhc/rupy.git@v0.0.1",
    
    # Using a specific commit
    "rupy-api @ git+https://github.com/manoelhc/rupy.git@abc123",
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

#### Method-Specific Decorators

For convenience, Rupy provides method-specific decorators that make your code more readable:

```python
from rupy import Rupy, Request, Response

app = Rupy()

# Instead of @app.route("/items", methods=["GET"])
@app.get("/items")
def list_items(request: Request) -> Response:
    return Response("List of items")

# Instead of @app.route("/items", methods=["POST"])
@app.post("/items")
def create_item(request: Request) -> Response:
    return Response(f"Created: {request.body}")

# Available decorators for all HTTP methods:
@app.put("/items/<item_id>")
def update_item(request: Request, item_id: str) -> Response:
    return Response(f"Updated item {item_id}: {request.body}")

@app.patch("/items/<item_id>")
def patch_item(request: Request, item_id: str) -> Response:
    return Response(f"Patched item {item_id}: {request.body}")

@app.delete("/items/<item_id>")
def delete_item(request: Request, item_id: str) -> Response:
    return Response(f"Deleted item {item_id}")

@app.head("/items")
def head_items(request: Request) -> Response:
    return Response("Headers only")

@app.options("/items")
def options_items(request: Request) -> Response:
    return Response("OPTIONS response")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
```

Available method-specific decorators:
- `@app.get(path)` - for GET requests
- `@app.post(path)` - for POST requests
- `@app.put(path)` - for PUT requests
- `@app.patch(path)` - for PATCH requests
- `@app.delete(path)` - for DELETE requests
- `@app.head(path)` - for HEAD requests
- `@app.options(path)` - for OPTIONS requests

You can still use `@app.route(path, methods=[...])` when you need to handle multiple methods with the same handler.

### Dynamic Route Parameters

You can define dynamic segments in your routes using angle brackets:

```python
@app.route("/user/<username>/post/<post_id>", methods=["GET"])
def get_user_post(request: Request, username: str, post_id: str) -> Response:
    return Response(f"Post {post_id} by {username}")
```

### Middleware

Rupy supports middleware functions that execute before route handlers. Middlewares can:
- Inspect and modify requests
- Return early responses (e.g., for authentication)
- Execute in registration order
- Block or allow requests to proceed

#### Basic Middleware

```python
from rupy import Rupy, Request, Response

app = Rupy()

@app.middleware
def logging_middleware(request: Request):
    print(f"Processing {request.method} {request.path}")
    # Return request to continue to next middleware/handler
    return request

@app.middleware
def auth_middleware(request: Request):
    # Check authentication and block if needed
    if request.path.startswith("/admin") and not is_authenticated(request):
        return Response("Unauthorized", status=401)
    return request

@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Hello, World!")
```

#### CORS Middleware Example

```python
@app.middleware
def cors_middleware(request: Request):
    print(f"[CORS] Processing {request.method} {request.path}")
    
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        return Response("", status=204)
    
    # Continue to next middleware or route handler
    return request
```

#### JWT Authentication Middleware Example

```python
@app.middleware
def jwt_auth_middleware(request: Request):
    # Skip auth for public routes
    if request.path in ["/", "/login", "/public"]:
        return request
    
    # Check for protected routes
    if request.path.startswith("/protected"):
        # In real implementation, validate JWT token from headers
        return Response(
            '{"error": "Unauthorized - Invalid or missing JWT token"}',
            status=401
        )
    
    return request
```

For complete production-ready examples, see:
- `examples/jwt_middleware.py` - JWT authentication with PyJWT library
- `examples/cors_middleware.py` - CORS with configurable origins and credentials
- `examples/geo_blocking_middleware.py` - IP-based geographical access control
- `examples/rate_limiting_middleware.py` - Rate limiting by IP and User-Agent
- `examples/combined_middlewares.py` - Multiple middlewares working together
- `examples/MIDDLEWARE_README.md` - Comprehensive middleware documentation

All middleware examples feature:
- Production-ready implementations with real libraries
- Security best practices and error handling
- Detailed documentation and usage examples
- Testing commands and load testing guidance

### Cookies and Authentication

Rupy provides built-in support for working with cookies and Bearer authentication tokens.

#### Working with Cookies

```python
from rupy import Rupy, Request, Response

app = Rupy()

@app.route("/login", methods=["POST"])
def login(request: Request) -> Response:
    resp = Response('{"message": "Login successful"}')
    
    # Set a cookie with options
    resp.set_cookie(
        "session_id",
        "abc123",
        max_age=3600,        # Expires in 1 hour
        http_only=True,      # Not accessible via JavaScript
        secure=True,         # Only sent over HTTPS
        same_site="Lax"      # CSRF protection
    )
    
    return resp

@app.route("/profile", methods=["GET"])
def profile(request: Request) -> Response:
    # Read a cookie
    session_id = request.get_cookie("session_id")
    
    if not session_id:
        return Response("Not logged in", status=401)
    
    return Response(f"Session: {session_id}")

@app.route("/logout", methods=["POST"])
def logout(request: Request) -> Response:
    resp = Response('{"message": "Logged out"}')
    
    # Delete a cookie
    resp.delete_cookie("session_id")
    
    return resp
```

#### Authentication Tokens

```python
@app.route("/protected", methods=["GET"])
def protected(request: Request) -> Response:
    # Get Bearer token from Authorization header
    token = request.auth_token
    
    if not token:
        return Response("Unauthorized", status=401)
    
    # Validate token (implement your own validation logic)
    if token == "valid-token":
        return Response("Access granted")
    else:
        return Response("Invalid token", status=401)

@app.middleware
def auth_middleware(request: Request):
    """Add authentication token in middleware"""
    if request.path.startswith("/internal"):
        request.set_auth_token("internal-service-token")
    return request
```

For complete examples, see:
- `examples/cookies_auth_example.py` - Cookie and auth token handling

### File Upload

Handle file uploads efficiently with the `@app.upload()` decorator. Files are streamed directly to disk without being loaded into memory, making it suitable for large files.

```python
from rupy import Rupy, Request, Response, UploadFile
from typing import List

app = Rupy()

# Basic file upload
@app.upload("/upload")
def handle_upload(request: Request, files: List[UploadFile]) -> Response:
    for file in files:
        print(f"Uploaded: {file.filename}")
        print(f"Size: {file.size} bytes")
        print(f"MIME type: {file.content_type}")
        print(f"Saved at: {file.path}")
    return Response("Files uploaded successfully")

# Upload with MIME type filtering
@app.upload("/upload-images", accepted_mime_types=["image/*"])
def upload_images(request: Request, files: List[UploadFile]) -> Response:
    return Response(f"Uploaded {len(files)} images")

# Upload with size limit (5MB)
@app.upload("/upload-limited", max_size=5*1024*1024)
def upload_limited(request: Request, files: List[UploadFile]) -> Response:
    return Response("Upload successful")

# Upload with all options
@app.upload(
    "/upload-docs",
    accepted_mime_types=["application/pdf", "application/msword"],
    max_size=10*1024*1024,  # 10MB
    upload_dir="/var/uploads"
)
def upload_docs(request: Request, files: List[UploadFile]) -> Response:
    return Response("Documents uploaded")
```

Upload features:
- **Streaming uploads**: Files are written directly to disk to prevent memory overflow
- **MIME type filtering**: Accept only specific file types (supports wildcards like `image/*`)
- **Size limits**: Set maximum file size per upload
- **Custom upload directory**: Specify where files should be stored (default: `/tmp`)
- **Multiple files**: Handle multiple file uploads in a single request
- **UploadFile attributes**:
  - `filename`: Original filename
  - `size`: File size in bytes
  - `content_type`: MIME type
  - `path`: Temporary file path on disk

For a complete example, see:
- `examples/upload_example.py` - File upload with web interface

### Static File Serving

Serve static files from a directory using the `@app.static()` decorator.

```python
from rupy import Rupy, Request, Response

app = Rupy()

# Serve files from ./public directory at /static path
@app.static("/static", "./public")
def static_files():
    pass

# Now files in ./public are accessible at /static/<filename>
# Example: ./public/style.css -> http://localhost:8000/static/style.css
```

The static file server includes:
- Automatic content-type detection
- Directory traversal protection
- Support for all common file types

For a complete example, see:
- `examples/static_files_example.py` - Static file serving

### Reverse Proxy

Proxy requests to another backend service using the `@app.proxy()` decorator.

```python
from rupy import Rupy, Request, Response

app = Rupy()

# Proxy all /api/* requests to backend service
@app.proxy("/api", "http://backend:8080")
def api_proxy():
    pass

# Now requests to /api/* are forwarded to http://backend:8080/*
# Example: /api/users -> http://backend:8080/users
```

The reverse proxy:
- Forwards all HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Preserves request headers and body
- Returns response headers and body from the backend

For a complete example, see:
- `examples/reverse_proxy_example.py` - Reverse proxy with backend

### OpenAPI/Swagger Support

Enable OpenAPI documentation for your API.

```python
from rupy import Rupy, Request, Response

app = Rupy()

# Enable OpenAPI endpoint
app.enable_openapi(
    path="/openapi.json",
    title="My API",
    version="1.0.0",
    description="API documentation"
)

@app.route("/users", methods=["GET"])
def list_users(request: Request) -> Response:
    """List all users - this docstring can be used for API docs"""
    return Response('[{"id": 1, "name": "Alice"}]')

# Access the OpenAPI spec at http://localhost:8000/openapi.json
```

To disable the OpenAPI endpoint:
```python
app.disable_openapi()
```

For a complete example, see:
- `examples/openapi_example.py` - OpenAPI documentation

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
