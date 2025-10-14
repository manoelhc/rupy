#!/usr/bin/env python3
"""
Unit tests for Rupy method-specific decorators.

Tests all HTTP method decorators (get, post, put, patch, delete, head, options).
"""

import unittest
import threading
import time
import requests
from rupy import Rupy, Request, Response


class TestMethodDecorators(unittest.TestCase):
    """Test suite for method-specific decorators"""

    @classmethod
    def setUpClass(cls):
        """Start the Rupy server in a separate thread"""
        cls.app = Rupy()
        cls.base_url = "http://127.0.0.1:8890"

        # Define routes using method-specific decorators
        @cls.app.get("/get-route")
        def get_handler(request: Request) -> Response:
            return Response("GET response")

        @cls.app.post("/post-route")
        def post_handler(request: Request) -> Response:
            return Response("POST response")

        @cls.app.put("/put-route")
        def put_handler(request: Request) -> Response:
            return Response("PUT response")

        @cls.app.patch("/patch-route")
        def patch_handler(request: Request) -> Response:
            return Response("PATCH response")

        @cls.app.delete("/delete-route")
        def delete_handler(request: Request) -> Response:
            return Response("DELETE response")

        @cls.app.head("/head-route")
        def head_handler(request: Request) -> Response:
            return Response("HEAD response")

        @cls.app.options("/options-route")
        def options_handler(request: Request) -> Response:
            return Response("OPTIONS response")

        # Test with dynamic parameters
        @cls.app.get("/user/<username>")
        def user_handler(request: Request, username: str) -> Response:
            return Response(f"User: {username}")

        @cls.app.delete("/resource/<id>")
        def resource_handler(request: Request, id: str) -> Response:
            return Response(f"Deleted: {id}")

        # Start server in a daemon thread
        cls.server_thread = threading.Thread(
            target=cls.app.run, kwargs={"host": "127.0.0.1", "port": 8890}, daemon=True
        )
        cls.server_thread.start()

        # Give the server time to start
        time.sleep(2)

    def test_get_decorator(self):
        """Test @app.get decorator"""
        response = requests.get(f"{self.base_url}/get-route")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "GET response")

    def test_post_decorator(self):
        """Test @app.post decorator"""
        response = requests.post(f"{self.base_url}/post-route")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "POST response")

    def test_put_decorator(self):
        """Test @app.put decorator"""
        response = requests.put(f"{self.base_url}/put-route")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "PUT response")

    def test_patch_decorator(self):
        """Test @app.patch decorator"""
        response = requests.patch(f"{self.base_url}/patch-route")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "PATCH response")

    def test_delete_decorator(self):
        """Test @app.delete decorator"""
        response = requests.delete(f"{self.base_url}/delete-route")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "DELETE response")

    def test_head_decorator(self):
        """Test @app.head decorator"""
        response = requests.head(f"{self.base_url}/head-route")
        self.assertEqual(response.status_code, 200)
        # HEAD requests should not have a body
        self.assertEqual(response.text, "")

    def test_options_decorator(self):
        """Test @app.options decorator"""
        response = requests.options(f"{self.base_url}/options-route")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "OPTIONS response")

    def test_get_with_dynamic_param(self):
        """Test @app.get decorator with dynamic parameters"""
        response = requests.get(f"{self.base_url}/user/john")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "User: john")

    def test_delete_with_dynamic_param(self):
        """Test @app.delete decorator with dynamic parameters"""
        response = requests.delete(f"{self.base_url}/resource/123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Deleted: 123")

    def test_wrong_method_on_get_decorator(self):
        """Test that using wrong method on @app.get returns 404"""
        response = requests.post(f"{self.base_url}/get-route")
        self.assertEqual(response.status_code, 404)

    def test_wrong_method_on_post_decorator(self):
        """Test that using wrong method on @app.post returns 404"""
        response = requests.get(f"{self.base_url}/post-route")
        self.assertEqual(response.status_code, 404)


class TestDecoratorRegistration(unittest.TestCase):
    """Test suite for decorator registration functionality"""

    def test_get_decorator_registration(self):
        """Test @app.get decorator registration"""
        app = Rupy()

        @app.get("/test")
        def handler(request: Request) -> Response:
            return Response("test")

        # Just verify the decorator works without errors
        self.assertTrue(True)

    def test_post_decorator_registration(self):
        """Test @app.post decorator registration"""
        app = Rupy()

        @app.post("/test")
        def handler(request: Request) -> Response:
            return Response("test")

        self.assertTrue(True)

    def test_put_decorator_registration(self):
        """Test @app.put decorator registration"""
        app = Rupy()

        @app.put("/test")
        def handler(request: Request) -> Response:
            return Response("test")

        self.assertTrue(True)

    def test_patch_decorator_registration(self):
        """Test @app.patch decorator registration"""
        app = Rupy()

        @app.patch("/test")
        def handler(request: Request) -> Response:
            return Response("test")

        self.assertTrue(True)

    def test_delete_decorator_registration(self):
        """Test @app.delete decorator registration"""
        app = Rupy()

        @app.delete("/test")
        def handler(request: Request) -> Response:
            return Response("test")

        self.assertTrue(True)

    def test_head_decorator_registration(self):
        """Test @app.head decorator registration"""
        app = Rupy()

        @app.head("/test")
        def handler(request: Request) -> Response:
            return Response("test")

        self.assertTrue(True)

    def test_options_decorator_registration(self):
        """Test @app.options decorator registration"""
        app = Rupy()

        @app.options("/test")
        def handler(request: Request) -> Response:
            return Response("test")

        self.assertTrue(True)

    def test_multiple_method_decorators(self):
        """Test registering multiple routes with different method decorators"""
        app = Rupy()

        @app.get("/resource")
        def get_resource(request: Request) -> Response:
            return Response("GET")

        @app.post("/resource")
        def post_resource(request: Request) -> Response:
            return Response("POST")

        @app.delete("/resource/<id>")
        def delete_resource(request: Request, id: str) -> Response:
            return Response(f"DELETE {id}")

        self.assertTrue(True)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
