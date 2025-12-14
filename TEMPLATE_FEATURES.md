# New Template Features

This document provides a quick reference for the two new template features added to Rupy.

## 1. Template Class

The `Template` class allows you to render templates programmatically without creating a route.

### Basic Usage

```python
from rupy import Rupy, Template

app = Rupy()
app.set_template_directory("./templates")

# Create a template instance
template = Template(app, "email.tpl")

# Render with context data
result = template.render({
    "name": "Alice",
    "subject": "Welcome",
    "message": "Thanks for signing up!"
})

print(result)
```

### Use Cases

- **Email Generation**: Render email templates dynamically
- **Report Generation**: Create PDF or text reports
- **Data Export**: Generate CSV, JSON, or XML from templates
- **Batch Processing**: Render multiple templates in a loop

### Example: Email Generator

```python
from rupy import Rupy, Request, Template

app = Rupy()

@app.post("/send-welcome-email")
def send_email(request: Request) -> str:
    # Get user data from request
    user_data = request.body  # Parse JSON
    
    # Render email template
    email_template = Template(app, "welcome_email.tpl")
    email_body = email_template.render({
        "name": user_data["name"],
        "email": user_data["email"],
        "verification_link": f"https://example.com/verify/{user_data['token']}"
    })
    
    # Send email (pseudo-code)
    # send_email_service(user_data["email"], email_body)
    
    return "Email sent!"
```

## 2. Multiple Template Directories

Configure multiple template directories for flexible template lookup.

### Basic Usage

```python
from rupy import Rupy

app = Rupy()

# Set primary directory
app.set_template_directory("./templates")

# Add fallback directories
app.add_template_directory("./shared_templates")
app.add_template_directory("./common_templates")

# Get all configured directories
dirs = app.get_template_directories()
print(f"Template directories: {dirs}")
# Output: ['./templates', './shared_templates', './common_templates']

# Remove a directory if needed
app.remove_template_directory("./common_templates")
```

### How It Works

- Templates are searched in the order directories were added
- The first matching template file is used
- This enables template override patterns and shared libraries

### Example: App-Specific and Shared Templates

```python
from rupy import Rupy, Request

app = Rupy()

# Configure directories
app.set_template_directory("./my_app/templates")    # App-specific templates
app.add_template_directory("./shared/templates")     # Shared templates

# If "header.tpl" exists in both directories,
# the one in "./my_app/templates" will be used

@app.template("/page", template="header.tpl")
def page(request: Request) -> dict:
    return {"title": "My Page"}

# If "footer.tpl" only exists in "./shared/templates",
# it will be found and used

@app.template("/page2", template="footer.tpl")
def page2(request: Request) -> dict:
    return {"copyright": "2024"}
```

### Example: Theme Override System

```python
from rupy import Rupy

app = Rupy()

# Set up theme override system
user_theme = "dark"  # Could come from user preferences

if user_theme == "dark":
    app.set_template_directory("./themes/dark")
    app.add_template_directory("./themes/default")  # Fallback
elif user_theme == "light":
    app.set_template_directory("./themes/light")
    app.add_template_directory("./themes/default")
else:
    app.set_template_directory("./themes/default")

# Now templates will be loaded from the user's theme first,
# falling back to default theme if not found
```

## API Reference

### Template Class

**Constructor:**
```python
Template(app: Rupy, template_name: str)
```
- `app`: Rupy application instance
- `template_name`: Template filename (e.g., "email.tpl")

**Methods:**
```python
template.render(context: dict) -> str
```
- `context`: Dictionary with template variables
- Returns: Rendered template as string
- Raises: `TypeError` if context is not a dict, `RuntimeError` if template not found

**Properties:**
```python
template.template_name -> str
```
- Returns: The template filename

### Multiple Directories Methods

**Set Primary Directory:**
```python
app.set_template_directory(directory: str)
```
- Sets the template directory and clears the list
- Replaces any previously configured directories

**Add Directory:**
```python
app.add_template_directory(directory: str)
```
- Adds a directory to the search path
- Directories are searched in order
- Duplicate directories are ignored

**Remove Directory:**
```python
app.remove_template_directory(directory: str)
```
- Removes a directory from the search path

**Get Directories:**
```python
app.get_template_directories() -> List[str]
```
- Returns: List of all configured template directories

**Get Primary Directory (backward compatibility):**
```python
app.get_template_directory() -> str
```
- Returns: The first directory in the list

## Examples

See these example files for complete working code:
- `examples/template_example.py` - Basic template decorator usage
- `examples/template_class_example.py` - Template class and multiple directories

## Testing

Run the tests to see all features in action:
```bash
python -m unittest tests.test_template -v
python -m unittest tests.test_template_class -v
```

## Documentation

For more detailed documentation, see:
- `TEMPLATE_DOCUMENTATION.md` - Complete template rendering documentation
- `README.md` - Updated feature list
