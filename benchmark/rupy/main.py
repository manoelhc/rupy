from rupy import Rupy, Request, Response

app = Rupy()

@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Hello, World!")

@app.route("/user/<username>", methods=["GET"])
def get_user(request: Request, username: str) -> Response:
    return Response(f"User: {username}")

@app.route("/echo", methods=["POST"])
def echo(request: Request) -> Response:
    return Response(f"Echo: {request.body}")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)