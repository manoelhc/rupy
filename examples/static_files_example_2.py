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

port = 8010
static_dir = "./static"

# Serve static files from the /static path
@app.static("/static", static_dir)
def static_files(response: Response) -> Response:
    """Serve static files from the static directory"""
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
<link rel="stylesheet" type="text/css" href="/static/css/styles.css">
<body>
    <h1>Rupy Static Files Example</h1>
    <p>This server demonstrates static file serving.</p>
    
    <h2>Try these static files:</h2>
    <ul>
        <li><a href="/static/css/styles.css">CSS File</a></li>
    </ul>
    
    <h2>Test directory:</h2>
    <p><code>./static</code></p>
    
    <h2>Files in directory:</h2>
    <ul>
        {''.join(f'<li>{f}</li>' for f in os.listdir(static_dir))}
    </ul>
</body>
</html>
"""
    return Response(html)

@app.route("/api/files", methods=["GET"])
def list_files(request: Request) -> Response:
    """API endpoint to list available files"""
    import json
    files = os.listdir("./static")
    return Response(json.dumps({"files": files, "directory": "./static"}))


if __name__ == "__main__":
    print("=" * 70)
    print("Rupy Static File Serving Example")
    print("=" * 70)
    print(f"\nServing files from: {static_dir}")
    print(f"\nStarting server on http://127.0.0.1:{port}")
    print("\nEndpoints:")
    print("  GET  /                    - Main page with links")
    print("  GET  /static/css/style.css   - Static file serving")
    print("  GET  /api/files           - List available files (JSON)")
    print("\nExample commands:")
    print(f"  curl http://127.0.0.1:{port}/")
    print(f"  curl http://127.0.0.1:{port}/static/css/styles.css")
    print("\n" + "=" * 70)
    
    try:
        app.run(host="127.0.0.1", port=port)
    except KeyboardInterrupt:
        print("\nServer stopped by user")