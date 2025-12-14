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
import sys
import tempfile

app = Rupy()

port = 8010
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(script_dir, "static")

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
    try:
        # Get files from directory with error handling
        if os.path.exists(static_dir) and os.path.isdir(static_dir):
            files_list = ''.join(f'<li>{f}</li>' for f in os.listdir(static_dir))
        else:
            files_list = f'<li>Error: Directory not found: {static_dir}</li>'
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Rupy Static Files Example</title>
    <link rel="stylesheet" type="text/css" href="/static/css/styles.css">
</head>
<body>
    <h1>Rupy Static Files Example</h1>
    <p>This server demonstrates static file serving.</p>
    
    <h2>Try these static files:</h2>
    <ul>
        <li><a href="/static/css/styles.css">CSS File</a></li>
    </ul>
    
    <h2>Test directory:</h2>
    <p><code>{static_dir}</code></p>
    
    <h2>Files in directory:</h2>
    <ul>
        {files_list}
    </ul>
</body>
</html>
"""
        return Response(html)
    except Exception as e:
        error_msg = f"Error rendering page: {str(e)}"
        print(f"ERROR in index route: {error_msg}", file=sys.stderr)
        return Response(f"<html><body><h1>Error</h1><p>{error_msg}</p></body></html>", status=500)

@app.route("/api/files", methods=["GET"])
def list_files(request: Request) -> Response:
    """API endpoint to list available files"""
    import json
    try:
        if not os.path.exists(static_dir):
            error_response = {"error": f"Directory not found: {static_dir}"}
            print(f"ERROR in /api/files: Directory not found: {static_dir}", file=sys.stderr)
            return Response(json.dumps(error_response), status=404)
        
        files = os.listdir(static_dir)
        return Response(json.dumps({"files": files, "directory": static_dir}))
    except Exception as e:
        error_msg = f"Error listing files: {str(e)}"
        print(f"ERROR in /api/files: {error_msg}", file=sys.stderr)
        error_response = {"error": error_msg}
        return Response(json.dumps(error_response), status=500)


if __name__ == "__main__":
    # Validate that the static directory exists before starting the server
    if not os.path.exists(static_dir):
        print("=" * 70, file=sys.stderr)
        print("ERROR: Static directory not found!", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(f"\nExpected directory: {static_dir}", file=sys.stderr)
        print(f"Script location: {script_dir}", file=sys.stderr)
        print(f"\nPlease ensure the 'static' directory exists at the expected location.", file=sys.stderr)
        print("\nTip: Run this script from its own directory or ensure the path is correct.", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(static_dir):
        print(f"ERROR: {static_dir} exists but is not a directory!", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 70)
    print("Rupy Static File Serving Example")
    print("=" * 70)
    print(f"\nServing files from: {static_dir}")
    print(f"\nStarting server on http://127.0.0.1:{port}")
    print("\nEndpoints:")
    print("  GET  /                    - Main page with links")
    print("  GET  /static/css/styles.css   - Static file serving")
    print("  GET  /api/files           - List available files (JSON)")
    print("\nExample commands:")
    print(f"  curl http://127.0.0.1:{port}/")
    print(f"  curl http://127.0.0.1:{port}/static/css/styles.css")
    print("\n" + "=" * 70)
    
    try:
        app.run(host="127.0.0.1", port=port)
    except KeyboardInterrupt:
        print("\nServer stopped by user")