#!/usr/bin/env python3
"""
Advanced test demonstrating practical use cases for @app.proxy and @app.static
with Response modification capabilities.
"""

import unittest
import threading
import time
import requests
import tempfile
import os
from rupy import Rupy, Request, Response


class TestAdvancedProxyStaticUseCases(unittest.TestCase):
    """Test advanced use cases for proxy and static with response modification"""

    @classmethod
    def setUpClass(cls):
        """Setup test servers"""
        # Create backend server
        cls.backend = Rupy()
        cls.backend_port = 8701
        
        @cls.backend.route("/data", methods=["GET"])
        def backend_api(request: Request) -> Response:
            return Response('{"status": "ok", "data": [1, 2, 3]}')
        
        @cls.backend.route("/secure", methods=["GET"])
        def backend_secure(request: Request) -> Response:
            # This backend doesn't handle CORS
            return Response('{"secure": "data"}')
        
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
        cls.app_port = 8700
        cls.base_url = f"http://127.0.0.1:{cls.app_port}"
        
        # Create temp directory for static files
        cls.static_dir = tempfile.mkdtemp()
        
        # Create various types of files
        with open(os.path.join(cls.static_dir, "public.html"), "w") as f:
            f.write("<html><body>Public Page</body></html>")
        
        with open(os.path.join(cls.static_dir, "style.css"), "w") as f:
            f.write("body { color: red; }")
        
        with open(os.path.join(cls.static_dir, "app.js"), "w") as f:
            f.write("console.log('app');")
        
        # Static file serving with conditional caching based on file type
        @cls.app.static("/assets", cls.static_dir)
        def serve_assets(response: Response) -> Response:
            # Add different cache headers based on content type
            content_type = response.headers.get("Content-Type", "")
            
            if "css" in content_type or "javascript" in content_type:
                # Cache CSS and JS for 1 hour
                response.set_header("Cache-Control", "public, max-age=3600")
            elif "html" in content_type:
                # Don't cache HTML
                response.set_header("Cache-Control", "no-cache")
            
            # Add security headers for all static files
            response.set_header("X-Content-Type-Options", "nosniff")
            
            return response
        
        # Proxy with CORS headers injection
        @cls.app.proxy("/proxy", f"http://127.0.0.1:{cls.backend_port}")
        def proxy_with_cors(response: Response) -> Response:
            # Add CORS headers to proxied responses
            response.set_header("Access-Control-Allow-Origin", "*")
            response.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
            response.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            
            # Track that this was proxied
            response.set_header("X-Proxy-Source", "rupy-proxy")
            
            return response
        
        # Proxy with error handling and custom error messages
        @cls.app.proxy("/guarded", f"http://127.0.0.1:{cls.backend_port}")
        def proxy_with_error_handling(response: Response) -> Response:
            # If the backend returns an error, customize the error message
            if response.status >= 400:
                response.set_header("X-Error-Handled", "true")
            
            # Add custom security header
            response.set_header("X-Frame-Options", "DENY")
            
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
    
    def test_static_conditional_caching_css(self):
        """Test that CSS files get long cache times"""
        response = requests.get(f"{self.base_url}/assets/style.css")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("color: red", response.text)
        
        # Check CSS-specific caching
        self.assertEqual(response.headers.get("Cache-Control"), "public, max-age=3600")
        
        # Check security header
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
    
    def test_static_conditional_caching_js(self):
        """Test that JavaScript files get long cache times"""
        response = requests.get(f"{self.base_url}/assets/app.js")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("console.log", response.text)
        
        # Check JS-specific caching
        self.assertEqual(response.headers.get("Cache-Control"), "public, max-age=3600")
    
    def test_static_conditional_caching_html(self):
        """Test that HTML files don't get cached"""
        response = requests.get(f"{self.base_url}/assets/public.html")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Public Page", response.text)
        
        # Check HTML-specific no-cache
        self.assertEqual(response.headers.get("Cache-Control"), "no-cache")
    
    def test_proxy_adds_cors_headers(self):
        """Test that proxy adds CORS headers to backend responses"""
        response = requests.get(f"{self.base_url}/proxy/data")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("ok", response.text)
        
        # Check CORS headers were added
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "*")
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Methods"), 
            "GET, POST, PUT, DELETE"
        )
        
        # Check tracking header
        self.assertEqual(response.headers.get("X-Proxy-Source"), "rupy-proxy")
    
    def test_proxy_adds_cors_to_secure_endpoint(self):
        """Test CORS is added even to secure endpoints"""
        response = requests.get(f"{self.base_url}/proxy/secure")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("secure", response.text)
        
        # CORS should be added by proxy handler
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "*")
    
    def test_guarded_proxy_security_headers(self):
        """Test that guarded proxy adds security headers"""
        response = requests.get(f"{self.base_url}/guarded/data")
        
        self.assertEqual(response.status_code, 200)
        
        # Check security header
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
    
    def test_guarded_proxy_error_handling(self):
        """Test that guarded proxy handles errors specially"""
        response = requests.get(f"{self.base_url}/guarded/nonexistent")
        
        # Should get 404 from backend
        self.assertEqual(response.status_code, 404)
        
        # But our handler should mark it as handled
        self.assertEqual(response.headers.get("X-Error-Handled"), "true")


if __name__ == "__main__":
    unittest.main(verbosity=2)
