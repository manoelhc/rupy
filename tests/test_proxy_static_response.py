#!/usr/bin/env python3
"""
Test that @app.proxy and @app.static decorators pass Response objects
to handler functions, allowing them to modify the response.
"""

import unittest
import threading
import time
import requests
import tempfile
import os
from rupy import Rupy, Request, Response


class TestProxyStaticResponse(unittest.TestCase):
    """Test that proxy and static handlers receive and can modify Response objects"""

    @classmethod
    def setUpClass(cls):
        """Setup test servers"""
        # Create backend server for proxy tests
        cls.backend = Rupy()
        cls.backend_port = 8801
        
        @cls.backend.route("/test", methods=["GET"])
        def backend_test(request: Request) -> Response:
            return Response('{"message": "from backend"}')
        
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
        cls.app_port = 8800
        cls.base_url = f"http://127.0.0.1:{cls.app_port}"
        
        # Create temp directory for static files
        cls.static_dir = tempfile.mkdtemp()
        with open(os.path.join(cls.static_dir, "test.txt"), "w") as f:
            f.write("Original content")
        with open(os.path.join(cls.static_dir, "data.json"), "w") as f:
            f.write('{"key": "value"}')
        
        # Static file serving with response modification
        @cls.app.static("/static", cls.static_dir)
        def serve_static(response: Response) -> Response:
            # Modify the response - add custom header
            response.set_header("X-Custom-Static", "modified-by-handler")
            # Also add cache control
            response.set_header("Cache-Control", "max-age=3600")
            return response
        
        # Reverse proxy with response modification
        @cls.app.proxy("/api", f"http://127.0.0.1:{cls.backend_port}")
        def proxy_backend(response: Response) -> Response:
            # Modify the proxied response - add custom header
            response.set_header("X-Custom-Proxy", "modified-by-handler")
            # Modify the content if it's JSON
            if response.body:
                # Just add a header, don't modify body to keep it simple
                response.set_header("X-Content-Modified", "true")
            return response
        
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
    
    def test_static_response_modification(self):
        """Test that static file handler receives and can modify Response"""
        response = requests.get(f"{self.base_url}/static/test.txt")
        
        # Check file content is served
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Original content")
        
        # Check custom headers added by the handler
        self.assertEqual(response.headers.get("X-Custom-Static"), "modified-by-handler")
        self.assertEqual(response.headers.get("Cache-Control"), "max-age=3600")
    
    def test_static_json_response_modification(self):
        """Test static handler for JSON files"""
        response = requests.get(f"{self.base_url}/static/data.json")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("key", response.text)
        
        # Check custom header
        self.assertEqual(response.headers.get("X-Custom-Static"), "modified-by-handler")
    
    def test_proxy_response_modification(self):
        """Test that proxy handler receives and can modify Response"""
        response = requests.get(f"{self.base_url}/api/test")
        
        # Check proxied content is served
        self.assertEqual(response.status_code, 200)
        self.assertIn("from backend", response.text)
        
        # Check custom headers added by the handler
        self.assertEqual(response.headers.get("X-Custom-Proxy"), "modified-by-handler")
        self.assertEqual(response.headers.get("X-Content-Modified"), "true")
    
    def test_static_404_response(self):
        """Test that handler receives 404 responses too"""
        response = requests.get(f"{self.base_url}/static/nonexistent.txt")
        
        # Should still get 404
        self.assertEqual(response.status_code, 404)
        
        # But handler should still process it
        self.assertEqual(response.headers.get("X-Custom-Static"), "modified-by-handler")


if __name__ == "__main__":
    unittest.main(verbosity=2)
