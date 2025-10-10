#!/usr/bin/env python3
"""Simple example showing Rupy routing"""

from rupy import Rupy, Request, Response

# Create a Rupy application
app = Rupy()

@app.route("/", methods=["GET"])
def hello_world(request: Request) -> Response:
    return Response("Hello, World!")

@app.route("/user/<username>", methods=["GET"])
def hello_user(request: Request, username: str) -> Response:
    return Response(f"Hello, {username}!")

@app.route("/echo", methods=["POST"])
def echo(request: Request) -> Response:
    return Response(f"Echo: {request.body}")

if __name__ == "__main__":
    # Run the server on localhost:8000
    print("Starting Rupy server with routing enabled...")
    print("Try:")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/user/alice")
    print("  curl -X POST -d 'test data' http://127.0.0.1:8000/echo")
    app.run(host="127.0.0.1", port=8000)
