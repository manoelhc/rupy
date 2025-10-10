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
        methods: List of HTTP methods (currently only "GET" is supported)
    
    Returns:
        Decorator function
    """
    methods = methods or ["GET"]
    
    # Currently only GET is supported
    if "GET" not in methods:
        raise ValueError("Only GET method is currently supported")
    
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
        
        # Call the Rust route method to register
        rupy_instance.route(path, wrapper)
        
        return func
    
    return decorator


# Monkey-patch the route method onto the Rupy class
_original_rupy_route = _RupyBase.route

def _new_route(self, path: str, methods: Optional[List[str]] = None):
    """
    Decorator to register a route handler, or direct route registration.
    
    Can be used as a decorator:
        @app.route("/", methods=["GET"])
        def handler(request):
            return Response("Hello")
    
    Or as a direct call (internal use):
        app.route("/", handler_func)
    """
    # Check if this is being called as a decorator (path is string)
    # or as a direct registration (path is string, second arg is function)
    if callable(methods):
        # Direct registration: route(path, handler)
        # In this case, 'methods' is actually the handler function
        handler = methods
        return _original_rupy_route(self, path, handler)
    else:
        # Decorator usage: route(path, methods=["GET"])
        return _route_decorator(self, path, methods)

_RupyBase.route = _new_route

# Export with the original name
Rupy = _RupyBase

__all__ = ['Rupy', 'Request', 'Response']
