#!/usr/bin/env python3
"""
Unit tests for middleware header modification in Rupy.
"""

import unittest
import threading
import time
import requests
from rupy import Rupy, Request, Response


class TestMiddlewareHeaderModification(unittest.TestCase):
    """Test suite for middleware header modification"""

    @classmethod
    def setUpClass(cls):
        """Start the Rupy server with header-modifying middleware"""
        cls.app = Rupy()
        cls.base_url = "http://127.0.0.1:8894"

        @cls.app.middleware
        def add_custom_header_middleware(request: Request):
            """Middleware that adds a custom header to the request"""
            request.set_header("X-Custom-Header", "added-by-middleware")
            request.set_header("X-Request-ID", "req-123")
            return request

        @cls.app.middleware
        def modify_auth_middleware(request: Request):
            """Middleware that modifies the Authorization header"""
            # If no auth header, add a default one for internal routes
            if request.path.startswith("/internal"):
                if not request.get_header("authorization"):
                    request.set_header("authorization", "Bearer internal-token")
            return request

        @cls.app.route("/headers", methods=["GET"])
        def show_headers(request: Request) -> Response:
            """Echo back the headers received"""
            custom_header = request.get_header("X-Custom-Header") or "not found"
            request_id = request.get_header("X-Request-ID") or "not found"
            auth_header = request.get_header("authorization") or "not found"
            
            return Response(
                f"X-Custom-Header: {custom_header}\n"
                f"X-Request-ID: {request_id}\n"
                f"Authorization: {auth_header}"
            )

        @cls.app.route("/internal/data", methods=["GET"])
        def internal_data(request: Request) -> Response:
            """Internal endpoint that should have auth header added by middleware"""
            auth_header = request.get_header("authorization") or "not found"
            return Response(f"Authorization: {auth_header}")

        # Start server in a daemon thread
        cls.server_thread = threading.Thread(
            target=cls.app.run, kwargs={"host": "127.0.0.1", "port": 8894}, daemon=True
        )
        cls.server_thread.start()

        # Give the server time to start
        time.sleep(2)

    def test_middleware_adds_headers(self):
        """Test that middleware can add headers to requests"""
        response = requests.get(f"{self.base_url}/headers")
        self.assertEqual(response.status_code, 200)
        self.assertIn("added-by-middleware", response.text)
        self.assertIn("req-123", response.text)

    def test_middleware_modifies_auth_header(self):
        """Test that middleware can add/modify auth headers"""
        response = requests.get(f"{self.base_url}/internal/data")
        self.assertEqual(response.status_code, 200)
        self.assertIn("internal-token", response.text)

    def test_middleware_preserves_existing_headers(self):
        """Test that middleware doesn't break existing headers"""
        headers = {"User-Agent": "TestClient/1.0"}
        response = requests.get(f"{self.base_url}/headers", headers=headers)
        self.assertEqual(response.status_code, 200)
        # Should still have the middleware-added headers
        self.assertIn("added-by-middleware", response.text)


class TestMiddlewareCookieModification(unittest.TestCase):
    """Test suite for middleware cookie modification"""

    @classmethod
    def setUpClass(cls):
        """Start server with cookie-modifying middleware"""
        cls.app = Rupy()
        cls.base_url = "http://127.0.0.1:8895"

        @cls.app.middleware
        def cookie_middleware(request: Request):
            """Middleware that can read and set cookies"""
            # Add a tracking cookie if not present
            if not request.get_cookie("tracking_id"):
                request.set_cookie("tracking_id", "track-123")
            return request

        @cls.app.route("/cookies", methods=["GET"])
        def show_cookies(request: Request) -> Response:
            """Show cookies received"""
            tracking = request.get_cookie("tracking_id") or "not found"
            session = request.get_cookie("session") or "not found"
            
            return Response(f"tracking_id: {tracking}\nsession: {session}")

        # Start server
        cls.server_thread = threading.Thread(
            target=cls.app.run, kwargs={"host": "127.0.0.1", "port": 8895}, daemon=True
        )
        cls.server_thread.start()
        time.sleep(2)

    def test_middleware_adds_cookie(self):
        """Test that middleware can add cookies to request"""
        response = requests.get(f"{self.base_url}/cookies")
        self.assertEqual(response.status_code, 200)
        # The middleware should have added the tracking cookie
        self.assertIn("track-123", response.text)

    def test_middleware_preserves_existing_cookies(self):
        """Test that middleware preserves existing cookies"""
        cookies = {"session": "user-session-456"}
        response = requests.get(f"{self.base_url}/cookies", cookies=cookies)
        self.assertEqual(response.status_code, 200)
        # Should have both cookies
        self.assertIn("track-123", response.text)
        self.assertIn("user-session-456", response.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
