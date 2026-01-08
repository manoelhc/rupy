"""
Rupy - A high-performance web framework for Python, powered by Rust and Axum
"""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import List
from typing import Optional

from .rupy import PyRequest as Request
from .rupy import PyResponse as Response
from .rupy import PyUploadFile as UploadFile
from .rupy import Rupy as _RupyBase


def _route_decorator(rupy_instance, path: str, methods: list[str] | None = None):
    """
    Decorator to register a route handler.

    Args:
        rupy_instance: The Rupy instance
        path: The URL path pattern (e.g., "/", "/user/<username>")
        methods: List of HTTP methods (e.g., ["GET", "POST"])

    Returns:
        Decorator function
    """
    methods = methods or ['GET']

    def decorator(func: Callable):
        # Register the route with the Rust backend
        # We need to wrap the function to ensure it can be called properly
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # If the result is a string, wrap it in a Response
            if isinstance(result, str):
                return Response(result)
            return result

        # Call the original Rust route method to register with methods
        _original_rupy_route(rupy_instance, path, wrapper, methods)

        return func

    return decorator


def _middleware_decorator(rupy_instance):
    """
    Decorator to register a middleware handler.

    Args:
        rupy_instance: The Rupy instance

    Returns:
        Decorator function
    """

    def decorator(func: Callable):
        # Register the middleware with the Rust backend
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Middleware can return:
            # - None or Request: continue to next middleware/handler
            # - Response: stop processing and return response
            if result is None:
                # Return the request to continue processing
                return args[0] if args else None
            return result

        # Call the Rust middleware method to register
        _original_rupy_middleware(rupy_instance, wrapper)

        return func

    return decorator


# Monkey-patch the route method onto the Rupy class
_original_rupy_route = _RupyBase.route
_original_rupy_middleware = _RupyBase.middleware


def _new_route(self, path: str, methods: list[str] | None = None):
    """
    Decorator to register a route handler, or direct route registration.

    Can be used as a decorator:
        @app.route("/", methods=["GET"])
        def handler(request):
            return Response("Hello")

    Or as a direct call (internal use):
        app.route("/", handler_func, ["GET"])
    """
    # Check if this is being called as a decorator (path is string)
    # or as a direct registration (path is string, second arg is function)
    if callable(methods):
        # Direct registration: route(path, handler)
        # In this case, 'methods' is actually the handler function
        handler = methods
        # Default to GET method if not specified
        actual_methods = ['GET']
        return _original_rupy_route(self, path, handler, actual_methods)
    else:
        # Decorator usage: route(path, methods=["GET"])
        return _route_decorator(self, path, methods)


def _new_middleware(self, handler: Callable | None = None):
    """
    Decorator to register a middleware handler.

    Can be used as a decorator:
        @app.middleware
        def my_middleware(request):
            # Process request
            return request  # or Response to stop processing

    Or as a direct call:
        app.middleware(my_middleware_func)
    """
    if handler is not None and callable(handler):
        # Direct registration
        return _original_rupy_middleware(self, handler)
    else:
        # Decorator usage
        return _middleware_decorator(self)


_RupyBase.route = _new_route
_RupyBase.middleware = _new_middleware


# Add method-specific decorators
def _create_method_decorator(method: str):
    """
    Creates a method-specific decorator (e.g., get, post, put, etc.)

    Args:
        method: HTTP method name (e.g., "GET", "POST")

    Returns:
        Method decorator function
    """

    def method_decorator(self, path: str):
        """
        Decorator to register a route handler for a specific HTTP method.

        Args:
            path: The URL path pattern (e.g., "/", "/user/<username>")

        Returns:
            Decorator function
        """
        return _route_decorator(self, path, [method])

    return method_decorator


# Add method-specific decorators to the Rupy class
_RupyBase.get = _create_method_decorator('GET')
_RupyBase.post = _create_method_decorator('POST')
_RupyBase.put = _create_method_decorator('PUT')
_RupyBase.patch = _create_method_decorator('PATCH')
_RupyBase.delete = _create_method_decorator('DELETE')
_RupyBase.head = _create_method_decorator('HEAD')
_RupyBase.options = _create_method_decorator('OPTIONS')


