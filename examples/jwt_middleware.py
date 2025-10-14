#!/usr/bin/env python3
"""
Example demonstrating JWT authentication middleware in Rupy.

This middleware checks for a valid JWT token in the Authorization header
and blocks requests that don't have a valid token.
"""

from rupy import Rupy, Request, Response

app = Rupy()

# In a real application, you would:
# 1. Use a proper JWT library like PyJWT
# 2. Validate tokens against a secret key
# 3. Check token expiration
# 4. Extract user information from the token

# For this example, we'll use a simple token validation
VALID_TOKEN = "secret-token-123"


@app.middleware
def jwt_auth_middleware(request: Request):
    """
    JWT authentication middleware that checks for valid tokens.

    Checks the Authorization header for a Bearer token and validates it.
    Returns 401 Unauthorized if the token is missing or invalid.
    """
    print(f"[JWT Auth Middleware] Checking auth for {request.method} {request.path}")

    # Skip authentication for public routes
    if request.path in ["/", "/login", "/public"]:
        print("[JWT Auth Middleware] Public route, skipping auth")
        return request

    # In a real implementation, you would extract the token from headers
    # For this example, we'll simulate checking for a token
    # Since we don't have header access in this simplified version,
    # we'll demonstrate the concept

    # Simulate token extraction from Authorization header
    # In a real implementation: token = request.get_header("Authorization")
    token = None  # Placeholder

    if token and token.startswith("Bearer "):
        actual_token = token[7:]  # Remove "Bearer " prefix
        if actual_token == VALID_TOKEN:
            print("[JWT Auth Middleware] Token valid, allowing request")
            return request

    # For demo purposes, let's check if path contains "protected"
    # In real use, you would always check the token
    if "protected" in request.path:
        print("[JWT Auth Middleware] Protected route without valid token")
        return Response(
            '{"error": "Unauthorized - Invalid or missing JWT token"}', status=401
        )

    # Allow through for demo
    return request


@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Welcome! This is a public endpoint.")


@app.route("/login", methods=["POST"])
def login(request: Request) -> Response:
    """Simulated login endpoint that returns a JWT token."""
    return Response(f'{{"token": "{VALID_TOKEN}", "message": "Login successful"}}')


@app.route("/public", methods=["GET"])
def public_endpoint(request: Request) -> Response:
    return Response("This is a public endpoint, no auth required.")


@app.route("/protected/data", methods=["GET"])
def protected_data(request: Request) -> Response:
    """Protected endpoint that requires authentication."""
    return Response('{"data": "This is protected data", "user": "authenticated"}')


@app.route("/protected/profile", methods=["GET"])
def protected_profile(request: Request) -> Response:
    """Another protected endpoint."""
    return Response('{"profile": "User profile information"}')


if __name__ == "__main__":
    print(
        "Starting Rupy server with JWT authentication middleware on http://127.0.0.1:8000"
    )
    print("\nPublic endpoints (no auth required):")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/public")
    print("  curl -X POST http://127.0.0.1:8000/login")
    print("\nProtected endpoints (returns 401 in this demo):")
    print("  curl http://127.0.0.1:8000/protected/data")
    print("  curl http://127.0.0.1:8000/protected/profile")
    print(
        "\nNote: In a real app, you would send the token from /login in the Authorization header"
    )
    app.run(host="127.0.0.1", port=8000)
