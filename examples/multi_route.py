"""
Multi-route Example - Demonstrates various routing patterns
"""
from rupy import Rupy, Request, Response

app = Rupy(__name__)

@app.route("/", methods=["GET"])
async def home(request: Request) -> Response:
    """Home page"""
    return Response("Welcome to Rupy Multi-Route Example!")

@app.route("/about", methods=["GET"])
async def about(request: Request) -> Response:
    """About page"""
    return Response("This is a Rupy application demonstrating various routes.")

@app.route("/greet/<name>", methods=["GET"])
async def greet(request: Request, name: str) -> Response:
    """Greet a user by name"""
    return Response(f"Hello, {name}! Welcome to Rupy!")

@app.route("/calculate/add/<a>/<b>", methods=["GET"])
async def add(request: Request, a: str, b: str) -> Response:
    """Add two numbers"""
    try:
        result = float(a) + float(b)
        return Response({"operation": "add", "a": a, "b": b, "result": result})
    except ValueError:
        return Response({"error": "Invalid numbers"}, status=400)

@app.route("/calculate/multiply/<a>/<b>", methods=["GET"])
async def multiply(request: Request, a: str, b: str) -> Response:
    """Multiply two numbers"""
    try:
        result = float(a) * float(b)
        return Response({"operation": "multiply", "a": a, "b": b, "result": result})
    except ValueError:
        return Response({"error": "Invalid numbers"}, status=400)

@app.route("/blog/posts/<post_id>", methods=["GET"])
async def get_post(request: Request, post_id: str) -> Response:
    """Get a blog post"""
    return Response({
        "post_id": post_id,
        "title": f"Blog Post #{post_id}",
        "content": "This is a sample blog post.",
        "author": "Demo User"
    })

@app.route("/blog/posts/<post_id>/comments/<comment_id>", methods=["GET"])
async def get_comment(request: Request, post_id: str, comment_id: str) -> Response:
    """Get a specific comment on a post"""
    return Response({
        "post_id": post_id,
        "comment_id": comment_id,
        "text": f"This is comment #{comment_id} on post #{post_id}",
        "author": "Demo Commenter"
    })

@app.route("/search", methods=["GET"])
async def search(request: Request) -> Response:
    """Search endpoint that uses query parameters"""
    query = request.query_params.get("q", "")
    page = request.query_params.get("page", "1")
    
    return Response({
        "query": query,
        "page": page,
        "results": [
            f"Result 1 for '{query}'",
            f"Result 2 for '{query}'",
            f"Result 3 for '{query}'"
        ]
    })

if __name__ == "__main__":
    print("Starting Multi-Route Example")
    print("\nAvailable routes:")
    print("  GET  /")
    print("  GET  /about")
    print("  GET  /greet/<name>")
    print("  GET  /calculate/add/<a>/<b>")
    print("  GET  /calculate/multiply/<a>/<b>")
    print("  GET  /blog/posts/<post_id>")
    print("  GET  /blog/posts/<post_id>/comments/<comment_id>")
    print("  GET  /search?q=<query>&page=<page>")
    print("\nTry these commands:")
    print("  curl http://localhost:8000/")
    print("  curl http://localhost:8000/greet/Alice")
    print("  curl http://localhost:8000/calculate/add/10/20")
    print("  curl http://localhost:8000/blog/posts/42")
    print("  curl http://localhost:8000/blog/posts/42/comments/7")
    print("  curl 'http://localhost:8000/search?q=rupy&page=2'")
    print()
    app.run(host="0.0.0.0", port=8000)
