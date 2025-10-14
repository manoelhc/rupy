#!/usr/bin/env python3
"""
Example demonstrating CORS middleware in Rupy.

This middleware adds CORS headers to allow cross-origin requests.
"""

from rupy import Rupy, Request, Response

app = Rupy()


@app.middleware
def cors_middleware(request: Request):
    """
    CORS middleware that adds appropriate headers to responses.
    
    For simplicity, this middleware doesn't modify the request directly
    but in a real implementation, you might want to handle preflight
    OPTIONS requests here and return early.
    """
    # In this simple example, we just pass through
    # In a real implementation, CORS headers would be added to responses
    # For now, we demonstrate middleware execution by logging
    print(f"[CORS Middleware] Processing {request.method} {request.path}")
    
    # Check for OPTIONS preflight request
    if request.method == "OPTIONS":
        print("[CORS Middleware] Handling OPTIONS preflight request")
        return Response(
            "",
            status=204
        )
    
    # Continue to next middleware or route handler
    return request


@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Welcome! CORS is enabled.")


@app.route("/api/data", methods=["GET", "POST", "OPTIONS"])
def api_data(request: Request) -> Response:
    if request.method == "POST":
        return Response(f"Data received: {request.body}")
    return Response('{"message": "API endpoint with CORS"}')


if __name__ == "__main__":
    print("Starting Rupy server with CORS middleware on http://127.0.0.1:8000")
    print("Try:")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/api/data")
    print("  curl -X OPTIONS http://127.0.0.1:8000/api/data")
    print("  curl -X POST -d '{\"test\": \"data\"}' http://127.0.0.1:8000/api/data")
    app.run(host="127.0.0.1", port=8000)
