#!/usr/bin/env python3
"""
Example demonstrating headers access in Rupy.

This example shows how to:
1. Access request headers like a dict
2. Set response headers
3. User-Agent logging
"""

from rupy import Rupy, Request, Response

app = Rupy()


@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    """
    Access headers from the request like a dictionary.
    """
    # Access headers using dict-like syntax
    user_agent = request.headers.get('user-agent', 'Unknown')
    host = request.headers.get('host', 'Unknown')
    
    # Build response
    message = f"Hello! Your browser is: {user_agent}\n"
    message += f"You're accessing: {host}\n"
    
    return Response(message)


@app.route("/headers", methods=["GET"])
def show_headers(request: Request) -> Response:
    """
    Display all request headers.
    """
    headers_list = []
    for key, value in request.headers.items():
        headers_list.append(f"{key}: {value}")
    
    response_text = "Request Headers:\n" + "\n".join(headers_list)
    return Response(response_text)


@app.route("/custom-response", methods=["GET"])
def custom_response(request: Request) -> Response:
    """
    Return a response with custom headers.
    """
    resp = Response("Response with custom headers")
    resp.set_header('X-Custom-Header', 'MyValue')
    resp.set_header('X-Powered-By', 'Rupy')
    
    return resp


@app.route("/echo-agent", methods=["GET"])
def echo_agent(request: Request) -> Response:
    """
    Echo the User-Agent header.
    """
    user_agent = request.headers.get('user-agent', 'Not provided')
    return Response(f"Your User-Agent: {user_agent}")


@app.middleware
def logging_middleware(request: Request):
    """
    Log request with User-Agent information.
    The User-Agent is automatically logged by Rupy in the structured logs.
    """
    user_agent = request.headers.get('user-agent', 'unknown')
    print(f"[Middleware] Request from {user_agent} to {request.path}")
    return request


if __name__ == "__main__":
    print("=" * 70)
    print("Rupy Headers Example")
    print("=" * 70)
    print("\nStarting server on http://127.0.0.1:8000")
    print("\nTry these commands:")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/headers")
    print("  curl http://127.0.0.1:8000/echo-agent")
    print("  curl -H 'User-Agent: MyBot/1.0' http://127.0.0.1:8000/")
    print("\nNote: User-Agent is automatically logged in the JSON logs")
    print("Set RUST_LOG=info to see structured JSON logs")
    print("\n" + "=" * 70 + "\n")
    
    app.run(host="127.0.0.1", port=8000)
