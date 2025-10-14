"""
Rupy - A high-performance web framework for Python, powered by Rust and Axum
"""

from .rupy import Rupy as _RupyBase, PyRequest as Request, PyResponse as Response
from functools import wraps
from typing import Callable, List, Optional


def _route_decorator(rupy_instance, path: str, methods: Optional[List[str]] = None):
    """
    Decorator to register a route handler.
    
    Args:
        rupy_instance: The Rupy instance
        path: The URL path pattern (e.g., "/", "/user/<username>")
        methods: List of HTTP methods (e.g., ["GET", "POST"])
    
    Returns:
        Decorator function
    """
    methods = methods or ["GET"]
    
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

def _new_route(self, path: str, methods: Optional[List[str]] = None):
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
        actual_methods = ["GET"]
        return _original_rupy_route(self, path, handler, actual_methods)
    else:
        # Decorator usage: route(path, methods=["GET"])
        return _route_decorator(self, path, methods)

def _new_middleware(self, handler: Optional[Callable] = None):
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

# Export with the original name
Rupy = _RupyBase

__all__ = ['Rupy', 'Request', 'Response']
