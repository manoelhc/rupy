#!/usr/bin/env python3
"""
Dynamic routing example demonstrating path parameters.
"""

from rupy import Rupy, Request, Response

app = Rupy()


@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Dynamic Routes Demo. Try /user/<name> or /blog/<author>/<post>")


@app.route("/user/<username>", methods=["GET"])
def user_profile(request: Request, username: str) -> Response:
    return Response(f"User Profile: {username}")


@app.route("/blog/<author>/<post_id>", methods=["GET"])
def blog_post(request: Request, author: str, post_id: str) -> Response:
    return Response(f"Blog post {post_id} by {author}")


@app.route("/api/v1/<resource>/<id>", methods=["GET"])
def api_resource(request: Request, resource: str, id: str) -> Response:
    return Response(f"API v1: {resource}/{id}")


@app.route("/products/<category>/<product_id>", methods=["GET"])
def product_details(request: Request, category: str, product_id: str) -> Response:
    return Response(f"Product {product_id} in category {category}")


if __name__ == "__main__":
    print("Starting Dynamic Routes App on http://127.0.0.1:8000")
    print("\nTry these URLs:")
    print("  curl http://127.0.0.1:8000/user/alice")
    print("  curl http://127.0.0.1:8000/blog/john/my-first-post")
    print("  curl http://127.0.0.1:8000/api/v1/users/123")
    print("  curl http://127.0.0.1:8000/products/electronics/laptop-x1")
    app.run(host="127.0.0.1", port=8000)
