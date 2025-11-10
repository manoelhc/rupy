#!/usr/bin/env python3
"""
Example demonstrating cookie and authentication token handling in Rupy.

This example shows how to:
1. Set and read cookies in requests/responses
2. Use the auth_token property for Bearer token authentication
3. Delete cookies
"""

from rupy import Rupy, Request, Response

app = Rupy()


@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    """Home page - check for session cookie"""
    session_id = request.get_cookie("session_id")
    
    if session_id:
        return Response(f"Welcome back! Your session: {session_id}")
    else:
        return Response("Welcome! Please login to start a session.")


@app.route("/login", methods=["POST"])
def login(request: Request) -> Response:
    """Login endpoint - sets session cookie and returns auth token"""
    # In a real app, you would validate credentials from request.body
    # For this example, we'll just create a session
    
    resp = Response('{"message": "Login successful", "token": "abc123xyz"}')
    
    # Set a session cookie
    resp.set_cookie(
        "session_id",
        "user-session-123",
        max_age=3600,  # 1 hour
        http_only=True,  # Not accessible via JavaScript
        secure=False,  # Set to True in production with HTTPS
        same_site="Lax"
    )
    
    # Set a user preference cookie
    resp.set_cookie(
        "theme",
        "dark",
        max_age=86400 * 30,  # 30 days
        path="/"
    )
    
    return resp


@app.route("/logout", methods=["POST"])
def logout(request: Request) -> Response:
    """Logout endpoint - deletes session cookie"""
    resp = Response('{"message": "Logged out successfully"}')
    
    # Delete the session cookie
    resp.delete_cookie("session_id")
    resp.delete_cookie("theme")
    
    return resp


@app.route("/profile", methods=["GET"])
def profile(request: Request) -> Response:
    """Protected endpoint that requires authentication"""
    # Check for auth token
    token = request.auth_token
    
    if not token:
        return Response('{"error": "Unauthorized - No token provided"}', status=401)
    
    # In a real app, validate the token here
    if token != "abc123xyz":
        return Response('{"error": "Unauthorized - Invalid token"}', status=401)
    
    # Get user preferences from cookies
    theme = request.get_cookie("theme") or "light"
    
    return Response(f'{{"username": "john_doe", "theme": "{theme}"}}')


@app.route("/preferences", methods=["GET"])
def get_preferences(request: Request) -> Response:
    """Get user preferences from cookies"""
    theme = request.get_cookie("theme") or "light"
    language = request.get_cookie("language") or "en"
    
    return Response(f'{{"theme": "{theme}", "language": "{language}"}}')


@app.route("/preferences", methods=["POST"])
def set_preferences(request: Request) -> Response:
    """Set user preferences as cookies"""
    # In a real app, parse JSON body to get preferences
    # For this example, we'll set some defaults
    
    resp = Response('{"message": "Preferences updated"}')
    
    # Set preference cookies
    resp.set_cookie("theme", "dark", max_age=86400 * 30)
    resp.set_cookie("language", "es", max_age=86400 * 30)
    
    return resp


@app.middleware
def auth_middleware(request: Request):
    """
    Middleware to check authentication for protected routes.
    Demonstrates reading auth_token from requests.
    """
    # Skip auth for public routes
    public_routes = ["/", "/login", "/preferences"]
    if request.path in public_routes or request.method == "OPTIONS":
        return request
    
    # Check for auth token on protected routes
    if request.path.startswith("/profile") or request.path == "/logout":
        token = request.auth_token
        if not token:
            return Response('{"error": "Unauthorized"}', status=401)
    
    return request


if __name__ == "__main__":
    print("=" * 70)
    print("Rupy Cookie and Authentication Example")
    print("=" * 70)
    print("\nStarting server on http://127.0.0.1:8000")
    print("\nEndpoints:")
    print("  GET  /                    - Home page (checks for session)")
    print("  POST /login               - Login and set session cookie")
    print("  POST /logout              - Logout and delete session cookie")
    print("  GET  /profile             - Protected route (requires auth token)")
    print("  GET  /preferences         - Get user preferences from cookies")
    print("  POST /preferences         - Set user preferences as cookies")
    print("\nExample commands:")
    print("  # Login and get cookies")
    print("  curl -c cookies.txt -X POST http://127.0.0.1:8000/login")
    print("\n  # Access home with session cookie")
    print("  curl -b cookies.txt http://127.0.0.1:8000/")
    print("\n  # Access protected profile with Bearer token")
    print('  curl -H "Authorization: Bearer abc123xyz" http://127.0.0.1:8000/profile')
    print("\n  # Logout and delete cookies")
    print("  curl -b cookies.txt -X POST http://127.0.0.1:8000/logout")
    print("\n" + "=" * 70)
    
    app.run(host="127.0.0.1", port=8000)
