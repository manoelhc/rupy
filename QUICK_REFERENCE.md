# Quick Reference Guide - New Features

## Cookie Support

### Request Cookies
```python
# Get a cookie
session_id = request.get_cookie("session_id")

# Get all cookies
all_cookies = request.cookies

# Set a cookie in middleware
request.set_cookie("tracking_id", "abc123")
```

### Response Cookies
```python
# Set a cookie with options
response.set_cookie(
    "session_id",
    "abc123",
    max_age=3600,        # Expires in 1 hour
    path="/",            # Cookie path
    domain=None,         # Cookie domain
    secure=True,         # HTTPS only
    http_only=True,      # Not accessible via JS
    same_site="Lax"      # CSRF protection
)

# Delete a cookie
response.delete_cookie("session_id", path="/")
```

## Authentication Token

### Using auth_token Property
```python
# Get Bearer token from Authorization header
token = request.auth_token

# Set Bearer token (adds "Bearer " prefix automatically)
request.auth_token = "my-secret-token"

# Check in middleware
@app.middleware
def auth_middleware(request: Request):
    if request.path.startswith("/protected"):
        if not request.auth_token:
            return Response("Unauthorized", status=401)
    return request
```

## Middleware Header Modification

```python
@app.middleware
def add_headers_middleware(request: Request):
    # Add custom headers
    request.set_header("X-Request-ID", "req-123")
    request.set_header("X-Custom", "value")
    
    # Modify existing headers
    request.set_header("User-Agent", "Modified-Agent")
    
    # These headers will be available in route handlers
    return request

@app.route("/test", methods=["GET"])
def test(request: Request) -> Response:
    # Headers set by middleware are accessible here
    req_id = request.get_header("X-Request-ID")
    return Response(f"Request ID: {req_id}")
```

## Static File Serving

```python
from rupy import Rupy, Response

app = Rupy()

# Serve files from ./public directory at /static path
# The handler receives a Response object with the file content
# and can modify it before returning
@app.static("/static", "./public")
def serve_static(response: Response) -> Response:
    # Optionally modify the response
    response.set_header("Cache-Control", "max-age=3600")
    response.set_header("X-Served-By", "My App")
    return response

# Now files are accessible:
# ./public/style.css    -> http://localhost:8000/static/style.css
# ./public/app.js        -> http://localhost:8000/static/app.js
# ./public/images/logo.png -> http://localhost:8000/static/images/logo.png
```

Features:
- ✅ Automatic content-type detection
- ✅ Directory traversal protection
- ✅ 404 for non-existent files
- ✅ 403 for security violations
- ✅ Handler receives Response object for modification

## Reverse Proxy

```python
from rupy import Rupy, Response

app = Rupy()

# Proxy all /api/* requests to backend service
# The handler receives a Response object with the proxied content
# and can modify it before returning
@app.proxy("/api", "http://backend-service:8080")
def api_proxy(response: Response) -> Response:
    # Optionally modify the proxied response
    response.set_header("X-Proxied-By", "My App")
    # Could also filter/transform content here
    return response

# Requests are forwarded:
# /api/users        -> http://backend-service:8080/users
# /api/data/123     -> http://backend-service:8080/data/123
# /api/v1/endpoint  -> http://backend-service:8080/v1/endpoint
```

Features:
- ✅ All HTTP methods supported (GET, POST, PUT, PATCH, DELETE)
- ✅ Headers preserved and forwarded
- ✅ Request body preserved
- ✅ Response headers returned
- ✅ Handler receives Response object for modification

## OpenAPI/Swagger

```python
from rupy import Rupy

app = Rupy()

# Enable OpenAPI endpoint
app.enable_openapi(
    path="/openapi.json",         # Custom path (optional)
    title="My API",               # API title
    version="1.0.0",              # API version
    description="API docs"        # Description
)

# Disable if needed
app.disable_openapi()

# Access the spec at:
# http://localhost:8000/openapi.json
```

To view in Swagger UI:
1. Go to https://editor.swagger.io/
2. Copy JSON from your /openapi.json endpoint
3. Paste into the editor

## Complete Example

```python
from rupy import Rupy, Request, Response

app = Rupy()

# Enable OpenAPI
app.enable_openapi(title="My App", version="1.0.0")

# Serve static files with custom caching headers
@app.static("/static", "./public")
def serve_static(response: Response) -> Response:
    response.set_header("Cache-Control", "max-age=3600")
    return response

# Proxy to backend with custom header
@app.proxy("/api", "http://backend:8080")
def api_proxy(response: Response) -> Response:
    response.set_header("X-Proxied-By", "My App")
    return response

# Authentication middleware
@app.middleware
def auth_middleware(request: Request):
    # Check token for protected routes
    if request.path.startswith("/protected"):
        if not request.auth_token:
            return Response("Unauthorized", status=401)
    return request

# Routes with cookies
@app.route("/login", methods=["POST"])
def login(request: Request) -> Response:
    resp = Response('{"status": "logged in"}')
    resp.set_cookie("session_id", "abc123", max_age=3600, http_only=True)
    return resp

@app.route("/profile", methods=["GET"])
def profile(request: Request) -> Response:
    session = request.get_cookie("session_id")
    if not session:
        return Response("Not logged in", status=401)
    return Response(f"Session: {session}")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
```

## Testing

### With curl
```bash
# Cookie test
curl -b "session=abc123" http://localhost:8000/profile

# Auth token test
curl -H "Authorization: Bearer my-token" http://localhost:8000/protected

# Static file
curl http://localhost:8000/static/style.css

# Proxied request
curl http://localhost:8000/api/users

# OpenAPI spec
curl http://localhost:8000/openapi.json
```

### With Python requests
```python
import requests

# With cookies
cookies = {"session_id": "abc123"}
response = requests.get("http://localhost:8000/profile", cookies=cookies)

# With auth token
headers = {"Authorization": "Bearer my-token"}
response = requests.get("http://localhost:8000/protected", headers=headers)
```

## Tips

1. **Cookies**: Use `http_only=True` for security
2. **Auth Tokens**: Validate tokens in middleware
3. **Static Files**: Use a CDN in production
4. **Reverse Proxy**: Set appropriate timeouts for backend
5. **OpenAPI**: Keep it updated as you add endpoints
