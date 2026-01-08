#!/usr/bin/env python3
"""
Unit tests for Rupy query string support.

Tests that Request objects can access and manipulate query strings.
"""

import unittest
import threading
import time
import requests
from rupy import Rupy, Request, Response


class TestRupyQueryString(unittest.TestCase):
    """Test suite for Rupy query string functionality"""

    @classmethod
    def setUpClass(cls):
        """Start the Rupy server in a separate thread"""
        cls.app = Rupy()
        cls.base_url = "http://127.0.0.1:8897"

        # Define routes for testing query strings
        @cls.app.route("/query-keys", methods=["GET"])
        def query_keys_handler(request: Request) -> Response:
            # Get query string keys
            keys = request.get_query_keys()
            return Response(f"Keys: {','.join(keys)}")

        @cls.app.route("/path-without-query", methods=["GET"])
        def path_without_query_handler(request: Request) -> Response:
            # Get path without query string
            path = request.get_path_without_query()
            return Response(f"Path: {path}")

        @cls.app.route("/query-param", methods=["GET"])
        def query_param_handler(request: Request) -> Response:
            # Get specific query parameter
            name = request.get_query_param("name")
            age = request.get_query_param("age")
            return Response(f"Name: {name}, Age: {age}")

        @cls.app.route("/query-params", methods=["GET"])
        def query_params_handler(request: Request) -> Response:
            # Get all query parameters
            params = request.query_params
            param_str = ','.join([f"{k}={v}" for k, v in params.items()])
            return Response(f"Params: {param_str}")

        @cls.app.route("/search", methods=["GET"])
        def search_handler(request: Request) -> Response:
            # Real-world example: search endpoint
            query = request.get_query_param("q")
            page = request.get_query_param("page") or "1"
            limit = request.get_query_param("limit") or "10"
            return Response(f"Search: q={query}, page={page}, limit={limit}")

        # Start server in a daemon thread
        cls.server_thread = threading.Thread(
            target=cls.app.run, kwargs={"host": "127.0.0.1", "port": 8897}, daemon=True
        )
        cls.server_thread.start()

        # Give the server time to start
        time.sleep(2)

    def test_get_query_keys_empty(self):
        """Test getting query keys when no query string"""
        response = requests.get(f"{self.base_url}/query-keys")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Keys: ", response.text)

    def test_get_query_keys_single(self):
        """Test getting query keys with single parameter"""
        response = requests.get(f"{self.base_url}/query-keys?name=John")
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.text)

    def test_get_query_keys_multiple(self):
        """Test getting query keys with multiple parameters"""
        response = requests.get(f"{self.base_url}/query-keys?name=John&age=30&city=NYC")
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.text)
        self.assertIn("age", response.text)
        self.assertIn("city", response.text)

    def test_get_path_without_query_no_query(self):
        """Test getting path without query when no query string"""
        response = requests.get(f"{self.base_url}/path-without-query")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Path: /path-without-query", response.text)

    def test_get_path_without_query_with_query(self):
        """Test getting path without query when query string exists"""
        response = requests.get(f"{self.base_url}/path-without-query?name=John&age=30")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Path: /path-without-query", response.text)
        self.assertNotIn("?", response.text)

    def test_get_query_param_exists(self):
        """Test getting a specific query parameter that exists"""
        response = requests.get(f"{self.base_url}/query-param?name=Alice&age=25")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Name: Alice", response.text)
        self.assertIn("Age: 25", response.text)

    def test_get_query_param_not_exists(self):
        """Test getting a query parameter that doesn't exist"""
        response = requests.get(f"{self.base_url}/query-param?name=Bob")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Name: Bob", response.text)
        self.assertIn("Age: None", response.text)

    def test_get_query_params_dict(self):
        """Test getting all query parameters as dict"""
        response = requests.get(f"{self.base_url}/query-params?name=John&age=30&city=NYC")
        self.assertEqual(response.status_code, 200)
        self.assertIn("name=John", response.text)
        self.assertIn("age=30", response.text)
        self.assertIn("city=NYC", response.text)

    def test_search_with_query_params(self):
        """Test real-world search endpoint with query parameters"""
        response = requests.get(f"{self.base_url}/search?q=python&page=2&limit=20")
        self.assertEqual(response.status_code, 200)
        self.assertIn("q=python", response.text)
        self.assertIn("page=2", response.text)
        self.assertIn("limit=20", response.text)

    def test_search_with_default_values(self):
        """Test search endpoint with only required parameter"""
        response = requests.get(f"{self.base_url}/search?q=rust")
        self.assertEqual(response.status_code, 200)
        self.assertIn("q=rust", response.text)
        self.assertIn("page=1", response.text)
        self.assertIn("limit=10", response.text)


if __name__ == "__main__":
    unittest.main()
