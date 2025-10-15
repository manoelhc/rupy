#!/usr/bin/env python3
"""
Unit tests for Rupy headers support.

Tests that Request and Response objects can access headers like a dict.
"""

import unittest
import threading
import time
import requests
from rupy import Rupy, Request, Response


class TestRupyHeaders(unittest.TestCase):
    """Test suite for Rupy headers functionality"""

    @classmethod
    def setUpClass(cls):
        """Start the Rupy server in a separate thread"""
        cls.app = Rupy()
        cls.base_url = "http://127.0.0.1:8891"

        # Define routes for testing headers
        @cls.app.route("/headers", methods=["GET"])
        def headers_handler(request: Request) -> Response:
            # Access headers like a dict
            host = request.headers.get('host', 'unknown')
            user_agent = request.headers.get('user-agent', 'unknown')
            return Response(f"Host: {host}, User-Agent: {user_agent}")

        @cls.app.route("/echo-headers", methods=["GET"])
        def echo_headers_handler(request: Request) -> Response:
            # Echo all headers
            headers_str = ', '.join([f"{k}: {v}" for k, v in request.headers.items()])
            return Response(f"Headers: {headers_str}")

        @cls.app.route("/custom-header", methods=["GET"])
        def custom_header_handler(request: Request) -> Response:
            # Check for custom header
            custom = request.headers.get('x-custom-header', 'not found')
            return Response(f"Custom header: {custom}")

        @cls.app.route("/response-headers", methods=["GET"])
        def response_headers_handler(request: Request) -> Response:
            # Create response with headers
            resp = Response("body with headers")
            resp.set_header('X-Custom-Response', 'test-value')
            return resp

        # Start server in a daemon thread
        cls.server_thread = threading.Thread(
            target=cls.app.run, kwargs={"host": "127.0.0.1", "port": 8891}, daemon=True
        )
        cls.server_thread.start()

        # Give the server time to start
        time.sleep(2)

    def test_request_headers_dict_access(self):
        """Test that request headers can be accessed like a dict"""
        response = requests.get(f"{self.base_url}/headers")
        self.assertEqual(response.status_code, 200)
        # Should contain host and user-agent
        self.assertIn("Host:", response.text)
        self.assertIn("User-Agent:", response.text)
        # Should not be 'unknown'
        self.assertNotIn("Host: unknown", response.text)

    def test_request_custom_header(self):
        """Test that custom headers are accessible"""
        headers = {'X-Custom-Header': 'my-custom-value'}
        response = requests.get(f"{self.base_url}/custom-header", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("my-custom-value", response.text)

    def test_request_headers_iteration(self):
        """Test that request headers can be iterated"""
        response = requests.get(f"{self.base_url}/echo-headers")
        self.assertEqual(response.status_code, 200)
        # Should contain some headers
        self.assertIn("host:", response.text.lower())

    def test_response_headers_property(self):
        """Test that Response has headers property"""
        resp = Response("test body")
        # Should have headers property
        self.assertTrue(hasattr(resp, 'headers'))
        # Should be dict-like
        self.assertIsNotNone(resp.headers)

    def test_response_set_header(self):
        """Test that Response can set headers"""
        resp = Response("test body")
        resp.set_header('X-Test', 'test-value')
        # Should be able to get the header back
        self.assertEqual(resp.get_header('X-Test'), 'test-value')

    def test_request_user_agent_present(self):
        """Test that User-Agent header is present in request"""
        response = requests.get(
            f"{self.base_url}/headers",
            headers={'User-Agent': 'Test-Agent/1.0'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test-Agent/1.0", response.text)


if __name__ == "__main__":
    unittest.main()
