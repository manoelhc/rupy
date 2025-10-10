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

## Architecture

- **Rust Backend**: Uses Axum web framework for high-performance HTTP handling
- **Python Bindings**: PyO3 provides seamless Python-Rust interoperability
- **Async Runtime**: Tokio powers the asynchronous server

## License

MIT License - see LICENSE file for details
