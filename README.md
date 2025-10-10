# Rupy

A high-performance web framework for Python, powered by Rust and Axum.

## Current Status

This is the initial implementation with basic functionality:
- ✅ `Rupy()` class instantiation
- ✅ `app.run(host, port)` method to start the server
- ✅ Returns 404 for all requests (routing not yet implemented)
- ✅ JSON-formatted request logging

## Building from Source

### Prerequisites

- Python 3.8+
- Rust 1.56+
- maturin

### Build Steps

1. Install maturin:
```bash
pip install maturin
```

2. Build the project:
```bash
maturin build --release
```

3. Install the wheel:
```bash
pip install target/wheels/rupy-*.whl
```

Or build and install in development mode:
```bash
maturin develop
```

## Usage

```python
from rupy import Rupy

app = Rupy()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
```

Run the example:
```bash
python example.py
```

The server will start and log all incoming requests in JSON format:
```json
{"timestamp": 1234567890, "method": "GET", "path": "/", "status": 404, "message": "Not Found"}
```

## Architecture

- **Rust Backend**: Uses Axum web framework for high-performance HTTP handling
- **Python Bindings**: PyO3 provides seamless Python-Rust interoperability
- **Async Runtime**: Tokio powers the asynchronous server

## License

MIT License - see LICENSE file for details
