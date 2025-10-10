"""
Tests for Rupy framework
"""
import asyncio
from rupy import Rupy, Request, Response
from rupy.routing import GET, POST


def test_request_creation():
    """Test Request object creation"""
    req = Request(
        method="GET",
        path="/test",
        headers={"Content-Type": "application/json"},
        body=b'{"key": "value"}'
    )
    assert req.method == "GET"
    assert req.path == "/test"
    assert req.headers["Content-Type"] == "application/json"


async def test_request_json():
    """Test Request JSON parsing"""
    req = Request(
        method="POST",
        path="/test",
        headers={},
        body=b'{"key": "value"}'
    )
    data = await req.json()
    assert data == {"key": "value"}


async def test_request_text():
    """Test Request text parsing"""
    req = Request(
        method="POST",
        path="/test",
        headers={},
        body=b"Hello, World!"
    )
    text = await req.text()
    assert text == "Hello, World!"


def test_response_string():
    """Test Response with string body"""
    resp = Response("Hello, World!")
    assert resp.body == b"Hello, World!"
    assert resp.status == 200
    assert resp.content_type == "text/plain"


def test_response_json():
    """Test Response with JSON body"""
    resp = Response({"key": "value"})
    assert resp.status == 200
    assert resp.content_type == "application/json"
    assert b"key" in resp.body
    assert b"value" in resp.body


def test_response_status():
    """Test Response with custom status"""
    resp = Response("Not Found", status=404)
    assert resp.status == 404


def test_app_creation():
    """Test Rupy app creation"""
    app = Rupy(__name__)
    assert app is not None
    assert len(app.routes) == 0


def test_route_decorator():
    """Test route decorator"""
    app = Rupy(__name__)
    
    @app.route("/test", methods=["GET"])
    async def test_handler(request: Request) -> Response:
        return Response("Test")
    
    assert len(app.routes) == 1
    assert app.routes[0].path == "/test"
    assert app.routes[0].methods == ["GET"]


def test_route_matching():
    """Test route path matching"""
    from rupy.app import Route
    
    async def handler(request):
        return Response("Test")
    
    # Test simple path
    route = Route("/test", handler, ["GET"])
    params = route.match("/test", "GET")
    assert params == {}
    
    # Test path with parameter
    route = Route("/user/<username>", handler, ["GET"])
    params = route.match("/user/john", "GET")
    assert params == {"username": "john"}
    
    # Test non-matching path
    params = route.match("/other", "GET")
    assert params is None
    
    # Test non-matching method
    params = route.match("/user/john", "POST")
    assert params is None


def test_multiple_path_params():
    """Test route with multiple path parameters"""
    from rupy.app import Route
    
    async def handler(request):
        return Response("Test")
    
    route = Route("/users/<user_id>/posts/<post_id>", handler, ["GET"])
    params = route.match("/users/123/posts/456", "GET")
    assert params == {"user_id": "123", "post_id": "456"}


if __name__ == "__main__":
    # Run tests
    print("Running tests...")
    
    test_request_creation()
    print("✓ test_request_creation passed")
    
    asyncio.run(test_request_json())
    print("✓ test_request_json passed")
    
    asyncio.run(test_request_text())
    print("✓ test_request_text passed")
    
    test_response_string()
    print("✓ test_response_string passed")
    
    test_response_json()
    print("✓ test_response_json passed")
    
    test_response_status()
    print("✓ test_response_status passed")
    
    test_app_creation()
    print("✓ test_app_creation passed")
    
    test_route_decorator()
    print("✓ test_route_decorator passed")
    
    test_route_matching()
    print("✓ test_route_matching passed")
    
    test_multiple_path_params()
    print("✓ test_multiple_path_params passed")
    
    print("\nAll tests passed!")
