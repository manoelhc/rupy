#!/usr/bin/env python3
"""Simple example showing basic Rupy usage"""

from rupy import Rupy

# Create a Rupy application
app = Rupy()

if __name__ == "__main__":
    # Run the server on localhost:8000
    # Returns 404 for all requests (routing not yet implemented)
    app.run(host="127.0.0.1", port=8000)
