"""
Request class for handling HTTP requests
"""
import json
from typing import Dict, Any, Optional


class Request:
    """Represents an HTTP request"""
    
    def __init__(self, method: str, path: str, headers: Dict[str, str], 
                 body: bytes, path_params: Optional[Dict[str, str]] = None,
                 query_params: Optional[Dict[str, str]] = None):
        self.method = method
        self.path = path
        self.headers = headers
        self._body = body
        self.path_params = path_params or {}
        self.query_params = query_params or {}
    
    async def json(self) -> Any:
        """Parse request body as JSON"""
        try:
            return json.loads(self._body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to parse JSON: {e}")
    
    async def text(self) -> str:
        """Get request body as text"""
        return self._body.decode('utf-8')
    
    async def body(self) -> bytes:
        """Get raw request body"""
        return self._body
