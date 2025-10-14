#!/usr/bin/env python3
"""
Unit tests for Rupy HTTP methods support.

Tests all HTTP verbs (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
and basic routing functionality.
"""

import unittest
import threading
import time
import requests
from rupy import Rupy, Request, Response


class TestRupyHTTPMethods(unittest.TestCase):
    """Test suite for Rupy HTTP methods"""

    @classmethod
    def setUpClass(cls):
        """Start the Rupy server in a separate thread"""
        cls.app = Rupy()
        cls.base_url = "http://127.0.0.1:8888"

        # Define routes for testing
        @cls.app.route("/", methods=["GET"])
        def index(request: Request) -> Response:
            return Response("GET index")

        @cls.app.route("/post", methods=["POST"])
        def post_handler(request: Request) -> Response:
            return Response(f"POST received: {request.body}")

        @cls.app.route("/put", methods=["PUT"])
        def put_handler(request: Request) -> Response:
            return Response(f"PUT received: {request.body}")

        @cls.app.route("/patch", methods=["PATCH"])
        def patch_handler(request: Request) -> Response:
            return Response(f"PATCH received: {request.body}")

        @cls.app.route("/delete", methods=["DELETE"])
        def delete_handler(request: Request) -> Response:
            return Response(f"DELETE received: {request.body}")

        @cls.app.route("/head", methods=["HEAD"])
        def head_handler(request: Request) -> Response:
            return Response("HEAD response")

        @cls.app.route("/options", methods=["OPTIONS"])
        def options_handler(request: Request) -> Response:
            return Response("OPTIONS response")

        @cls.app.route("/user/<username>", methods=["GET"])
        def user_handler(request: Request, username: str) -> Response:
            return Response(f"User: {username}")

        @cls.app.route("/resource/<id>", methods=["PUT", "PATCH", "DELETE"])
        def resource_handler(request: Request, id: str) -> Response:
            return Response(f"{request.method} resource {id}: {request.body}")

        # Start server in a daemon thread
        cls.server_thread = threading.Thread(
            target=cls.app.run, kwargs={"host": "127.0.0.1", "port": 8888}, daemon=True
        )
        cls.server_thread.start()

        # Give the server time to start
        time.sleep(2)

    def test_get_request(self):
        """Test GET request"""
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "GET index")

    def test_post_request(self):
        """Test POST request with body"""
        data = "test post data"
        response = requests.post(f"{self.base_url}/post", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("POST received:", response.text)
        self.assertIn(data, response.text)

    def test_put_request(self):
        """Test PUT request with body"""
        data = "test put data"
        response = requests.put(f"{self.base_url}/put", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("PUT received:", response.text)
        self.assertIn(data, response.text)

    def test_patch_request(self):
        """Test PATCH request with body"""
        data = "test patch data"
        response = requests.patch(f"{self.base_url}/patch", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("PATCH received:", response.text)
        self.assertIn(data, response.text)

    def test_delete_request(self):
        """Test DELETE request with body"""
        data = "test delete data"
        response = requests.delete(f"{self.base_url}/delete", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("DELETE received:", response.text)

    def test_head_request(self):
        """Test HEAD request"""
        response = requests.head(f"{self.base_url}/head")
        self.assertEqual(response.status_code, 200)
        # HEAD response should not have a body
        self.assertEqual(response.text, "")

    def test_options_request(self):
        """Test OPTIONS request"""
        response = requests.options(f"{self.base_url}/options")
        self.assertEqual(response.status_code, 200)

    def test_dynamic_route(self):
        """Test dynamic route with parameter"""
        response = requests.get(f"{self.base_url}/user/alice")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "User: alice")

    def test_dynamic_route_with_put(self):
        """Test dynamic route with PUT method"""
        data = "update data"
        response = requests.put(f"{self.base_url}/resource/123", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("PUT", response.text)
        self.assertIn("123", response.text)

    def test_dynamic_route_with_patch(self):
        """Test dynamic route with PATCH method"""
        data = "patch data"
        response = requests.patch(f"{self.base_url}/resource/456", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("PATCH", response.text)
        self.assertIn("456", response.text)

    def test_dynamic_route_with_delete(self):
        """Test dynamic route with DELETE method"""
        response = requests.delete(f"{self.base_url}/resource/789")
        self.assertEqual(response.status_code, 200)
        self.assertIn("DELETE", response.text)
        self.assertIn("789", response.text)

    def test_404_not_found(self):
        """Test 404 for non-existent route"""
        response = requests.get(f"{self.base_url}/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_method_not_allowed(self):
        """Test that wrong method returns 404"""
        # POST to a GET-only endpoint
        response = requests.post(f"{self.base_url}/")
        self.assertEqual(response.status_code, 404)


class TestRupyRouteDecorator(unittest.TestCase):
    """Test suite for route decorator functionality"""

    def test_route_decorator_with_get(self):
        """Test route decorator with GET method"""
        app = Rupy()

        @app.route("/test", methods=["GET"])
        def handler(request: Request) -> Response:
            return Response("test")

        # Just verify the decorator works without errors
        self.assertTrue(True)

    def test_route_decorator_with_multiple_methods(self):
        """Test route decorator with multiple methods"""
        app = Rupy()

        @app.route("/multi", methods=["GET", "POST", "PUT"])
        def handler(request: Request) -> Response:
            return Response("multi")

        self.assertTrue(True)

    def test_route_decorator_with_parameters(self):
        """Test route decorator with dynamic parameters"""
        app = Rupy()

        @app.route("/item/<id>", methods=["GET"])
        def handler(request: Request, id: str) -> Response:
            return Response(f"Item {id}")

        self.assertTrue(True)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
