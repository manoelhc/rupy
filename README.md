# Rupy

A high-performance Python web framework for building web applications.

## Features

- Simple and intuitive API
- Async/await support
- Path parameters in routes
- JSON request/response handling
- Multiple HTTP methods support

## Installation

```bash
pip install -e .
```

## Quick Start

Create a file named `app.py`:

```python
from rupy import Rupy, Request, Response
from rupy.routing import get, post

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

## API Reference

### Rupy

Main application class.

- `Rupy(module_name)`: Create a new Rupy application
- `route(path, methods)`: Decorator for registering routes
- `run(host, port)`: Start the web server

### Request

Represents an HTTP request.

- `method`: HTTP method (GET, POST, etc.)
- `path`: Request path
- `headers`: Request headers dict
- `path_params`: Path parameters dict
- `query_params`: Query parameters dict
- `json()`: Parse request body as JSON
- `text()`: Get request body as text
- `body()`: Get raw request body as bytes

### Response

Represents an HTTP response.

- `Response(body, status=200, headers=None, content_type=None)`: Create a response
- `body`: Response body as bytes
- `status`: HTTP status code
- `content_type`: Content type header
- `headers`: Response headers dict

## License

MIT License - see LICENSE file for details.
