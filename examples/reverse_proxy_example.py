#!/usr/bin/env python3
"""
Example demonstrating reverse proxy functionality in Rupy.

This example shows how to:
1. Proxy requests to another backend service
2. Forward headers and request bodies
3. Handle different HTTP methods
"""

from rupy import Rupy, Request, Response
import threading
import time

# Create the main app that will handle proxying
app = Rupy()

# Create a simple backend service to proxy to
backend = Rupy()


# Backend service endpoints
@backend.route("/", methods=["GET"])
def backend_index(request: Request) -> Response:
    return Response('{"service": "backend", "message": "Hello from backend!"}')


@backend.route("/users", methods=["GET"])
def backend_users(request: Request) -> Response:
    return Response('[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]')


@backend.route("/users", methods=["POST"])
def backend_create_user(request: Request) -> Response:
    return Response(f'{{"created": true, "data": {request.body}}}', status=201)


@backend.route("/data/<item_id>", methods=["GET"])
def backend_get_data(request: Request, item_id: str) -> Response:
    return Response(f'{{"id": "{item_id}", "data": "item data"}}')


# Start backend server in a thread
def run_backend():
    backend.run(host="127.0.0.1", port=8001)


backend_thread = threading.Thread(target=run_backend, daemon=True)
backend_thread.start()
time.sleep(1)  # Give backend time to start


# Main app with proxy
@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    """Main page"""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Rupy Reverse Proxy Example</title>
</head>
<body>
    <h1>Rupy Reverse Proxy Example</h1>
    <p>This server proxies requests to a backend service.</p>
    
    <h2>Direct API Endpoints:</h2>
    <ul>
        <li><a href="/direct">/direct</a> - Direct endpoint (not proxied)</li>
        <li><a href="/status">/status</a> - Status endpoint (not proxied)</li>
    </ul>
    
    <h2>Proxied API Endpoints (to backend on port 8001):</h2>
    <ul>
        <li><a href="/api/">/api/</a> - Proxied to backend root</li>
        <li><a href="/api/users">/api/users</a> - Proxied to backend /users</li>
        <li><a href="/api/data/123">/api/data/123</a> - Proxied with parameters</li>
    </ul>
    
    <h2>Test Commands:</h2>
    <pre>
# Get proxied data
curl http://127.0.0.1:8000/api/
curl http://127.0.0.1:8000/api/users

# Post through proxy
curl -X POST -d '{"name":"Charlie"}' http://127.0.0.1:8000/api/users

# Get with path parameter
curl http://127.0.0.1:8000/api/data/456
    </pre>
</body>
</html>
"""
    return Response(html)


@app.route("/direct", methods=["GET"])
def direct(request: Request) -> Response:
    """Direct endpoint that is NOT proxied"""
    return Response('{"message": "This is a direct endpoint, not proxied"}')


@app.route("/status", methods=["GET"])
def status(request: Request) -> Response:
    """Status endpoint"""
    return Response('{"status": "ok", "proxy_enabled": true, "backend": "http://127.0.0.1:8001"}')


# Proxy all /api/* requests to the backend service
@app.proxy("/api", "http://127.0.0.1:8001")
def api_proxy(response: Response) -> Response:
    """Proxy /api/* to backend service"""
    # You can modify the proxied response here if needed
    # For example, add custom headers
    response.set_header("X-Proxied-By", "Rupy Proxy Handler")
    return response


if __name__ == "__main__":
    print("=" * 70)
    print("Rupy Reverse Proxy Example")
    print("=" * 70)
    print("\nStarting backend service on http://127.0.0.1:8001")
    print("Starting proxy service on http://127.0.0.1:8000")
    print("\nThe proxy forwards requests from /api/* to the backend service")
    print("\nEndpoints:")
    print("  GET  /                    - Main page with links")
    print("  GET  /direct              - Direct endpoint (not proxied)")
    print("  GET  /status              - Status endpoint")
    print("  ALL  /api/*               - Proxied to backend service")
    print("\nBackend endpoints (proxied):")
    print("  GET  /api/                - Backend root")
    print("  GET  /api/users           - List users")
    print("  POST /api/users           - Create user")
    print("  GET  /api/data/<id>       - Get data by ID")
    print("\nExample commands:")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/direct")
    print("  curl http://127.0.0.1:8000/api/")
    print("  curl http://127.0.0.1:8000/api/users")
    print("  curl -X POST -d '{\"name\":\"Charlie\"}' http://127.0.0.1:8000/api/users")
    print("\n" + "=" * 70)
    
    app.run(host="127.0.0.1", port=8000)
