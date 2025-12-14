# Template Rendering Feature

## Overview

The Rupy framework now supports server-side template rendering using the Handlebars template engine. This feature allows you to create dynamic HTML pages (or any text-based content) by combining templates with data from your Python handlers.

## Installation

Template rendering is built into Rupy - no additional installation required!

## Quick Start

### 1. Create a Template

Create a template file in the `./template` directory (default location):

**template/hello.tpl:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{title}}</title>
</head>
<body>
    <h1>{{greeting}}, {{name}}!</h1>
    <p>{{message}}</p>
</body>
</html>
```

### 2. Use the Template Decorator

```python
from rupy import Rupy, Request

app = Rupy()

@app.template("/", template="hello.tpl")
def index(request: Request) -> dict:
    """Handler returns a dict that becomes the template context."""
    return {
        "title": "Welcome",
        "greeting": "Hello",
        "name": "World",
        "message": "Welcome to Rupy template rendering!"
    }

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
```

### 3. Run and Test

```bash
python your_app.py
curl http://127.0.0.1:8000/
```

## API Reference

### `@app.template(path, template, content_type="text/html")`

Decorator to register a template-based route handler.

**Parameters:**
- `path` (str): URL path pattern (e.g., `"/"`, `"/user/<username>"`)
- `template` (str): Template filename relative to template directory (e.g., `"index.tpl"`)
- `content_type` (str, optional): Response content type. Defaults to `"text/html"`

**Returns:**
The decorated function must return a `dict` that will be used as the template context.

**Example:**
```python
@app.template("/user/<username>", template="user.tpl")
def user_profile(request: Request, username: str) -> dict:
    return {
        "username": username,
        "user_id": 12345
    }
```

### `app.set_template_directory(directory)`

Configure the directory where template files are located.

**Parameters:**
- `directory` (str): Path to template directory

**Default:** `"./template"`

**Example:**
```python
app = Rupy()
app.set_template_directory("./templates")
```

### `app.get_template_directory()`

Get the current template directory path.

**Returns:**
- `str`: Current template directory path

**Example:**
```python
current_dir = app.get_template_directory()
print(f"Templates are in: {current_dir}")
```

## Template Syntax

Rupy uses the Handlebars template engine. Here are some common patterns:

### Variables
```handlebars
<h1>{{title}}</h1>
<p>Hello, {{name}}!</p>
```

### Escaping HTML
Variables are HTML-escaped by default:
```handlebars
<p>{{user_input}}</p>  <!-- Safe from XSS -->
```

## Advanced Features

### Dynamic Route Parameters

Template routes support dynamic parameters just like regular routes:

```python
@app.template("/post/<post_id>", template="post.tpl")
def show_post(request: Request, post_id: str) -> dict:
    return {
        "post_id": post_id,
        "title": f"Post {post_id}",
        "content": "Post content here..."
    }
```

### Custom Content Types

You can use templates for any text-based format:

```python
@app.template("/api/data", template="data.json", content_type="application/json")
def json_template(request: Request) -> dict:
    return {
        "status": "success",
        "count": 42
    }
```

**template/data.json:**
```json
{
  "status": "{{status}}",
  "count": {{count}},
  "timestamp": "{{timestamp}}"
}
```

### Custom Template Directory

```python
app = Rupy()
app.set_template_directory("./my_templates")

@app.template("/", template="home.tpl")
def home(request: Request) -> dict:
    return {"message": "Hello"}
```

### Multiple Template Directories

You can configure multiple template directories for flexible template lookup. Templates are searched in the order directories were added:

```python
app = Rupy()
app.set_template_directory("./templates")      # Primary directory
app.add_template_directory("./shared_templates")  # Fallback directory
app.add_template_directory("./common_templates")  # Second fallback

# Get all configured directories
dirs = app.get_template_directories()
print(f"Template directories: {dirs}")

# Remove a directory if needed
app.remove_template_directory("./common_templates")
```

**How it works:**
- When rendering a template, Rupy searches each directory in order
- The first matching template file is used
- This allows for template override patterns and shared template libraries

## Template Class for Programmatic Rendering

The `Template` class allows you to render templates programmatically without creating a route. This is useful for generating emails, reports, or other dynamic content:

```python
from rupy import Rupy, Template

app = Rupy()
app.set_template_directory("./templates")

# Create a template instance
email_template = Template(app, "email.tpl")

# Render with context data
def send_welcome_email(user_email: str, user_name: str):
    rendered = email_template.render({
        "email": user_email,
        "name": user_name,
        "subject": "Welcome!",
        "message": "Thanks for signing up!"
    })
    # Send the rendered email...
    return rendered
```

**Template Class API:**

- `Template(app, template_name)` - Create a template instance
  - `app`: Rupy application instance
  - `template_name`: Template filename (e.g., "email.tpl")

- `template.render(context)` - Render the template
  - `context`: Dictionary with template variables
  - Returns: Rendered string

**Example Use Cases:**

1. **Email Generation**: Render email templates dynamically
2. **Report Generation**: Create PDF or text reports
3. **Data Export**: Generate CSV, JSON, or XML from templates
4. **Batch Processing**: Render multiple templates in a loop

```python
from rupy import Rupy, Request, Template

app = Rupy()

@app.get("/send-report")
def send_report(request: Request) -> str:
    # Render report template programmatically
    report = Template(app, "report.tpl")
    rendered = report.render({
        "title": "Monthly Report",
        "data": "Sales: $10,000"
    })
    
    # Could send via email, save to file, etc.
    return rendered
```

## Error Handling

### Missing Template File

If a template file doesn't exist, Rupy returns a 500 error with details:

```
Template rendering error: Failed to read template file './template/missing.tpl': No such file or directory
```

### Invalid Template Syntax

If a template has invalid Handlebars syntax, you'll get a parse error:

```
Template rendering error: Failed to parse template: ...
```

### Wrong Return Type

Template handlers must return a dict:

```python
@app.template("/bad", template="test.tpl")
def bad_handler(request: Request) -> str:
    return "This will error!"  # Must return dict!
```

Error: `Template handler must return a dict`

## Best Practices

1. **Organize Templates**: Keep templates in a dedicated directory
2. **Consistent Naming**: Use `.tpl` or `.html` extension for templates
3. **Return Type**: Always return a dict from template handlers
4. **Variable Names**: Use clear, descriptive variable names in both Python and templates
5. **Content Type**: Set appropriate content type for non-HTML templates
6. **Multiple Directories**: Use primary directory for app-specific templates and fallback directories for shared templates
7. **Template Class**: Use `Template` class for programmatic rendering (emails, reports, etc.)

## Examples

- `examples/template_example.py` - Basic template decorator usage
- `examples/template_class_example.py` - Template class and multiple directories

## Security Considerations

- **XSS Protection**: Handlebars automatically escapes HTML by default
- **Path Traversal**: Template directory is set at application level, not from user input
- **File Access**: Only files within the configured template directory can be accessed

## Troubleshooting

### Template not found
- Verify template file exists in one of the configured directories
- Check file name and extension match exactly
- Use `app.get_template_directories()` to see all search paths
- Templates are searched in the order directories were added

### Variables not appearing
- Ensure variable names in template match dict keys exactly
- Check for typos in variable names
- Verify handler is returning the dict correctly

### Content type issues
- Specify `content_type` parameter if not using HTML
- Ensure template syntax matches the content type (e.g., valid JSON for JSON templates)

### Multiple directories priority
- First directory has highest priority
- Use `app.get_template_directories()` to check search order
- Templates in earlier directories override those in later ones
