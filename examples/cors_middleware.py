#!/usr/bin/env python3
"""
Real-world CORS (Cross-Origin Resource Sharing) Middleware Example for Rupy

This example demonstrates production-ready CORS handling with comprehensive
support for various CORS scenarios.

Features:
- Configurable allowed origins (specific domains or wildcard)
- Support for credentials (cookies, authorization headers)
- Preflight request handling (OPTIONS method)
- Configurable allowed methods and headers
- Proper CORS header management
- Security best practices

CORS is essential for web applications where:
- Frontend (e.g., React at https://app.example.com) needs to call
  backend APIs (e.g., at https://api.example.com)
- Mobile apps need to access your API
- Third-party integrations need to access your endpoints
"""

from rupy import Rupy, Request, Response

app = Rupy()

# ============================================================================
# CORS Configuration
# ============================================================================

# Allowed origins - in production, use specific domains
# Examples:
#   - ["https://app.example.com", "https://admin.example.com"]  # Specific domains
#   - ["*"]  # Allow all (use with caution, not recommended for production with credentials)
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React development server
    "http://localhost:8080",  # Vue development server
    "https://app.example.com",  # Production frontend
]

# For development, you might want to allow all origins
# ALLOWED_ORIGINS = ["*"]

# Allowed HTTP methods
ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

# Allowed headers that clients can send
ALLOWED_HEADERS = [
    "Content-Type",
    "Authorization",
    "X-Requested-With",
    "X-Custom-Header",
]

# Headers that can be exposed to the client
EXPOSED_HEADERS = ["X-Total-Count", "X-Page-Number"]

# Allow credentials (cookies, authorization headers)
# Set to False if using wildcard origin (*)
ALLOW_CREDENTIALS = True

# Max age for preflight cache (in seconds)
MAX_AGE = 86400  # 24 hours


def is_origin_allowed(origin: str) -> bool:
    """
    Check if the origin is allowed based on configuration.
    
    Args:
        origin: The Origin header value from the request
    
    Returns:
        True if origin is allowed, False otherwise
    """
    if not origin:
        return False
    
    # Allow all origins if wildcard is configured
    if "*" in ALLOWED_ORIGINS:
        return True
    
    # Check if origin is in the allowed list
    return origin in ALLOWED_ORIGINS


def add_cors_headers(response: Response, origin: str) -> Response:
    """
    Add CORS headers to a response.
    
    Args:
        response: The Response object to add headers to
        origin: The origin to allow
    
    Returns:
        Response with CORS headers added
    """
    # Set the allowed origin
    if "*" in ALLOWED_ORIGINS:
        response.set_header("Access-Control-Allow-Origin", "*")
    else:
        response.set_header("Access-Control-Allow-Origin", origin)
    
    # Allow credentials if configured
    if ALLOW_CREDENTIALS and "*" not in ALLOWED_ORIGINS:
        response.set_header("Access-Control-Allow-Credentials", "true")
    
    # Set allowed methods
    response.set_header("Access-Control-Allow-Methods", ", ".join(ALLOWED_METHODS))
    
    # Set allowed headers
    response.set_header("Access-Control-Allow-Headers", ", ".join(ALLOWED_HEADERS))
    
    # Set exposed headers
    if EXPOSED_HEADERS:
        response.set_header("Access-Control-Expose-Headers", ", ".join(EXPOSED_HEADERS))
    
    # Set max age for preflight cache
    response.set_header("Access-Control-Max-Age", str(MAX_AGE))
    
    return response


@app.middleware
def cors_middleware(request: Request):
    """
    Production-ready CORS middleware.
    
    This middleware:
    1. Checks if the origin is allowed
    2. Handles preflight OPTIONS requests
    3. Adds appropriate CORS headers to responses
    4. Blocks requests from disallowed origins
    """
    print(f"[CORS] Processing {request.method} {request.path}")
    
    # Get the Origin header from the request
    origin = request.headers.get("Origin", "")
    
    print(f"[CORS] Request origin: {origin if origin else 'None'}")
    
    # If no origin header, it's not a CORS request (likely same-origin)
    # Allow it to proceed
    if not origin:
        print("[CORS] No origin header, allowing request (same-origin)")
        return request
    
    # Check if origin is allowed
    if not is_origin_allowed(origin):
        print(f"[CORS] Origin {origin} not allowed, blocking request")
        response = Response("CORS policy: Origin not allowed", status=403)
        return response
    
    print(f"[CORS] Origin {origin} is allowed")
    
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        print("[CORS] Handling preflight OPTIONS request")
        
        # Check if this is a CORS preflight request
        # Preflight requests have Access-Control-Request-Method header
        access_control_request_method = request.headers.get("Access-Control-Request-Method", "")
        
        if access_control_request_method:
            print(f"[CORS] Preflight for method: {access_control_request_method}")
            
            # Create preflight response
            response = Response("", status=204)  # No content
            response = add_cors_headers(response, origin)
            
            return response
        else:
            # Regular OPTIONS request, not a preflight
            print("[CORS] Regular OPTIONS request, continuing to handler")
            return request
    
    # For all other requests, continue to the next middleware/handler
    # CORS headers will be added to the response in a real implementation
    # For this demo, we'll add a note that handlers should add CORS headers
    print(f"[CORS] Allowing {request.method} request from {origin}")
    
    # Note: In a production system with full response middleware support,
    # we would intercept the response here and add CORS headers
    # For now, handlers need to add them manually if needed
    
    return request


