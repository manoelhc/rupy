#!/usr/bin/env python3
"""
Example demonstrating static file serving in Rupy.

This example shows how to:
1. Serve static files from a directory
2. Handle different file types
3. Prevent directory traversal attacks
"""

from rupy import Rupy, Request, Response
import os
import tempfile

app = Rupy()


# Create a temporary directory with some test files
# In production, you would serve from a real directory like "./static" or "./public"
test_dir = tempfile.mkdtemp()

# Create some test files
with open(os.path.join(test_dir, "index.html"), "w") as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Static Files Demo</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <h1>Welcome to Rupy Static Files</h1>
    <p>This page is served as a static file.</p>
    <script src="/static/app.js"></script>
</body>
</html>
""")

with open(os.path.join(test_dir, "style.css"), "w") as f:
    f.write("""body {
    font-family: Arial, sans-serif;
    margin: 40px;
    background-color: #f0f0f0;
}

h1 {
    color: #333;
}
""")

with open(os.path.join(test_dir, "app.js"), "w") as f:
    f.write("""console.log('Static JavaScript file loaded!');
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded via Rupy static file serving');
});
""")

with open(os.path.join(test_dir, "data.json"), "w") as f:
    f.write("""{
    "message": "This is a static JSON file",
    "served_by": "Rupy"
}
""")


# Serve static files from the /static path
@app.static("/static", test_dir)
def static_files(response: Response) -> Response:
    """Serve static files from the test directory"""
    # You can modify the response here if needed
    # For example, add custom headers
    response.set_header("X-Served-By", "Rupy Static Handler")
    return response


@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    """Main page with links to static files"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Rupy Static Files Example</title>
</head>
<body>
    <h1>Rupy Static Files Example</h1>
    <p>This server demonstrates static file serving.</p>
    
    <h2>Try these static files:</h2>
    <ul>
        <li><a href="/static/index.html">HTML Page</a></li>
        <li><a href="/static/style.css">CSS File</a></li>
        <li><a href="/static/app.js">JavaScript File</a></li>
        <li><a href="/static/data.json">JSON File</a></li>
    </ul>
    
    <h2>Test directory:</h2>
    <p><code>{test_dir}</code></p>
    
    <h2>Files in directory:</h2>
    <ul>
        {''.join(f'<li>{f}</li>' for f in os.listdir(test_dir))}
    </ul>
</body>
</html>
"""
    return Response(html)


@app.route("/api/files", methods=["GET"])
def list_files(request: Request) -> Response:
    """API endpoint to list available files"""
    import json
    files = os.listdir(test_dir)
    return Response(json.dumps({"files": files, "directory": test_dir}))


if __name__ == "__main__":
    print("=" * 70)
    print("Rupy Static File Serving Example")
    print("=" * 70)
    print(f"\nServing files from: {test_dir}")
    print("\nStarting server on http://127.0.0.1:8000")
    print("\nEndpoints:")
    print("  GET  /                    - Main page with links")
    print("  GET  /static/<filepath>   - Static file serving")
    print("  GET  /api/files           - List available files (JSON)")
    print("\nExample commands:")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/static/index.html")
    print("  curl http://127.0.0.1:8000/static/data.json")
    print("  curl http://127.0.0.1:8000/api/files")
    print("\n" + "=" * 70)
    
    try:
        app.run(host="127.0.0.1", port=8009)
    finally:
        # Clean up temp directory
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
