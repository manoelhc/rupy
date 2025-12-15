#!/usr/bin/env python3
"""
Unit tests for Rupy file upload decorator.

Tests the @app.upload decorator functionality including:
- Basic file upload
- MIME type filtering
- File size limits
- Multiple file uploads
"""

import unittest
import threading
import time
import requests
import tempfile
import os
import json
from rupy import Rupy, Request, Response, UploadFile
from typing import List


class TestUploadDecorator(unittest.TestCase):
    """Test suite for file upload decorator"""

    @classmethod
    def setUpClass(cls):
        """Start the Rupy server in a separate thread"""
        cls.app = Rupy()
        cls.base_url = "http://127.0.0.1:8896"
        cls.upload_dir = tempfile.mkdtemp()

        # Define upload routes
        @cls.app.upload("/upload", upload_dir=cls.upload_dir)
        def upload_handler(request: Request, files: List[UploadFile]) -> Response:
            result = []
            for file in files:
                result.append({
                    "filename": file.filename,
                    "size": file.size,
                    "content_type": file.content_type,
                    "path": file.path,
                })
            resp = Response(json.dumps(result))
            resp.set_header("Content-Type", "application/json")
            return resp

        @cls.app.upload(
            "/upload-images",
            accepted_mime_types=["image/*"],
            upload_dir=cls.upload_dir
        )
        def upload_images(request: Request, files: List[UploadFile]) -> Response:
            result = []
            for file in files:
                result.append({
                    "filename": file.filename,
                    "size": file.size,
                    "content_type": file.content_type,
                })
            resp = Response(json.dumps(result))
            resp.set_header("Content-Type", "application/json")
            return resp

        @cls.app.upload(
            "/upload-size-limit",
            max_size=1024,  # 1KB limit
            upload_dir=cls.upload_dir
        )
        def upload_size_limit(request: Request, files: List[UploadFile]) -> Response:
            resp = Response(json.dumps({"status": "success"}))
            resp.set_header("Content-Type", "application/json")
            return resp

        # Start server in a daemon thread
        cls.server_thread = threading.Thread(
            target=cls.app.run, kwargs={"host": "127.0.0.1", "port": 8896}, daemon=True
        )
        cls.server_thread.start()

        # Give the server time to start
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        """Clean up upload directory"""
        import shutil
        if os.path.exists(cls.upload_dir):
            shutil.rmtree(cls.upload_dir)

    def test_basic_upload(self):
        """Test basic file upload"""
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = requests.post(f"{self.base_url}/upload", files=files)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['filename'], 'test.txt')
            self.assertEqual(data[0]['content_type'], 'text/plain')
            self.assertEqual(data[0]['size'], 13)  # "Hello, World!" is 13 bytes
        finally:
            os.unlink(temp_path)

    def test_multiple_files_upload(self):
        """Test uploading multiple files"""
        # Create test files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(f"File content {i}")
                temp_files.append(f.name)

        try:
            # Open all files in a try-finally to ensure proper cleanup
            file_handles = []
            try:
                for i, temp_path in enumerate(temp_files):
                    fh = open(temp_path, 'rb')
                    file_handles.append(fh)
                
                files = [(f'file{i}', (f'test{i}.txt', fh, 'text/plain')) 
                         for i, fh in enumerate(file_handles)]
                
                response = requests.post(f"{self.base_url}/upload", files=files)
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(len(data), 3)
            finally:
                # Close all file handles
                for fh in file_handles:
                    fh.close()
        finally:
            for temp_path in temp_files:
                os.unlink(temp_path)

    def test_mime_type_filter_accepted(self):
        """Test that accepted MIME types are allowed"""
        # Create a test image file (just a fake one with image MIME type)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.png') as f:
            f.write("fake image data")
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                files = {'file': ('test.png', f, 'image/png')}
                response = requests.post(f"{self.base_url}/upload-images", files=files)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['content_type'], 'image/png')
        finally:
            os.unlink(temp_path)

    def test_mime_type_filter_rejected(self):
        """Test that non-accepted MIME types are rejected"""
        # Create a text file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("This is a text file")
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = requests.post(f"{self.base_url}/upload-images", files=files)

            # Should be rejected with 400 Bad Request
            self.assertEqual(response.status_code, 400)
            self.assertIn("not accepted", response.text)
        finally:
            os.unlink(temp_path)

    def test_size_limit_accepted(self):
        """Test that files within size limit are accepted"""
        # Create a small file (less than 1KB)
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Small file content")  # ~18 bytes
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                files = {'file': ('small.txt', f, 'text/plain')}
                response = requests.post(f"{self.base_url}/upload-size-limit", files=files)

            self.assertEqual(response.status_code, 200)
        finally:
            os.unlink(temp_path)

    def test_size_limit_rejected(self):
        """Test that files exceeding size limit are rejected"""
        # Create a file larger than 1KB
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("x" * 2000)  # 2KB file
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                files = {'file': ('large.txt', f, 'text/plain')}
                response = requests.post(f"{self.base_url}/upload-size-limit", files=files)

            # Should be rejected with 400 Bad Request
            self.assertEqual(response.status_code, 400)
            self.assertIn("exceeds maximum", response.text)
        finally:
            os.unlink(temp_path)

    def test_uploaded_file_exists(self):
        """Test that uploaded files are actually written to disk"""
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test file content")
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = requests.post(f"{self.base_url}/upload", files=files)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            uploaded_path = data[0]['path']

            # Check that the file exists and has correct content
            self.assertTrue(os.path.exists(uploaded_path))
            with open(uploaded_path, 'r') as f:
                content = f.read()
            self.assertEqual(content, "Test file content")

            # Clean up uploaded file
            os.unlink(uploaded_path)
        finally:
            os.unlink(temp_path)


class TestUploadDecoratorRegistration(unittest.TestCase):
    """Test suite for upload decorator registration functionality"""

    def test_upload_decorator_registration(self):
        """Test @app.upload decorator registration"""
        app = Rupy()

        @app.upload("/test-upload")
        def handler(request: Request, files: List[UploadFile]) -> Response:
            return Response("ok")

        # Just verify the decorator works without errors
        self.assertTrue(True)

    def test_upload_decorator_with_options(self):
        """Test @app.upload decorator with all options"""
        app = Rupy()

        @app.upload(
            "/test-upload",
            accepted_mime_types=["image/*", "application/pdf"],
            max_size=10 * 1024 * 1024,
            upload_dir="/tmp/uploads"
        )
        def handler(request: Request, files: List[UploadFile]) -> Response:
            return Response("ok")

        self.assertTrue(True)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
