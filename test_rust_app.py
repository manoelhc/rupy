#!/usr/bin/env python3
"""Simple test to verify Rust backend is working"""

from rupy import Rupy, Request, Response

print("Creating app...")
app = Rupy(__name__)

print("Registering route...")
@app.route("/", methods=["GET"])
async def hello(request: Request) -> Response:
    print("Handler called!")
    return Response("Hello from Rust!")

print("Routes registered:", len(app._routes))
print("About to start server...")
app.run(host="127.0.0.1", port=8000)
