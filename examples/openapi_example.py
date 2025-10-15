#!/usr/bin/env python3
"""
Example demonstrating OpenAPI/Swagger support in Rupy.

This example shows how to:
1. Enable OpenAPI JSON endpoint
2. Configure API documentation
3. Access the OpenAPI specification
"""

from rupy import Rupy, Request, Response

app = Rupy()

# Enable OpenAPI/Swagger JSON endpoint
app.enable_openapi(
    path="/openapi.json",
    title="My API",
    version="1.0.0",
    description="A sample API built with Rupy"
)


@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    """Main page with OpenAPI information"""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Rupy OpenAPI Example</title>
</head>
<body>
    <h1>Rupy OpenAPI/Swagger Example</h1>
    <p>This server has OpenAPI documentation enabled.</p>
    
    <h2>OpenAPI Endpoints:</h2>
    <ul>
        <li><a href="/openapi.json">/openapi.json</a> - OpenAPI 3.0 specification (JSON)</li>
    </ul>
    
    <h2>API Endpoints:</h2>
    <ul>
        <li><a href="/api/users">/api/users</a> - List users</li>
        <li><a href="/api/health">/api/health</a> - Health check</li>
    </ul>
    
    <h2>Viewing the API Documentation:</h2>
    <p>You can view the OpenAPI specification at <a href="/openapi.json">/openapi.json</a></p>
    <p>To view in Swagger UI, you can:</p>
    <ol>
        <li>Go to <a href="https://editor.swagger.io/" target="_blank">Swagger Editor</a></li>
        <li>Copy the JSON from <a href="/openapi.json">/openapi.json</a></li>
        <li>Paste it into the editor</li>
    </ol>
    
    <h2>Test Commands:</h2>
    <pre>
# Get OpenAPI spec
curl http://127.0.0.1:8000/openapi.json | jq

# Get users
curl http://127.0.0.1:8000/api/users

# Health check
curl http://127.0.0.1:8000/api/health
    </pre>
</body>
</html>
"""
    return Response(html)


@app.route("/api/users", methods=["GET"])
def list_users(request: Request) -> Response:
    """
    List all users.
    
    Returns a JSON array of user objects.
    """
    users = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
    ]
    
    import json
    resp = Response(json.dumps(users))
    resp.set_header("Content-Type", "application/json")
    return resp


@app.route("/api/users", methods=["POST"])
def create_user(request: Request) -> Response:
    """
    Create a new user.
    
    Expects JSON body with user data.
    """
    import json
    
    # In a real app, you would parse and validate the request body
    result = {
        "created": True,
        "message": "User created successfully",
        "data": request.body
    }
    
    resp = Response(json.dumps(result), status=201)
    resp.set_header("Content-Type", "application/json")
    return resp


@app.route("/api/users/<user_id>", methods=["GET"])
def get_user(request: Request, user_id: str) -> Response:
    """
    Get a specific user by ID.
    
    Returns a JSON object with user data.
    """
    import json
    
    user = {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }
    
    resp = Response(json.dumps(user))
    resp.set_header("Content-Type", "application/json")
    return resp


@app.route("/api/health", methods=["GET"])
def health_check(request: Request) -> Response:
    """
    Health check endpoint.
    
    Returns the current status of the service.
    """
    import json
    
    health = {
        "status": "healthy",
        "version": "1.0.0",
        "openapi_enabled": True
    }
    
    resp = Response(json.dumps(health))
    resp.set_header("Content-Type", "application/json")
    return resp


if __name__ == "__main__":
    print("=" * 70)
    print("Rupy OpenAPI/Swagger Example")
    print("=" * 70)
    print("\nOpenAPI documentation enabled!")
    print("\nStarting server on http://127.0.0.1:8000")
    print("\nEndpoints:")
    print("  GET  /                    - Main page with documentation")
    print("  GET  /openapi.json        - OpenAPI 3.0 specification")
    print("  GET  /api/users           - List all users")
    print("  POST /api/users           - Create a new user")
    print("  GET  /api/users/<id>      - Get specific user")
    print("  GET  /api/health          - Health check")
    print("\nExample commands:")
    print("  curl http://127.0.0.1:8000/openapi.json | jq")
    print("  curl http://127.0.0.1:8000/api/users")
    print("  curl http://127.0.0.1:8000/api/users/1")
    print('  curl -X POST -d \'{"name":"Dave"}\' http://127.0.0.1:8000/api/users')
    print("  curl http://127.0.0.1:8000/api/health")
    print("\nView the OpenAPI spec in Swagger Editor:")
    print("  https://editor.swagger.io/")
    print("\n" + "=" * 70)
    
    app.run(host="127.0.0.1", port=8000)
