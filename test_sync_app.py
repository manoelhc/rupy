#!/usr/bin/env python3
"""Test sync handler"""

from rupy import Rupy, Request, Response

print("Creating app...")
app = Rupy(__name__)

print("Registering sync route...")
@app.route("/", methods=["GET"])
def hello_sync(request: Request) -> Response:
    print("SYNC Handler called!")
    return Response("Hello from sync handler!")

print("Routes registered:", len(app._routes))
print("About to start server...")
app.run(host="127.0.0.1", port=8001)
