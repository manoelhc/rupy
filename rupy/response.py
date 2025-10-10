"""
Response class for handling HTTP responses
"""
import json
from typing import Any, Dict, Optional, Union


class Response:
    """Represents an HTTP response"""
    
    def __init__(self, body: Union[str, dict, list, bytes] = "", 
                 status: int = 200,
                 headers: Optional[Dict[str, str]] = None,
                 content_type: Optional[str] = None):
        self.status = status
        self.headers = headers or {}
        
        # Handle different body types
        if isinstance(body, (dict, list)):
            self._body = json.dumps(body).encode('utf-8')
            self.content_type = content_type or "application/json"
        elif isinstance(body, str):
            self._body = body.encode('utf-8')
            self.content_type = content_type or "text/plain"
        elif isinstance(body, bytes):
            self._body = body
            self.content_type = content_type or "application/octet-stream"
        else:
            self._body = str(body).encode('utf-8')
            self.content_type = content_type or "text/plain"
    
    @property
    def body(self) -> bytes:
        """Get response body as bytes"""
        return self._body
    
    def set_header(self, key: str, value: str) -> None:
        """Set a response header"""
        self.headers[key] = value
