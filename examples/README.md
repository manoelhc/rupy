# Rupy Examples

This directory contains example applications demonstrating various features of Rupy.

## Examples

### 1. Basic App (`basic_app.py`)
A simple application demonstrating basic GET and POST routes.

**Run:**
```bash
python examples/basic_app.py
```

**Test:**
```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/hello
curl -X POST -d 'test data' http://127.0.0.1:8000/echo
```

### 2. REST API (`rest_api.py`)
A complete RESTful API example with all HTTP methods (GET, POST, PUT, PATCH, DELETE).

**Run:**
```bash
python examples/rest_api.py
```

**Test:**
```bash
# List items
curl http://127.0.0.1:8000/items

# Get item
curl http://127.0.0.1:8000/items/1

# Create item
curl -X POST -d '{"name": "New Item"}' http://127.0.0.1:8000/items

# Update item
curl -X PUT -d '{"name": "Updated"}' http://127.0.0.1:8000/items/1

# Patch item
curl -X PATCH -d '{"status": "inactive"}' http://127.0.0.1:8000/items/1

# Delete item
curl -X DELETE http://127.0.0.1:8000/items/1
```

### 3. Dynamic Routes (`dynamic_routes.py`)
Demonstrates dynamic path parameters.

**Run:**
```bash
python examples/dynamic_routes.py
```

**Test:**
```bash
curl http://127.0.0.1:8000/user/alice
curl http://127.0.0.1:8000/blog/john/my-first-post
curl http://127.0.0.1:8000/products/electronics/laptop
```

### 4. All HTTP Methods (`all_methods.py`)
Comprehensive example showing all supported HTTP methods.

**Run:**
```bash
python examples/all_methods.py
```

**Test:**
```bash
curl http://127.0.0.1:8000/resource                      # GET
curl -X POST -d 'data' http://127.0.0.1:8000/resource    # POST
curl -X PUT -d 'data' http://127.0.0.1:8000/resource/1   # PUT
curl -X PATCH -d 'data' http://127.0.0.1:8000/resource/1 # PATCH
curl -X DELETE http://127.0.0.1:8000/resource/1          # DELETE
curl -I http://127.0.0.1:8000/resource                   # HEAD
curl -X OPTIONS http://127.0.0.1:8000/resource           # OPTIONS
```

### 5. Telemetry Example (`telemetry_example.py`)
Demonstrates OpenTelemetry integration for metrics, tracing, and logging.

**Run:**
```bash
python examples/telemetry_example.py
```

### 6. CORS Middleware (`cors_middleware.py`)
Example demonstrating Cross-Origin Resource Sharing (CORS) middleware.

**Features:**
- Middleware execution demonstration
- OPTIONS preflight request handling
- Request logging

**Run:**
```bash
python examples/cors_middleware.py
```

**Test:**
```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/data
curl -X OPTIONS http://127.0.0.1:8000/api/data
curl -X POST -d '{"test": "data"}' http://127.0.0.1:8000/api/data
```

### 7. JWT Authentication Middleware (`jwt_middleware.py`)
Example demonstrating JWT-based authentication middleware.

**Features:**
- Public vs protected routes
- Early response for unauthorized access
- Simulated token validation

**Run:**
```bash
python examples/jwt_middleware.py
```

**Test:**
```bash
# Public endpoints (no auth)
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/public
curl -X POST http://127.0.0.1:8000/login

# Protected endpoints (returns 401)
curl http://127.0.0.1:8000/protected/data
curl http://127.0.0.1:8000/protected/profile
```

### 8. Headers Example (`headers_example.py`)
Example demonstrating HTTP headers access in requests and responses.

**Features:**
- Access request headers like a dictionary
- Set custom response headers
- User-Agent automatic logging
- Middleware with header access

**Run:**
```bash
python examples/headers_example.py
```

**Test:**
```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/headers
curl http://127.0.0.1:8000/echo-agent
curl -H 'User-Agent: MyBot/1.0' http://127.0.0.1:8000/
```

## Notes

- All examples run on `http://127.0.0.1:8000` by default
- You need to have Rupy installed (`maturin develop` or install the wheel)
- Press Ctrl+C to stop the server
