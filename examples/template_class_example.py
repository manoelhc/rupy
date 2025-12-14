#!/usr/bin/env python3
"""
Example demonstrating the Template class and multiple template directories.

This example shows how to:
1. Use the Template class to render templates programmatically
2. Set up multiple template directories
3. Use template lookup with fallback directories
"""

from rupy import Rupy, Request, Template
import os
import tempfile
import shutil

app = Rupy()

# Create temporary directories for demonstration
temp_dir1 = tempfile.mkdtemp(prefix="templates1_")
temp_dir2 = tempfile.mkdtemp(prefix="templates2_")

# Create templates in first directory (primary templates)
with open(os.path.join(temp_dir1, "greeting.tpl"), "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head><title>Greeting</title></head>
<body>
    <h1>{{greeting}}, {{name}}!</h1>
    <p>This template is from the primary directory.</p>
</body>
</html>
""")

with open(os.path.join(temp_dir1, "user.tpl"), "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head><title>User Profile</title></head>
<body>
    <h1>User Profile</h1>
    <p>Username: {{username}}</p>
    <p>ID: {{user_id}}</p>
</body>
</html>
""")

# Create templates in second directory (shared/fallback templates)
with open(os.path.join(temp_dir2, "email.tpl"), "w") as f:
    f.write("""
To: {{email}}
Subject: {{subject}}

Dear {{name}},

{{message}}

Best regards,
{{sender}}
""")

with open(os.path.join(temp_dir2, "report.tpl"), "w") as f:
    f.write("""
Report Title: {{title}}
Generated: {{date}}
---
{{content}}
""")

# Configure multiple template directories
app.set_template_directory(temp_dir1)  # Primary directory
app.add_template_directory(temp_dir2)   # Fallback directory

print(f"Template directories configured:")
for i, dir_path in enumerate(app.get_template_directories(), 1):
    print(f"  {i}. {dir_path}")


# Example 1: Using @app.template decorator (existing functionality)
@app.template("/", template="greeting.tpl")
def index(request: Request) -> dict:
    """Route-based template rendering."""
    return {
        "greeting": "Hello",
        "name": "World"
    }


@app.template("/user/<username>", template="user.tpl")
def user_profile(request: Request, username: str) -> dict:
    """Dynamic route with template."""
    return {
        "username": username,
        "user_id": 12345
    }


# Example 2: Using Template class for programmatic rendering
@app.get("/generate-email")
def generate_email(request: Request) -> str:
    """Programmatically render a template (not from a route)."""
    # Create Template instance
    email_template = Template(app, "email.tpl")
    
    # Render with context
    rendered = email_template.render({
        "email": "user@example.com",
        "subject": "Welcome to Rupy!",
        "name": "John Doe",
        "message": "Thanks for trying out the Template class feature!",
        "sender": "The Rupy Team"
    })
    
    return f"<pre>{rendered}</pre>"


@app.get("/generate-report")
def generate_report(request: Request) -> str:
    """Generate a report using Template class."""
    from datetime import datetime
    
    # Create template from second directory
    report_template = Template(app, "report.tpl")
    
    rendered = report_template.render({
        "title": "Monthly Report",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "content": "Sales increased by 25%\nCustomer satisfaction: 95%"
    })
    
    return f"<pre>{rendered}</pre>"


# Example 3: Template lookup from multiple directories
@app.get("/template-info")
def template_info(request: Request) -> str:
    """Show information about template directories."""
    dirs = app.get_template_directories()
    
    html = "<html><body>"
    html += "<h1>Template Directory Configuration</h1>"
    html += "<h2>Configured Directories:</h2><ol>"
    
    for dir_path in dirs:
        html += f"<li>{dir_path}</li>"
    
    html += "</ol>"
    
    html += "<h2>Available Templates:</h2><ul>"
    html += "<li>greeting.tpl (from primary directory)</li>"
    html += "<li>user.tpl (from primary directory)</li>"
    html += "<li>email.tpl (from fallback directory)</li>"
    html += "<li>report.tpl (from fallback directory)</li>"
    html += "</ul>"
    
    html += "<h2>Try These URLs:</h2><ul>"
    html += "<li><a href='/'>/ - Route-based template</a></li>"
    html += "<li><a href='/user/alice'>/user/alice - Dynamic route template</a></li>"
    html += "<li><a href='/generate-email'>/generate-email - Programmatic email template</a></li>"
    html += "<li><a href='/generate-report'>/generate-report - Programmatic report template</a></li>"
    html += "</ul></body></html>"
    
    return html


# Cleanup function (for demonstration purposes)
def cleanup():
    """Clean up temporary directories."""
    shutil.rmtree(temp_dir1, ignore_errors=True)
    shutil.rmtree(temp_dir2, ignore_errors=True)
    print("\nCleaned up temporary directories.")


if __name__ == "__main__":
    import atexit
    atexit.register(cleanup)
    
    print("\nStarting Template Class Example on http://127.0.0.1:8000")
    print("\nFeatures demonstrated:")
    print("  1. Template class for programmatic rendering")
    print("  2. Multiple template directories with lookup")
    print("  3. Template fallback from secondary directories")
    print("\nExample routes:")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/user/alice")
    print("  curl http://127.0.0.1:8000/generate-email")
    print("  curl http://127.0.0.1:8000/generate-report")
    print("  curl http://127.0.0.1:8000/template-info")
    print("\nPress Ctrl+C to stop")
    
    try:
        app.run(host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
