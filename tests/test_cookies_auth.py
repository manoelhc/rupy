#!/usr/bin/env python3
"""
Unit tests for cookie and auth_token support in Rupy.
"""

import unittest
import threading
import time
import requests
from rupy import Rupy, Request, Response


class TestCookiesAndAuth(unittest.TestCase):
    """Test suite for cookies and auth_token support"""

    @classmethod
    def setUpClass(cls):
        """Start the Rupy server with cookie and auth routes"""
        cls.app = Rupy()
        cls.base_url = "http://127.0.0.1:8893"

        @cls.app.route("/set-cookie", methods=["GET"])
        def set_cookie_handler(request: Request) -> Response:
            """Set a cookie in the response"""
            resp = Response("Cookie set successfully")
            resp.set_cookie("session_id", "abc123", max_age=3600)
            resp.set_cookie("user", "john_doe", path="/", http_only=True)
            return resp

        @cls.app.route("/get-cookie", methods=["GET"])
        def get_cookie_handler(request: Request) -> Response:
            """Get a cookie from the request"""
            session_id = request.get_cookie("session_id")
            user = request.get_cookie("user")
            
            if session_id:
                return Response(f"Session ID: {session_id}, User: {user}")
            else:
                return Response("No cookies found", status=404)

        @cls.app.route("/delete-cookie", methods=["GET"])
        def delete_cookie_handler(request: Request) -> Response:
            """Delete a cookie"""
            resp = Response("Cookie deleted")
            resp.delete_cookie("session_id")
            return resp

        @cls.app.route("/auth-check", methods=["GET"])
        def auth_check_handler(request: Request) -> Response:
            """Check for auth token"""
            token = request.auth_token
            
            if token:
                return Response(f"Authenticated with token: {token}")
            else:
                return Response("No auth token", status=401)

        @cls.app.route("/set-auth", methods=["GET"])
        def set_auth_handler(request: Request) -> Response:
            """Set auth token in response"""
            resp = Response("Auth token set")
            request.set_auth_token("test-token-123")
            # For testing, we'll return the modified request's auth token
            token = request.auth_token
            return Response(f"Token set: {token}")

        # Start server in a daemon thread
        cls.server_thread = threading.Thread(
            target=cls.app.run, kwargs={"host": "127.0.0.1", "port": 8893}, daemon=True
        )
        cls.server_thread.start()

        # Give the server time to start
        time.sleep(2)

    def test_set_cookie(self):
        """Test setting cookies in response"""
        response = requests.get(f"{self.base_url}/set-cookie")
        self.assertEqual(response.status_code, 200)
        self.assertIn("session_id", response.cookies)
        self.assertEqual(response.cookies["session_id"], "abc123")

    def test_get_cookie(self):
        """Test reading cookies from request"""
        cookies = {"session_id": "test123", "user": "alice"}
        response = requests.get(f"{self.base_url}/get-cookie", cookies=cookies)
        self.assertEqual(response.status_code, 200)
        self.assertIn("test123", response.text)
        self.assertIn("alice", response.text)

    def test_get_cookie_not_found(self):
        """Test handling missing cookies"""
        response = requests.get(f"{self.base_url}/get-cookie")
        self.assertEqual(response.status_code, 404)

    def test_delete_cookie(self):
        """Test deleting cookies"""
        response = requests.get(f"{self.base_url}/delete-cookie")
        self.assertEqual(response.status_code, 200)
        # Check that Set-Cookie header is present for deletion
        self.assertIn("set-cookie", response.headers)

    def test_auth_token_present(self):
        """Test reading auth token from Authorization header"""
        headers = {"Authorization": "Bearer my-secret-token"}
        response = requests.get(f"{self.base_url}/auth-check", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("my-secret-token", response.text)

    def test_auth_token_missing(self):
        """Test handling missing auth token"""
        response = requests.get(f"{self.base_url}/auth-check")
        self.assertEqual(response.status_code, 401)

    def test_set_auth_token(self):
        """Test setting auth token"""
        response = requests.get(f"{self.base_url}/set-auth")
        self.assertEqual(response.status_code, 200)
        self.assertIn("test-token-123", response.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
