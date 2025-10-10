# Contributing to Rupy

## Architecture

Rupy is currently implemented in pure Python using `aiohttp` as the underlying HTTP server. This provides a solid foundation for the framework and allows for easy development and testing.

### Current Implementation

The current implementation consists of:

- **Python Package** (`rupy/`): Contains the main framework code
  - `app.py`: Main Rupy application class with routing
  - `request.py`: Request class for handling HTTP requests
  - `response.py`: Response class for handling HTTP responses
  - `routing.py`: Routing utilities and HTTP method constants

### Future Plans: Rust Backend

As mentioned in the project description, Rupy is designed to leverage Rust (Axum + PyO3) for high performance. The Rust backend integration is planned for future releases.

#### Rust Backend Architecture (Planned)

The future Rust implementation will:

1. Use **Axum** as the HTTP server framework
2. Use **PyO3** to create Python bindings
3. Integrate with **Tokio** for async runtime
4. Provide the same Python API while using Rust under the hood
5. Achieve significant performance improvements over pure Python

#### Migration Path

The Python API will remain unchanged, allowing users to seamlessly upgrade from the Python implementation to the Rust-backed implementation when it becomes available.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/manoelhc/rupy.git
cd rupy
```

2. Install in development mode:
```bash
pip install -e .
```

### Running Tests

```bash
python test_rupy.py
```

### Running Examples

```bash
python examples/simple_app.py
```

Then test the endpoints:
```bash
curl http://localhost:8000/
curl http://localhost:8000/user/John
curl -X POST http://localhost:8000/echo -H "Content-Type: application/json" -d '{"test": "data"}'
```

## Project Structure

```
rupy/
├── rupy/                  # Main package
│   ├── __init__.py       # Package exports
│   ├── app.py            # Rupy application class
│   ├── request.py        # Request class
│   ├── response.py       # Response class
│   └── routing.py        # Routing utilities
├── examples/             # Example applications
│   └── simple_app.py    # Basic example
├── test_rupy.py         # Unit tests
├── pyproject.toml       # Package metadata
├── README.md            # User documentation
├── INSTRUCTIONS.md      # Project specifications
└── LICENSE              # MIT License
```

## Contributing Guidelines

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add or update tests
5. Ensure all tests pass
6. Submit a pull request

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all public APIs
- Keep functions focused and small

## Testing

- Write tests for new features
- Ensure all existing tests pass
- Test edge cases and error conditions

## Future Rust Implementation

If you're interested in contributing to the Rust backend implementation:

1. Familiarity with Rust and Axum
2. Experience with PyO3 for Python bindings
3. Understanding of async Rust with Tokio
4. Knowledge of Python C extensions

Please open an issue to discuss Rust backend implementation plans before starting work.
