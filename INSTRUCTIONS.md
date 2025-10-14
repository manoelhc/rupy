Rupy is a web framework for building web applications in Python. 
However It users Rust (Axum + pyo3) behind the scenes to provide high performance.

# Ergonomics

Rupy is designed to be ergonomic and easy to use. It provides a simple and intuitive API that allows developers to quickly build web applications without having to worry about the underlying implementation details.

Example of a simple web application using Rupy:

```python
from rupy import Rupy, Request, Response

app = Rupy()

@app.route("/", methods=["GET"])
def hello_world(request: Request) -> Response:
    return Response("Hello, World!")

@app.route("/user/<username>", methods=["GET"])
def hello_user(request: Request, username: str) -> Response:
    return Response(f"Hello, {username}!")

@app.route("/echo", methods=["POST"])
def echo(request: Request) -> Response:
    return Response(f"Echo: {request.body}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```
To run the application, save the code to a file named `app.py` and execute it using Python:

```bash
python app.py
```

## Middleware Support

Rupy supports middleware functions that execute before route handlers. This allows you to add cross-cutting concerns like authentication, logging, CORS, etc.

Example with middleware:

```python
from rupy import Rupy, Request, Response

app = Rupy()

@app.middleware
def auth_middleware(request: Request):
    if request.path.startswith("/admin"):
        return Response("Unauthorized", status=401)
    return request

@app.middleware
def logging_middleware(request: Request):
    print(f"Request: {request.method} {request.path}")
    return request

@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Public page")

@app.route("/admin", methods=["GET"])
def admin(request: Request) -> Response:
    return Response("Admin page")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

Middlewares can:
- Inspect and modify requests
- Return early responses (blocking further processing)
- Execute in registration order
- Be used for authentication, logging, CORS, rate limiting, etc.

# Performance

Rupy leverages the performance of Rust and Axum to provide a fast and efficient web framework. It is designed to handle high loads and provide low latency responses.
It was meant to be a high-performance, fastest alternative to existing Python web frameworks like FastAPI and Flask.

It was benchmarked against FastAPI and Flask using `wrk` and the results are as follows:

```bash
$ wrk -t12 -c400 -d30s http://127.0.0.1:8000/
```
