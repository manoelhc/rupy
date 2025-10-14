#!/usr/bin/env python3
"""
Comprehensive example demonstrating all supported HTTP methods.
"""

from rupy import Rupy, Request, Response

app = Rupy()


# GET - Retrieve data
@app.route("/resource", methods=["GET"])
def get_resource(request: Request) -> Response:
    return Response("GET: Retrieving resource")


# POST - Create new resource
@app.route("/resource", methods=["POST"])
def create_resource(request: Request) -> Response:
    return Response(f"POST: Creating resource with data: {request.body}")


# PUT - Update/replace entire resource
@app.route("/resource/<id>", methods=["PUT"])
def update_resource(request: Request, id: str) -> Response:
    return Response(f"PUT: Replacing resource {id} with: {request.body}")


# PATCH - Partially update resource
@app.route("/resource/<id>", methods=["PATCH"])
def patch_resource(request: Request, id: str) -> Response:
    return Response(f"PATCH: Partially updating resource {id} with: {request.body}")


# DELETE - Remove resource
@app.route("/resource/<id>", methods=["DELETE"])
def delete_resource(request: Request, id: str) -> Response:
    return Response(f"DELETE: Removing resource {id}")


# HEAD - Get headers only (no body)
@app.route("/resource", methods=["HEAD"])
def head_resource(request: Request) -> Response:
    return Response("HEAD: Metadata only")


# OPTIONS - Get supported methods
@app.route("/resource", methods=["OPTIONS"])
def options_resource(request: Request) -> Response:
    return Response("OPTIONS: Supported methods - GET, POST, HEAD, OPTIONS")


if __name__ == "__main__":
    print("Starting All HTTP Methods Demo on http://127.0.0.1:8000")
    print("\nSupported HTTP Methods:")
    print("  curl http://127.0.0.1:8000/resource                      # GET")
    print("  curl -X POST -d 'data' http://127.0.0.1:8000/resource    # POST")
    print("  curl -X PUT -d 'data' http://127.0.0.1:8000/resource/1   # PUT")
    print("  curl -X PATCH -d 'data' http://127.0.0.1:8000/resource/1 # PATCH")
    print("  curl -X DELETE http://127.0.0.1:8000/resource/1          # DELETE")
    print("  curl -I http://127.0.0.1:8000/resource                   # HEAD")
    print("  curl -X OPTIONS http://127.0.0.1:8000/resource           # OPTIONS")
    app.run(host="127.0.0.1", port=8000)