# Add static file serving decorator
def _static_decorator(self, url_path: str, directory: str):
    """
    Decorator to serve static files from a directory.

    The decorated function receives a Response object with the file content
    and can modify it before returning.

    Args:
        url_path: URL path prefix (e.g., "/static")
        directory: Local directory path to serve files from

    Example:
        @app.static("/static", "./public")
        def static_files(response: Response) -> Response:
            # Optionally modify the response (add headers, etc.)
            response.set_header("Cache-Control", "max-age=3600")
            return response
    """
    import os
    import sys

    def decorator(func: Callable):
        # Validate directory exists when decorator is applied
        if not os.path.exists(directory):
            print(
                f"WARNING: Static directory does not exist: {directory}", file=sys.stderr)
            print(
                f"         Static file serving for '{url_path}' may not work correctly.", file=sys.stderr)
        elif not os.path.isdir(directory):
            print(
                f"WARNING: Path exists but is not a directory: {directory}", file=sys.stderr)
            print(
                f"         Static file serving for '{url_path}' may not work correctly.", file=sys.stderr)

        # Create a handler that serves files from the directory
        @wraps(func)
        def static_handler(request: Request, filepath: str = '') -> Response:
            # Build the full file path
            full_path = os.path.join(directory, filepath)

            # Security check: prevent directory traversal
            try:
                real_directory = os.path.realpath(directory)
                real_path = os.path.realpath(full_path)
            except Exception as e:
                error_msg = f"Error resolving path: {str(e)}"
                print(f"ERROR in static handler: {error_msg}", file=sys.stderr)
                resp = Response(error_msg, status=500)
                return func(resp)

            if not real_path.startswith(real_directory):
                print(
                    f"SECURITY: Directory traversal attempt blocked: {filepath}", file=sys.stderr)
                resp = Response('Forbidden', status=403)
                return func(resp)

            # Check if directory exists
            if not os.path.exists(real_directory):
                error_msg = f"Static directory not found: {directory}"
                print(f"ERROR in static handler: {error_msg}", file=sys.stderr)
                resp = Response(error_msg, status=500)
                return func(resp)

            # Check if file exists and is a file (not directory)
            if not os.path.exists(real_path):
                print(
                    f"File not found: {filepath} (resolved to: {real_path})", file=sys.stderr)
                resp = Response('Not Found', status=404)
                return func(resp)

            if not os.path.isfile(real_path):
                print(
                    f"Path is not a file: {filepath} (resolved to: {real_path})", file=sys.stderr)
                resp = Response('Not Found', status=404)
                return func(resp)

            # Read and return the file
            try:
                with open(real_path, 'rb') as f:
                    content = f.read()

                # Determine content type based on file extension
                content_type = _get_content_type(real_path)

                resp = Response(content.decode('utf-8', errors='replace'))
                resp.set_header('Content-Type', content_type)

                # Call the user function with the response
                return func(resp)
            except Exception as e:
                error_msg = f"Error reading file: {str(e)}"
                print(f"ERROR in static handler: {error_msg}", file=sys.stderr)
                resp = Response(error_msg, status=500)
                return func(resp)

        # Register the route with a wildcard pattern
        route_pattern = f"{url_path}/<filepath:path>"
        _original_rupy_route(self, route_pattern, static_handler, ['GET'])

        return func

    return decorator


def _get_content_type(filepath: str) -> str:
    """Get content type based on file extension"""
    import mimetypes
    content_type, _ = mimetypes.guess_type(filepath)
    return content_type or 'application/octet-stream'


_RupyBase.static = _static_decorator


