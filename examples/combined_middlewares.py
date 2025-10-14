#!/usr/bin/env python3
"""
Example combining multiple middlewares with routes.

This example demonstrates:
1. Multiple middleware execution in order
2. Middleware for logging
3. Middleware for authentication
4. Middleware for rate limiting (simulated)
"""

from rupy import Rupy, Request, Response
import time

app = Rupy()

# Track request counts per path
request_counts = {}
last_reset = time.time()


@app.middleware
def logging_middleware(request: Request):
    """Log all incoming requests."""
    print(f"[LOG] {request.method} {request.path}")
    return request


@app.middleware
def rate_limit_middleware(request: Request):
    """
    Simple rate limiting middleware.
    Limits requests to 10 per minute per endpoint.
    """
    global request_counts, last_reset

    # Reset counts every 60 seconds
    if time.time() - last_reset > 60:
        request_counts = {}
        last_reset = time.time()

    # Track request count
    path = request.path
    request_counts[path] = request_counts.get(path, 0) + 1

    # Check rate limit
    if request_counts[path] > 10:
        print(f"[RATE LIMIT] Blocked {path} - too many requests")
        return Response(
            '{"error": "Rate limit exceeded. Try again later."}', status=429
        )

    print(f"[RATE LIMIT] {path} - Request {request_counts[path]}/10")
    return request


@app.middleware
def auth_middleware(request: Request):
    """
    Authentication middleware.
    Blocks access to /admin routes without authentication.
    """
    if request.path.startswith("/admin"):
        print(f"[AUTH] Checking authentication for {request.path}")
        # In real implementation, check for valid token/session
        # For demo, always block admin routes
        return Response('{"error": "Unauthorized - Admin access required"}', status=401)

    return request


# Public routes
@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Welcome! Middleware demo is running.")


@app.route("/public", methods=["GET"])
def public_endpoint(request: Request) -> Response:
    return Response('{"message": "This is a public endpoint"}')


@app.route("/status", methods=["GET"])
def status_endpoint(request: Request) -> Response:
    return Response(
        f'{{"requests": {dict(request_counts)}, "uptime": {int(time.time() - last_reset)}}}'
    )


# Protected routes
@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard(request: Request) -> Response:
    # This handler should never be called due to auth middleware
    return Response("Admin Dashboard - This should not be visible")


@app.route("/admin/users", methods=["GET"])
def admin_users(request: Request) -> Response:
    # This handler should never be called due to auth middleware
    return Response("Admin Users - This should not be visible")


if __name__ == "__main__":
    print("=" * 70)
    print("Rupy Middleware Combination Example")
    print("=" * 70)
    print("\nActive Middlewares:")
    print("  1. Logging Middleware - logs all requests")
    print("  2. Rate Limit Middleware - limits to 10 requests/min per endpoint")
    print("  3. Auth Middleware - blocks /admin/* routes")
    print("\nStarting server on http://127.0.0.1:8000")
    print("\nPublic endpoints:")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/public")
    print("  curl http://127.0.0.1:8000/status")
    print("\nProtected endpoints (will return 401):")
    print("  curl http://127.0.0.1:8000/admin/dashboard")
    print("  curl http://127.0.0.1:8000/admin/users")
    print("\nRate limit test (run >10 times quickly):")
    print("  for i in {1..15}; do curl http://127.0.0.1:8000/public; done")
    print("\n" + "=" * 70)

    app.run(host="127.0.0.1", port=8000)
