#!/usr/bin/env python3
"""
Basic Rupy application demonstrating simple GET and POST routes.
"""

from rupy import Rupy, Request, Response

app = Rupy()


@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Welcome to Rupy! Try /hello or /echo")


@app.route("/hello", methods=["GET"])
def hello(request: Request) -> Response:
    return Response("Hello, World!")


@app.route("/echo", methods=["POST"])
def echo(request: Request) -> Response:
    return Response(f"You sent: {request.body}")


if __name__ == "__main__":
    print("Starting Basic Rupy App on http://127.0.0.1:8000")
    print("Try:")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/hello")
    print("  curl -X POST -d 'test data' http://127.0.0.1:8000/echo")
    app.run(host="127.0.0.1", port=8000)
