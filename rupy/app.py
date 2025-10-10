"""
Main Rupy application class
"""
import re
import asyncio
from typing import Callable, Dict, List, Optional, Tuple, Any
from aiohttp import web
from .request import Request
from .response import Response


class Route:
    """Represents a route with path pattern and handler"""
    
    def __init__(self, path: str, handler: Callable, methods: List[str]):
        self.path = path
        self.handler = handler
        self.methods = [m.upper() for m in methods]
        self.pattern, self.param_names = self._compile_path(path)
    
    def _compile_path(self, path: str) -> Tuple[re.Pattern, List[str]]:
        """Compile path pattern with parameter support"""
        param_names = []
        pattern_str = "^"
        
        # Find all path parameters like <username>
        parts = re.split(r'(<[^>]+>)', path)
        
        for part in parts:
            if part.startswith('<') and part.endswith('>'):
                # Extract parameter name
                param_name = part[1:-1]
                param_names.append(param_name)
                # Match any characters except /
                pattern_str += r'([^/]+)'
            else:
                # Escape special regex characters
                pattern_str += re.escape(part)
        
        pattern_str += "$"
        return re.compile(pattern_str), param_names
    
    def match(self, path: str, method: str) -> Optional[Dict[str, str]]:
        """Check if this route matches the given path and method"""
        if method.upper() not in self.methods:
            return None
        
        match = self.pattern.match(path)
        if not match:
            return None
        
        # Extract path parameters
        params = {}
        for i, name in enumerate(self.param_names):
            params[name] = match.group(i + 1)
        
        return params


class Rupy:
    """Main Rupy application class"""
    
    def __init__(self, module_name: Any = None):
        self.routes: List[Route] = []
        self.module_name = module_name
    
    def route(self, path: str, methods: Optional[List[str]] = None):
        """Decorator for registering routes"""
        if methods is None:
            methods = ["GET"]
        
        def decorator(handler: Callable):
            route = Route(path, handler, methods)
            self.routes.append(route)
            return handler
        
        return decorator
    
    async def _handle_request(self, aiohttp_request: web.Request) -> web.Response:
        """Handle incoming HTTP request"""
        method = aiohttp_request.method
        path = aiohttp_request.path
        
        # Try to match route
        for route in self.routes:
            path_params = route.match(path, method)
            if path_params is not None:
                # Create Request object
                body = await aiohttp_request.read()
                headers = dict(aiohttp_request.headers)
                
                # Parse query parameters
                query_params = dict(aiohttp_request.query)
                
                request = Request(
                    method=method,
                    path=path,
                    headers=headers,
                    body=body,
                    path_params=path_params,
                    query_params=query_params
                )
                
                # Call handler with request and path parameters
                try:
                    # If handler accepts path parameters, pass them as kwargs
                    import inspect
                    sig = inspect.signature(route.handler)
                    params = list(sig.parameters.keys())
                    
                    if len(params) > 1:
                        # Handler expects path parameters
                        response = await route.handler(request, **path_params)
                    else:
                        # Handler only expects request
                        response = await route.handler(request)
                    
                    # Convert Response to aiohttp response
                    if isinstance(response, Response):
                        headers_dict = response.headers.copy()
                        headers_dict['Content-Type'] = response.content_type
                        
                        return web.Response(
                            body=response.body,
                            status=response.status,
                            headers=headers_dict
                        )
                    else:
                        # Handle raw return values
                        return web.Response(text=str(response))
                
                except Exception as e:
                    # Return 500 error
                    return web.Response(
                        text=f"Internal Server Error: {str(e)}",
                        status=500
                    )
        
        # No route matched
        return web.Response(text="Not Found", status=404)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the web server"""
        app = web.Application()
        
        # Add catch-all route handler
        app.router.add_route('*', '/{path:.*}', self._handle_request)
        
        print(f"Starting Rupy server on http://{host}:{port}")
        web.run_app(app, host=host, port=port)
