# Rupy

A high-performance Python web framework for building web applications.

> **Note**: Rupy is currently implemented in pure Python using aiohttp. A Rust-backed implementation using Axum + PyO3 is planned for future releases to provide even better performance.

## Features

- ✨ Simple and intuitive API
- ⚡ Async/await support
- 🛣️ Path parameters in routes (e.g., `/user/<username>`)
- 📦 JSON request/response handling
- 🔧 Multiple HTTP methods support (GET, POST, PUT, DELETE, etc.)
- 🎯 Type hints for better IDE support

## Installation

### From Source

```bash
git clone https://github.com/manoelhc/rupy.git
cd rupy
pip install -e .
```

## Quick Start

Create a file named `app.py`:

```python
from rupy import Rupy, Request, Response

app = Rupy(__name__)

@app.route("/", methods=["GET"])
async def hello_world(request: Request) -> Response:
    return Response("Hello, World!")

@app.route("/user/<username>", methods=["GET"])
async def hello_user(request: Request, username: str) -> Response:
    return Response(f"Hello, {username}!")

@app.route("/echo", methods=["POST"])
async def echo(request: Request) -> Response:
    data = await request.json()
    return Response(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

Run the application:

```bash
python app.py
```

Test the endpoints:

```bash
# Test GET endpoint
curl http://localhost:8000/

# Test path parameters
curl http://localhost:8000/user/Alice

# Test POST with JSON
curl -X POST http://localhost:8000/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, Rupy!"}'
```

## Examples

Check out the [examples/](examples/) directory for more examples:

- `simple_app.py`: Basic application with multiple routes

## API Reference

### Rupy

Main application class.

**Constructor:**
```python
app = Rupy(module_name)
```

**Methods:**
- `route(path, methods)`: Decorator for registering routes
  - `path` (str): URL path pattern (supports `<param>` syntax)
  - `methods` (List[str]): List of HTTP methods (e.g., `["GET", "POST"]`)
- `run(host, port)`: Start the web server
  - `host` (str): Host address (default: "0.0.0.0")
  - `port` (int): Port number (default: 8000)

**Example:**
```python
from rupy import Rupy, Request, Response

app = Rupy(__name__)

@app.route("/api/users/<user_id>", methods=["GET"])
async def get_user(request: Request, user_id: str) -> Response:
    return Response({"user_id": user_id})

app.run(host="127.0.0.1", port=3000)
```

### Request

Represents an HTTP request.

**Properties:**
- `method` (str): HTTP method (GET, POST, etc.)
- `path` (str): Request path
- `headers` (Dict[str, str]): Request headers
- `path_params` (Dict[str, str]): Path parameters extracted from URL
- `query_params` (Dict[str, str]): Query string parameters

**Methods:**
- `json()`: Parse request body as JSON (async)
- `text()`: Get request body as text (async)
- `body()`: Get raw request body as bytes (async)

**Example:**
```python
@app.route("/api/data", methods=["POST"])
async def handle_data(request: Request) -> Response:
    data = await request.json()
    user_agent = request.headers.get("User-Agent", "Unknown")
    return Response({"received": data, "user_agent": user_agent})
```

### Response

Represents an HTTP response.

**Constructor:**
```python
Response(body, status=200, headers=None, content_type=None)
```

**Parameters:**
- `body`: Response body (str, dict, list, or bytes)
- `status` (int): HTTP status code (default: 200)
- `headers` (Dict[str, str]): Additional response headers
- `content_type` (str): Content-Type header (auto-detected if not specified)

**Properties:**
- `body` (bytes): Response body as bytes
- `status` (int): HTTP status code
- `content_type` (str): Content type
- `headers` (Dict[str, str]): Response headers

**Examples:**
```python
# Text response
return Response("Hello, World!")

# JSON response (auto-detected)
return Response({"key": "value"})

# Custom status code
return Response("Not Found", status=404)

# Custom content type
return Response(xml_data, content_type="application/xml")
```

## Advanced Usage

### Multiple Path Parameters

```python
@app.route("/api/users/<user_id>/posts/<post_id>", methods=["GET"])
async def get_post(request: Request, user_id: str, post_id: str) -> Response:
    return Response({
        "user_id": user_id,
        "post_id": post_id
    })
```

### Multiple HTTP Methods

```python
@app.route("/api/resource", methods=["GET", "POST", "PUT", "DELETE"])
async def handle_resource(request: Request) -> Response:
    if request.method == "GET":
        return Response("Getting resource")
    elif request.method == "POST":
        data = await request.json()
        return Response({"created": data})
    elif request.method == "PUT":
        return Response("Updating resource")
    elif request.method == "DELETE":
        return Response("Deleting resource")
```

### Error Handling

```python
@app.route("/api/divide/<int:a>/<int:b>", methods=["GET"])
async def divide(request: Request, a: str, b: str) -> Response:
    try:
        result = int(a) / int(b)
        return Response({"result": result})
    except ValueError:
        return Response("Invalid numbers", status=400)
    except ZeroDivisionError:
        return Response("Cannot divide by zero", status=400)
```

## Performance

Rupy is designed with performance in mind. The current Python implementation uses aiohttp for efficient async I/O. Future releases will include a Rust-backed implementation using Axum + PyO3 for even better performance.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Future Roadmap

- [ ] Rust backend implementation with Axum + PyO3
- [ ] Middleware support
- [ ] WebSocket support
- [ ] Static file serving
- [ ] Template engine integration
- [ ] Database ORM integration
- [ ] Authentication & authorization helpers
- [ ] OpenAPI/Swagger documentation generation

