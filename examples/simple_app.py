"""
Example Rupy application
"""
from rupy import Rupy, Request, Response
from rupy.routing import get, post

app = Rupy(__name__)

@app.route("/", methods=["GET"])
async def hello_world(request: Request) -> Response:
    return Response("Hello, World!")

@app.route("/user/<username>", methods=["GET"])
async def hello_user(request: Request, username: str) -> Response:
    return Response(f"Hello, {username}!")

@app.route("/echo", methods=["POST"])
async def echo(request: Request) -> Response:
    data = await request.json()
    return Response(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
