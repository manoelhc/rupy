#!/usr/bin/env python3
"""
Integration tests for all new features:
- Cookies and auth tokens
- Middleware header modification
- Static file serving
- Reverse proxy
- OpenAPI endpoint
"""

import unittest
import threading
import time
import requests
import tempfile
import os
from rupy import Rupy, Request, Response


class TestNewFeatures(unittest.TestCase):
    """Integration tests for new Rupy features"""

    @classmethod
    def setUpClass(cls):
        """Setup test servers"""
        # Create backend server for proxy tests
        cls.backend = Rupy()
        cls.backend_port = 8901
        
        @cls.backend.route("/backend-test", methods=["GET"])
        def backend_test(request: Request) -> Response:
            return Response('{"source": "backend"}')
        
        # Start backend
        cls.backend_thread = threading.Thread(
            target=cls.backend.run,
            kwargs={"host": "127.0.0.1", "port": cls.backend_port},
            daemon=True
        )
        cls.backend_thread.start()
        time.sleep(1)
        
        # Create main app
        cls.app = Rupy()
        cls.app_port = 8900
        cls.base_url = f"http://127.0.0.1:{cls.app_port}"
        
        # Create temp directory for static files
        cls.static_dir = tempfile.mkdtemp()
        with open(os.path.join(cls.static_dir, "test.txt"), "w") as f:
            f.write("Static file content")
        
        # Enable OpenAPI
        cls.app.enable_openapi(
            path="/openapi.json",
            title="Test API",
            version="1.0.0"
        )
        
        # Add middleware that modifies headers
        @cls.app.middleware
        def header_middleware(request: Request):
            request.set_header("X-Test-Header", "added-by-middleware")
            return request
        
        # Static file serving
        @cls.app.static("/static", cls.static_dir)
        def serve_static(response: Response) -> Response:
            return response
        
        # Reverse proxy
        @cls.app.proxy("/proxy", f"http://127.0.0.1:{cls.backend_port}")
        def proxy_backend(response: Response) -> Response:
            return response
        
        # Test routes
        @cls.app.route("/cookies", methods=["GET"])
        def test_cookies(request: Request) -> Response:
            session = request.get_cookie("session")
            resp = Response(f"Session: {session or 'none'}")
            resp.set_cookie("new_cookie", "cookie_value", max_age=3600)
            return resp
        
        @cls.app.route("/auth", methods=["GET"])
        def test_auth(request: Request) -> Response:
            token = request.auth_token
            return Response(f"Token: {token or 'none'}")
        
        @cls.app.route("/headers", methods=["GET"])
        def test_headers(request: Request) -> Response:
            test_header = request.get_header("X-Test-Header")
            return Response(f"Header: {test_header or 'none'}")
        
        # Start main app
        cls.app_thread = threading.Thread(
            target=cls.app.run,
            kwargs={"host": "127.0.0.1", "port": cls.app_port},
            daemon=True
        )
        cls.app_thread.start()
        time.sleep(2)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup"""
        import shutil
        shutil.rmtree(cls.static_dir, ignore_errors=True)
    
    def test_cookies_get_and_set(self):
        """Test cookie reading and setting"""
        # Send request with cookie
        cookies = {"session": "test-session-123"}
        response = requests.get(f"{self.base_url}/cookies", cookies=cookies)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("test-session-123", response.text)
        # Check that new cookie was set
        self.assertIn("new_cookie", response.cookies)
    
    def test_auth_token(self):
        """Test auth token extraction"""
        headers = {"Authorization": "Bearer test-token-xyz"}
        response = requests.get(f"{self.base_url}/auth", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("test-token-xyz", response.text)
    
    def test_middleware_header_modification(self):
        """Test that middleware can modify headers"""
        response = requests.get(f"{self.base_url}/headers")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("added-by-middleware", response.text)
    
    def test_static_file_serving(self):
        """Test static file serving"""
        response = requests.get(f"{self.base_url}/static/test.txt")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Static file content")
    
    def test_static_file_not_found(self):
        """Test 404 for non-existent static file"""
        response = requests.get(f"{self.base_url}/static/nonexistent.txt")
        
        self.assertEqual(response.status_code, 404)
    
    def test_reverse_proxy(self):
        """Test reverse proxy functionality"""
        response = requests.get(f"{self.base_url}/proxy/backend-test")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("backend", response.text)
    
    def test_openapi_endpoint(self):
        """Test OpenAPI endpoint"""
        response = requests.get(f"{self.base_url}/openapi.json")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        
        import json
        spec = json.loads(response.text)
        self.assertEqual(spec["openapi"], "3.0.0")
        self.assertEqual(spec["info"]["title"], "Test API")


if __name__ == "__main__":
    unittest.main(verbosity=2)