# ============================================================================
# Route Handlers
# ============================================================================

@app.route("/", methods=["GET", "OPTIONS"])
def index(request: Request) -> Response:
    """Root endpoint with CORS support."""
    origin = request.headers.get("Origin", "")
    
    response = Response('{"message": "CORS-enabled API", "version": "1.0"}')
    response.set_header("Content-Type", "application/json")
    
    # Add CORS headers for actual request
    if origin and is_origin_allowed(origin):
        response = add_cors_headers(response, origin)
    
    return response


@app.route("/api/users", methods=["GET", "POST", "OPTIONS"])
def api_users(request: Request) -> Response:
    """API endpoint demonstrating CORS with different methods."""
    origin = request.headers.get("Origin", "")
    
    if request.method == "GET":
        # Return list of users
        response = Response('''
        {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
                {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
            ],
            "total": 3
        }
        ''')
        response.set_header("Content-Type", "application/json")
        response.set_header("X-Total-Count", "3")
        
    elif request.method == "POST":
        # Create new user
        response = Response('''
        {
            "message": "User created successfully",
            "user": {"id": 4, "name": "New User", "email": "new@example.com"}
        }
        ''')
        response.set_header("Content-Type", "application/json")
    
    else:
        response = Response("Method not allowed", status=405)
    
    # Add CORS headers
    if origin and is_origin_allowed(origin):
        response = add_cors_headers(response, origin)
    
    return response


@app.route("/api/data", methods=["GET", "PUT", "DELETE", "OPTIONS"])
def api_data(request: Request) -> Response:
    """API endpoint demonstrating CORS with various methods."""
    origin = request.headers.get("Origin", "")
    
    if request.method == "GET":
        response = Response('{"data": "Some important data", "timestamp": "2024-01-15T10:30:00Z"}')
    elif request.method == "PUT":
        response = Response(f'{{"message": "Data updated", "body": "{request.body}"}}')
    elif request.method == "DELETE":
        response = Response('{"message": "Data deleted successfully"}')
    else:
        response = Response("Method not allowed", status=405)
    
    response.set_header("Content-Type", "application/json")
    
    # Add CORS headers
    if origin and is_origin_allowed(origin):
        response = add_cors_headers(response, origin)
    
    return response


@app.route("/api/credentials", methods=["GET", "OPTIONS"])
def api_credentials(request: Request) -> Response:
    """
    Endpoint that requires credentials (cookies, auth headers).
    Demonstrates CORS with credentials.
    """
    origin = request.headers.get("Origin", "")
    
    # Check for authorization
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header:
        response = Response('{"error": "Unauthorized", "message": "Authorization header required"}', status=401)
    else:
        response = Response('{"message": "Authenticated data", "user": "john_doe"}')
    
    response.set_header("Content-Type", "application/json")
    
    # Add CORS headers with credentials support
    if origin and is_origin_allowed(origin):
        response = add_cors_headers(response, origin)
    
    return response


if __name__ == "__main__":
    print("=" * 80)
    print("CORS Middleware Example - Production Ready")
    print("=" * 80)
    print("\nStarting server on http://127.0.0.1:8000")
    
    print(f"\nCORS Configuration:")
    print(f"  Allowed Origins: {ALLOWED_ORIGINS}")
    print(f"  Allowed Methods: {ALLOWED_METHODS}")
    print(f"  Allowed Headers: {ALLOWED_HEADERS}")
    print(f"  Allow Credentials: {ALLOW_CREDENTIALS}")
    print(f"  Max Age: {MAX_AGE} seconds")
    
    print("\n" + "=" * 80)
    print("Testing CORS:")
    print("=" * 80)
    
    print("\n1. Simple CORS request (GET):")
    print('   curl -H "Origin: http://localhost:3000" \\')
    print('     http://127.0.0.1:8000/')
    
    print("\n2. Preflight request (OPTIONS):")
    print('   curl -X OPTIONS \\')
    print('     -H "Origin: http://localhost:3000" \\')
    print('     -H "Access-Control-Request-Method: POST" \\')
    print('     -H "Access-Control-Request-Headers: Content-Type" \\')
    print('     http://127.0.0.1:8000/api/users')
    
    print("\n3. POST request with CORS:")
    print('   curl -X POST \\')
    print('     -H "Origin: http://localhost:3000" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"name": "Test User", "email": "test@example.com"}\' \\')
    print('     http://127.0.0.1:8000/api/users')
    
    print("\n4. Request with credentials:")
    print('   curl -H "Origin: http://localhost:3000" \\')
    print('     -H "Authorization: Bearer test-token-123" \\')
    print('     http://127.0.0.1:8000/api/credentials')
    
    print("\n5. Request from disallowed origin (will be blocked):")
    print('   curl -H "Origin: http://evil.example.com" \\')
    print('     http://127.0.0.1:8000/')
    
    print("\n6. Same-origin request (no CORS headers needed):")
    print('   curl http://127.0.0.1:8000/')
    
    print("\n" + "=" * 80)
    print("Frontend JavaScript Example:")
    print("=" * 80)
    print("""
    // Fetch API example
    fetch('http://127.0.0.1:8000/api/users', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer your-token'
        },
        credentials: 'include',  // Include cookies
        body: JSON.stringify({
            name: 'New User',
            email: 'user@example.com'
        })
    })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));
    """)
    
    print("=" * 80)
    print()
    
    app.run(host="127.0.0.1", port=8000)

