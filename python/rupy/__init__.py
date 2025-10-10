"""
Rupy - A high-performance Python web framework powered by Rust and Axum
"""

try:
    from .rupy_core import Rupy as RustRupy, Request, Response
    
    # Wrap the Rust Rupy to make the decorator work properly
    class Rupy:
        def __init__(self, module_name):
            self._rust_app = RustRupy(module_name)
            self._routes = []
        
        def route(self, path, methods=None):
            if methods is None:
                methods = ["GET"]
            
            def decorator(func):
                # Store the route information
                route_idx = len(self._routes)
                self._routes.append({
                    'path': path,
                    'methods': methods,
                    'handler': func
                })
                
                # Register with Rust backend
                self._rust_app._register_route(path, methods, func)
                return func
            
            return decorator
        
        def run(self, host="0.0.0.0", port=8000):
            self._rust_app.run(host, port)
    
except ImportError:
    # Fallback to pure Python implementation if Rust extension is not available
    from .app import Rupy
    from .request import Request
    from .response import Response

__version__ = "0.1.0"
__all__ = ["Rupy", "Request", "Response"]
