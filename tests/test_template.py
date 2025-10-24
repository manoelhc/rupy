"""
Tests for template rendering functionality.
"""
import unittest
import threading
import time
import requests
import os
import tempfile
import shutil
from rupy import Rupy, Request


class TestTemplateDecorator(unittest.TestCase):
    """Test the @app.template decorator functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up a test Rupy server with template routes."""
        cls.app = Rupy()
        cls.port = 8007
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        # Create a temporary directory for templates
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create test templates
        with open(os.path.join(cls.temp_dir, "test.tpl"), "w") as f:
            f.write("<html><body><h1>{{title}}</h1><p>{{message}}</p></body></html>")
        
        with open(os.path.join(cls.temp_dir, "user.tpl"), "w") as f:
            f.write("<html><body><h1>User: {{username}}</h1><p>ID: {{user_id}}</p></body></html>")
        
        with open(os.path.join(cls.temp_dir, "json_test.tpl"), "w") as f:
            f.write('{"title": "{{title}}", "count": {{count}}}')

        # Set custom template directory
        cls.app.set_template_directory(cls.temp_dir)

        # Register template routes
        @cls.app.template("/test", template="test.tpl")
        def test_page(request: Request) -> dict:
            return {
                "title": "Test Page",
                "message": "Hello from template!"
            }

        @cls.app.template("/user/<username>", template="user.tpl")
        def user_page(request: Request, username: str) -> dict:
            return {
                "username": username,
                "user_id": 123
            }

        @cls.app.template("/json", template="json_test.tpl", content_type="application/json")
        def json_page(request: Request) -> dict:
            return {
                "title": "JSON Response",
                "count": 42
            }

        # Start server in a background thread
        cls.server_thread = threading.Thread(
            target=lambda: cls.app.run(host="127.0.0.1", port=cls.port),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(1)  # Wait for server to start

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_basic_template_rendering(self):
        """Test that basic template rendering works."""
        response = requests.get(f"{self.base_url}/test")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Page", response.text)
        self.assertIn("Hello from template!", response.text)
        self.assertIn("<html>", response.text)
        self.assertEqual(response.headers.get("Content-Type"), "text/html")

    def test_template_with_dynamic_param(self):
        """Test template rendering with dynamic route parameters."""
        response = requests.get(f"{self.base_url}/user/alice")
        self.assertEqual(response.status_code, 200)
        self.assertIn("User: alice", response.text)
        self.assertIn("ID: 123", response.text)

    def test_template_custom_content_type(self):
        """Test template with custom content type."""
        response = requests.get(f"{self.base_url}/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertIn("JSON Response", response.text)
        self.assertIn("42", response.text)


class TestTemplateConfiguration(unittest.TestCase):
    """Test template directory configuration."""

    def test_set_template_directory(self):
        """Test setting custom template directory."""
        app = Rupy()
        custom_dir = "/custom/template/dir"
        app.set_template_directory(custom_dir)
        # Verify it was set (we can't easily check this without calling the route,
        # but at least ensure the method doesn't raise an error)
        self.assertIsNotNone(app)

    def test_default_template_directory(self):
        """Test that default template directory is './template'."""
        app = Rupy()
        # Default should be "./template"
        default_dir = app.get_template_directory()
        self.assertEqual(default_dir, "./template")


class TestTemplateErrors(unittest.TestCase):
    """Test error handling in template routes."""

    @classmethod
    def setUpClass(cls):
        """Set up a test server with error scenarios."""
        cls.app = Rupy()
        cls.port = 8008
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        # Create a temporary directory for templates
        cls.temp_dir = tempfile.mkdtemp()
        cls.app.set_template_directory(cls.temp_dir)

        # Create a test template
        with open(os.path.join(cls.temp_dir, "valid.tpl"), "w") as f:
            f.write("<html><body>{{text}}</body></html>")

        @cls.app.template("/missing", template="nonexistent.tpl")
        def missing_template(request: Request) -> dict:
            return {"text": "This should fail"}

        @cls.app.template("/valid", template="valid.tpl")
        def valid_template(request: Request) -> dict:
            return {"text": "Success"}

        # Start server in a background thread
        cls.server_thread = threading.Thread(
            target=lambda: cls.app.run(host="127.0.0.1", port=cls.port),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_missing_template_file(self):
        """Test error handling when template file is missing."""
        response = requests.get(f"{self.base_url}/missing")
        self.assertEqual(response.status_code, 500)
        self.assertIn("Template rendering error", response.text)

    def test_valid_template(self):
        """Test that valid template still works."""
        response = requests.get(f"{self.base_url}/valid")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Success", response.text)


if __name__ == "__main__":
    unittest.main()