# Add reverse proxy decorator
def _proxy_decorator(self, url_path: str, target_url: str):
    """
    Decorator to reverse proxy requests to another server.

    The decorated function receives a Response object with the proxied content
    and can modify it before returning.

    Args:
        url_path: URL path prefix to proxy (e.g., "/api")
        target_url: Target server URL (e.g., "http://backend:8080")

    Example:
        @app.proxy("/api", "http://backend:8080")
        def api_proxy(response: Response) -> Response:
            # Optionally modify the response (add headers, filter content, etc.)
            response.set_header("X-Proxied-By", "Rupy")
            return response
    """
    def decorator(func: Callable):
        import urllib.request
        import urllib.error

        @wraps(func)
        def proxy_handler(request: Request, path: str = '') -> Response:
            # Build the target URL
            target = f"{target_url.rstrip('/')}/{path.lstrip('/')}"

            try:
                # Create the proxied request
                headers_dict = {}
                for key, value in request.headers.items():
                    # Skip hop-by-hop headers
                    if key.lower() not in ['host', 'connection', 'transfer-encoding']:
                        headers_dict[key] = value

                # Make the request to the target
                req = urllib.request.Request(
                    target,
                    data=request.body.encode(
                        'utf-8') if request.body else None,
                    headers=headers_dict,
                    method=request.method,
                )

                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                    status = response.status

                    # Create response
                    resp = Response(content, status=status)

                    # Copy response headers
                    for key, value in response.headers.items():
                        if key.lower() not in ['connection', 'transfer-encoding']:
                            resp.set_header(key, value)

                    # Call the user function with the response
                    return func(resp)

            except urllib.error.HTTPError as e:
                resp = Response(e.read().decode('utf-8'), status=e.code)
                return func(resp)
            except urllib.error.URLError as e:
                resp = Response(f"Proxy error: {str(e)}", status=502)
                return func(resp)
            except Exception as e:
                resp = Response(f"Proxy error: {str(e)}", status=500)
                return func(resp)

        # Register the route with a wildcard pattern
        route_pattern = f"{url_path}/<path>"
        _original_rupy_route(self, route_pattern, proxy_handler, [
                             'GET', 'POST', 'PUT', 'PATCH', 'DELETE'])

        return func

    return decorator


_RupyBase.proxy = _proxy_decorator


# Add OpenAPI/Swagger support
_openapi_configs = {}  # Store configs per app instance


def _enable_openapi(
    self,
    path: str = '/openapi.json',
    title: str = 'API Documentation',
    version: str = '1.0.0',
    description: str = '',
):
    """
    Enable OpenAPI/Swagger JSON endpoint.

    Args:
        path: URL path for the OpenAPI JSON endpoint (default: "/openapi.json")
        title: API title
        version: API version
        description: API description
    """
    # Store config using object id as key
    _openapi_configs[id(self)] = {
        'enabled': True,
        'path': path,
        'title': title,
        'version': version,
        'description': description,
    }

    # Register the OpenAPI endpoint
    @self.route(path, methods=['GET'])
    def openapi_spec(request: Request) -> Response:
        import json
        spec = _generate_openapi_spec(self, title, version, description)
        resp = Response(json.dumps(spec, indent=2))
        resp.set_header('Content-Type', 'application/json')
        return resp


def _disable_openapi(self):
    """Disable OpenAPI/Swagger JSON endpoint."""
    config_id = id(self)
    if config_id in _openapi_configs:
        _openapi_configs[config_id]['enabled'] = False


def _generate_openapi_spec(app, title: str, version: str, description: str) -> dict:
    """Generate OpenAPI 3.0 specification from registered routes."""
    # This is a basic implementation - can be extended
    spec = {
        'openapi': '3.0.0',
        'info': {
            'title': title,
            'version': version,
            'description': description,
        },
        'paths': {},
    }

    # Try to extract route information if available
    # For now, return a basic spec
    # In a full implementation, we would introspect registered routes

    return spec


_RupyBase.enable_openapi = _enable_openapi
_RupyBase.disable_openapi = _disable_openapi


