#!/usr/bin/env python3
"""
Example demonstrating template rendering with Handlebars.
"""

from rupy import Rupy, Request

app = Rupy()


@app.template("/", template="hello.tpl")
def index(request: Request) -> dict:
    """Render the hello template with context data."""
    return {
        "title": "Welcome Page",
        "greeting": "Hello",
        "name": "World",
        "message": "This page is rendered using Handlebars templates!"
    }


@app.template("/user/<username>", template="user.tpl")
def user_profile(request: Request, username: str) -> dict:
    """Render a user profile page with dynamic route parameter."""
    return {
        "username": username,
        "user_id": 12345
    }


@app.template("/custom", template="hello.tpl", content_type="text/html; charset=utf-8")
def custom_content_type(request: Request) -> dict:
    """Template with custom content type."""
    return {
        "title": "Custom Content Type",
        "greeting": "Bonjour",
        "name": "Monde",
        "message": "This demonstrates custom content-type header!"
    }


if __name__ == "__main__":
    print("Starting Template Example on http://127.0.0.1:8000")
    print("\nExample routes:")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/user/john")
    print("  curl http://127.0.0.1:8000/custom")
    app.run(host="127.0.0.1", port=8000)
