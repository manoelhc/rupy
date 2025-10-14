#!/usr/bin/env python3
"""
Example demonstrating HTTP method-specific decorators.

This example shows how to use the convenient method-specific decorators
like @app.get(), @app.post(), etc. instead of @app.route() with methods parameter.
"""

from rupy import Rupy, Request, Response

app = Rupy()


# Using method-specific decorators is more concise and readable
@app.get("/")
def index(request: Request) -> Response:
    return Response("Welcome! Try different endpoints with different methods.")


# GET - Retrieve data
@app.get("/resource")
def get_resource(request: Request) -> Response:
    return Response("GET: Retrieving resource")


# POST - Create new resource
@app.post("/resource")
def create_resource(request: Request) -> Response:
    return Response(f"POST: Creating resource with data: {request.body}")


# PUT - Update/replace entire resource
@app.put("/resource/<id>")
def update_resource(request: Request, id: str) -> Response:
    return Response(f"PUT: Replacing resource {id} with: {request.body}")


# PATCH - Partially update resource
@app.patch("/resource/<id>")
def patch_resource(request: Request, id: str) -> Response:
    return Response(f"PATCH: Partially updating resource {id} with: {request.body}")


# DELETE - Remove resource
@app.delete("/resource/<id>")
def delete_resource(request: Request, id: str) -> Response:
    return Response(f"DELETE: Removing resource {id}")


# HEAD - Get headers only (no body)
@app.head("/resource")
def head_resource(request: Request) -> Response:
    return Response("HEAD: Metadata only")


# OPTIONS - Get supported methods
@app.options("/resource")
def options_resource(request: Request) -> Response:
    return Response("OPTIONS: Supported methods - GET, POST, HEAD, OPTIONS")


# You can also use multiple decorators on the same path
@app.get("/user/<username>")
def get_user(request: Request, username: str) -> Response:
    return Response(f"GET: User information for {username}")


@app.put("/user/<username>")
def update_user(request: Request, username: str) -> Response:
    return Response(f"PUT: Updating user {username}")


@app.delete("/user/<username>")
def delete_user(request: Request, username: str) -> Response:
    return Response(f"DELETE: Removing user {username}")


if __name__ == "__main__":
    print("Starting Method Decorators Demo on http://127.0.0.1:8000")
    print("\nNew method-specific decorators:")
    print("  @app.get(path)    - For GET requests")
    print("  @app.post(path)   - For POST requests")
    print("  @app.put(path)    - For PUT requests")
    print("  @app.patch(path)  - For PATCH requests")
    print("  @app.delete(path) - For DELETE requests")
    print("  @app.head(path)   - For HEAD requests")
    print("  @app.options(path) - For OPTIONS requests")
    print("\nExample requests:")
    print("  curl http://127.0.0.1:8000/                              # GET /")
    print("  curl http://127.0.0.1:8000/resource                      # GET")
    print("  curl -X POST -d 'data' http://127.0.0.1:8000/resource    # POST")
    print("  curl -X PUT -d 'data' http://127.0.0.1:8000/resource/1   # PUT")
    print("  curl -X PATCH -d 'data' http://127.0.0.1:8000/resource/1 # PATCH")
    print("  curl -X DELETE http://127.0.0.1:8000/resource/1          # DELETE")
    print("  curl -I http://127.0.0.1:8000/resource                   # HEAD")
    print("  curl -X OPTIONS http://127.0.0.1:8000/resource           # OPTIONS")
    print("  curl http://127.0.0.1:8000/user/john                     # GET user")
    app.run(host="127.0.0.1", port=8000)