# Add template decorator
def _template_decorator(
    self,
    path: str,
    template: str,
    content_type: str = 'text/html',
):
    """
    Decorator to register a template route handler.

    The decorated function should return a dictionary that will be used
    as the context for rendering the template using Handlebars.

    Args:
        path: URL path pattern (e.g., "/", "/user/<username>")
        template: Template filename (e.g., "index.tpl")
        content_type: Response content type (default: "text/html")

    Example:
        @app.template("/hello", template="hello.tpl")
        def hello_page(request: Request) -> dict:
            return {"name": "World", "greeting": "Hello"}
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Call the handler function which should return a dict
            result = func(*args, **kwargs)
            # Ensure result is a dict
            if not isinstance(result, dict):
                raise TypeError(
                    f"Template handler must return a dict, got {type(result)}")
            return result

        # Register the template route with the Rust backend
        # Use the internal route_template method
        _RupyBase.route_template(
            self,
            path,
            wrapper,
            ['GET'],  # Default to GET for template routes
            template,
            content_type,
        )

        return func

    return decorator


_RupyBase.template = _template_decorator


# Add method to set template directory
def _set_template_directory(self, directory: str):
    """
    Set the directory where template files are located.

    Args:
        directory: Path to the template directory (default: "./template")

    Example:
        app.set_template_directory("./templates")
    """
    _RupyBase.set_template_dir(self, directory)


_RupyBase.set_template_directory = _set_template_directory


def _get_template_directory(self) -> str:
    """
    Get the directory where template files are located.

    Returns:
        str: Path to the template directory

    Example:
        template_dir = app.get_template_directory()
    """
    return _RupyBase.get_template_dir(self)


_RupyBase.get_template_directory = _get_template_directory


def _add_template_directory(self, directory: str):
    """
    Add a directory to the template search path.

    Templates will be searched in the order directories were added.

    Args:
        directory: Path to add to template search path

    Example:
        app.add_template_directory("./templates")
        app.add_template_directory("./shared_templates")
    """
    _RupyBase.add_template_dir(self, directory)


_RupyBase.add_template_directory = _add_template_directory


def _remove_template_directory(self, directory: str):
    """
    Remove a directory from the template search path.

    Args:
        directory: Path to remove from template search path

    Example:
        app.remove_template_directory("./templates")
    """
    _RupyBase.remove_template_dir(self, directory)


_RupyBase.remove_template_directory = _remove_template_directory


def _get_template_directories(self) -> list[str]:
    """
    Get all template directories in the search path.

    Returns:
        List[str]: List of template directory paths

    Example:
        dirs = app.get_template_directories()
        print(f"Template directories: {dirs}")
    """
    return _RupyBase.get_template_dirs(self)


_RupyBase.get_template_directories = _get_template_directories


# Add upload decorator
def _upload_decorator(
    self,
    path: str,
    accepted_mime_types: list[str] | None = None,
    max_size: int | None = None,
    upload_dir: str | None = None,
):
    """
    Decorator to register a file upload handler.

    The decorated function receives a Request object and a list of UploadFile objects.
    Files are streamed to disk to avoid memory overflow.

    Args:
        path: URL path pattern (e.g., "/upload")
        accepted_mime_types: List of accepted MIME types (e.g., ["image/*", "application/pdf"])
                           Empty list or None means all types accepted
        max_size: Maximum file size in bytes (None means no limit)
        upload_dir: Directory to store uploaded files (default: "/tmp")

    Example:
        @app.upload("/upload", accepted_mime_types=["image/*"], max_size=10*1024*1024)
        def handle_upload(request: Request, files: List[UploadFile]) -> Response:
            for file in files:
                print(f"Uploaded: {file.filename} ({file.size} bytes)")
                print(f"Stored at: {file.path}")
                print(f"MIME type: {file.content_type}")
            return Response("Files uploaded successfully")
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # If the result is a string, wrap it in a Response
            if isinstance(result, str):
                return Response(result)
            return result

        # Register the upload route with the Rust backend
        _RupyBase.route_upload(
            self,
            path,
            wrapper,
            ['POST'],  # Upload routes typically use POST
            accepted_mime_types,
            max_size,
            upload_dir,
        )

        return func

    return decorator


_RupyBase.upload = _upload_decorator


# Template class for standalone template rendering
class Template:
    """
    A class for loading and rendering templates independently of routes.

    This allows you to render templates programmatically with context data,
    useful for generating emails, reports, or other dynamic content.

    Example:
        template = Template(app, "email.tpl")
        rendered = template.render({"name": "John", "subject": "Welcome"})
    """

    def __init__(self, app: _RupyBase, template_name: str):
        """
        Initialize a Template instance.

        Args:
            app: The Rupy application instance (used to access template directories)
            template_name: Name of the template file (e.g., "email.tpl")
        """
        self._app = app
        self._template_name = template_name

    def render(self, context: dict) -> str:
        """
        Render the template with the given context data.

        Args:
            context: Dictionary containing template variables

        Returns:
            str: The rendered template as a string

        Raises:
            RuntimeError: If template cannot be found or rendered

        Example:
            template = Template(app, "greeting.tpl")
            html = template.render({"name": "Alice", "greeting": "Hello"})
        """
        if not isinstance(context, dict):
            raise TypeError(
                f"Context must be a dict, got {type(context).__name__}")

        # Use the Rust backend to render the template
        return _RupyBase.render_template_string(self._app, self._template_name, context)

    @property
    def template_name(self) -> str:
        """Get the template name."""
        return self._template_name


# Export with the original name
Rupy = _RupyBase

__all__ = ['Rupy', 'Request', 'Response', 'UploadFile', 'Template']
