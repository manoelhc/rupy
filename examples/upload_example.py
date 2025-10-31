#!/usr/bin/env python3
"""
Example demonstrating file upload functionality in Rupy.

This example shows how to use the @app.upload decorator to handle file uploads
with various options like MIME type filtering and size limits.
"""

from rupy import Rupy, Request, Response, UploadFile
from typing import List
import json

app = Rupy()


@app.get("/")
def index(request: Request) -> Response:
    """Serve a simple HTML form for file upload"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rupy File Upload Example</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .upload-form { border: 2px dashed #ccc; padding: 30px; border-radius: 10px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin-top: 20px; padding: 15px; background: #f0f0f0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Rupy File Upload Example</h1>
        
        <div class="upload-form">
            <h2>Upload Any File</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" multiple required>
                <br><br>
                <button type="submit">Upload</button>
            </form>
        </div>
        
        <div class="upload-form">
            <h2>Upload Images Only</h2>
            <form action="/upload-images" method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept="image/*" multiple required>
                <br><br>
                <button type="submit">Upload Images</button>
            </form>
        </div>
        
        <div class="upload-form">
            <h2>Upload with Size Limit (Max 5MB)</h2>
            <form action="/upload-limited" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <br><br>
                <button type="submit">Upload (Max 5MB)</button>
            </form>
        </div>
    </body>
    </html>
    """
    resp = Response(html)
    resp.set_header("Content-Type", "text/html")
    return resp


@app.upload("/upload", upload_dir="/tmp/rupy-uploads")
def upload_any_file(request: Request, files: List[UploadFile]) -> Response:
    """
    Handle uploads of any file type.
    Files are streamed to disk to avoid memory overflow.
    """
    result = {
        "status": "success",
        "files": []
    }
    
    for file in files:
        file_info = {
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type,
            "path": file.path
        }
        result["files"].append(file_info)
        print(f"Uploaded: {file.filename} ({file.size} bytes) -> {file.path}")
    
    resp = Response(json.dumps(result, indent=2))
    resp.set_header("Content-Type", "application/json")
    return resp


@app.upload(
    "/upload-images",
    accepted_mime_types=["image/*"],  # Only accept images
    upload_dir="/tmp/rupy-uploads"
)
def upload_images(request: Request, files: List[UploadFile]) -> Response:
    """
    Handle uploads of image files only.
    Uses wildcard matching for MIME types (image/*).
    """
    result = {
        "status": "success",
        "files": []
    }
    
    for file in files:
        file_info = {
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type,
            "path": file.path
        }
        result["files"].append(file_info)
        print(f"Image uploaded: {file.filename} ({file.size} bytes)")
    
    resp = Response(json.dumps(result, indent=2))
    resp.set_header("Content-Type", "application/json")
    return resp


@app.upload(
    "/upload-limited",
    max_size=5 * 1024 * 1024,  # 5MB limit
    upload_dir="/tmp/rupy-uploads"
)
def upload_with_limit(request: Request, files: List[UploadFile]) -> Response:
    """
    Handle uploads with a 5MB size limit per file.
    Files exceeding the limit will be rejected.
    """
    result = {
        "status": "success",
        "files": []
    }
    
    for file in files:
        file_info = {
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type,
            "path": file.path
        }
        result["files"].append(file_info)
        print(f"Limited upload: {file.filename} ({file.size} bytes)")
    
    resp = Response(json.dumps(result, indent=2))
    resp.set_header("Content-Type", "application/json")
    return resp


@app.upload(
    "/upload-documents",
    accepted_mime_types=["application/pdf", "application/msword", "text/plain"],
    max_size=10 * 1024 * 1024,  # 10MB limit
    upload_dir="/tmp/rupy-uploads"
)
def upload_documents(request: Request, files: List[UploadFile]) -> Response:
    """
    Handle uploads of specific document types with size limit.
    Only accepts PDF, Word documents, and plain text files.
    """
    result = {
        "status": "success",
        "files": []
    }
    
    for file in files:
        file_info = {
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type,
            "path": file.path
        }
        result["files"].append(file_info)
        print(f"Document uploaded: {file.filename}")
    
    resp = Response(json.dumps(result, indent=2))
    resp.set_header("Content-Type", "application/json")
    return resp


if __name__ == "__main__":
    print("Starting Rupy file upload example server...")
    print("\nEndpoints:")
    print("  - GET  /                     - Upload form")
    print("  - POST /upload               - Upload any file")
    print("  - POST /upload-images        - Upload images only")
    print("  - POST /upload-limited       - Upload with 5MB limit")
    print("  - POST /upload-documents     - Upload documents with 10MB limit")
    print("\nTry uploading files using:")
    print("  curl -F 'file=@myfile.txt' http://127.0.0.1:8000/upload")
    print("  curl -F 'file=@image.png' http://127.0.0.1:8000/upload-images")
    print("\nOr visit http://127.0.0.1:8000/ in your browser")
    print()
    
    app.run(host="127.0.0.1", port=8000)
