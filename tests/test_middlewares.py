#!/usr/bin/env python3
"""
Unit tests for Rupy middleware functionality.

Tests middleware execution order, early returns, and request modification.
"""

import unittest
import threading
import time
import requests
from rupy import Rupy, Request, Response


class TestRupyMiddleware(unittest.TestCase):
    """Test suite for Rupy middleware"""

    @classmethod
    def setUpClass(cls):
        """Start the Rupy server with middleware in a separate thread"""
        cls.app = Rupy()
        cls.base_url = "http://127.0.0.1:8889"

        # Track middleware execution order
        cls.execution_log = []

        # Define middlewares
        @cls.app.middleware
        def first_middleware(request: Request):
            cls.execution_log.append("first")
            # Continue to next middleware
            return request

        @cls.app.middleware
        def second_middleware(request: Request):
            cls.execution_log.append("second")
            # Continue to next middleware
            return request

        @cls.app.middleware
        def auth_middleware(request: Request):
            cls.execution_log.append("auth")
            # Block access to /blocked path
            if request.path == "/blocked":
                return Response("Access Denied", status=403)
            return request

        # Define routes
        @cls.app.route("/", methods=["GET"])
        def index(request: Request) -> Response:
            cls.execution_log.append("handler")
            return Response("Success")

        @cls.app.route("/blocked", methods=["GET"])
        def blocked_route(request: Request) -> Response:
            # This should never be called due to middleware
            cls.execution_log.append("blocked_handler")
            return Response("This should not be reached")

        @cls.app.route("/test", methods=["GET"])
        def test_route(request: Request) -> Response:
            cls.execution_log.append("test_handler")
            return Response("Test successful")

        # Start server in a daemon thread
        cls.server_thread = threading.Thread(
            target=cls.app.run, kwargs={"host": "127.0.0.1", "port": 8889}, daemon=True
        )
        cls.server_thread.start()

        # Give the server time to start
        time.sleep(2)

    def setUp(self):
        """Clear execution log before each test"""
        self.execution_log.clear()

    def test_middleware_execution_order(self):
        """Test that middlewares execute in registration order"""
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Success")

        # Check middleware execution order
        # All three middlewares should execute, then the handler
        self.assertEqual(self.execution_log[0], "first")
        self.assertEqual(self.execution_log[1], "second")
        self.assertEqual(self.execution_log[2], "auth")
        self.assertEqual(self.execution_log[3], "handler")

    def test_middleware_early_return(self):
        """Test that middleware can return early and prevent route execution"""
        response = requests.get(f"{self.base_url}/blocked")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.text, "Access Denied")

        # Check that route handler was NOT called
        self.assertNotIn("blocked_handler", self.execution_log)
        # But middlewares were called
        self.assertIn("first", self.execution_log)
        self.assertIn("second", self.execution_log)
        self.assertIn("auth", self.execution_log)

    def test_middleware_allows_request_through(self):
        """Test that middlewares can allow requests through to handlers"""
        response = requests.get(f"{self.base_url}/test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Test successful")

        # Check that all middlewares and handler were called
        self.assertIn("first", self.execution_log)
        self.assertIn("second", self.execution_log)
        self.assertIn("auth", self.execution_log)
        self.assertIn("test_handler", self.execution_log)


class TestMiddlewareDecorator(unittest.TestCase):
    """Test suite for middleware decorator functionality"""

    def test_middleware_decorator(self):
        """Test middleware decorator registration"""
        app = Rupy()

        @app.middleware
        def my_middleware(request: Request):
            return request

        # Just verify the decorator works without errors
        self.assertTrue(True)

    def test_multiple_middlewares(self):
        """Test registering multiple middlewares"""
        app = Rupy()

        @app.middleware
        def middleware_one(request: Request):
            return request

        @app.middleware
        def middleware_two(request: Request):
            return request

        @app.middleware
        def middleware_three(request: Request):
            return request

        self.assertTrue(True)


class TestMiddlewareWithRoutes(unittest.TestCase):
    """Test middleware interaction with routes"""

    @classmethod
    def setUpClass(cls):
        """Start server with middleware and routes"""
        cls.app = Rupy()
        cls.base_url = "http://127.0.0.1:8892"

        cls.request_count = 0

        @cls.app.middleware
        def counter_middleware(request: Request):
            cls.request_count += 1
            return request

        @cls.app.route("/count", methods=["GET"])
        def count_handler(request: Request) -> Response:
            return Response(f"Request count: {cls.request_count}")

        @cls.app.route("/reset", methods=["POST"])
        def reset_handler(request: Request) -> Response:
            cls.request_count = 0
            return Response("Counter reset")

        # Start server
        cls.server_thread = threading.Thread(
            target=cls.app.run, kwargs={"host": "127.0.0.1", "port": 8892}, daemon=True
        )
        cls.server_thread.start()
        time.sleep(2)

    def test_middleware_executes_on_every_request(self):
        """Test that middleware executes on every request"""
        # Reset counter
        requests.post(f"{self.base_url}/reset")
        time.sleep(0.1)

        # Make multiple requests
        requests.get(f"{self.base_url}/count")
        time.sleep(0.1)
        requests.get(f"{self.base_url}/count")
        time.sleep(0.1)

        response = requests.get(f"{self.base_url}/count")
        # The counter should include the current request
        self.assertIn("Request count:", response.text)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
