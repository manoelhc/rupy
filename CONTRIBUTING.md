# Contributing to Rupy

## Architecture

Rupy is implemented with a **Rust backend** using Axum and PyO3, providing high-performance HTTP serving while maintaining an ergonomic Python API.

### Current Implementation

The current implementation consists of:

- **Rust Backend** (`src/lib.rs`): HTTP server using Axum
  - Route matching and request handling
  - Integration with Python handlers via PyO3
  - Async request/response processing
  
- **Python Package** (`python/rupy/`): Python API layer
  - `__init__.py`: Main module with Rupy class wrapper
  - `routing.py`: HTTP method constants
  - Fallback pure Python implementation (for development)

### Technology Stack

- **Rust**: Axum web framework + PyO3 for Python bindings
- **Python**: Type-hinted API with async/await support
- **Build Tool**: Maturin for building Python extension modules

##Future Plans: Rust Backend

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
- Rust and Cargo (for building the Rust extension)
- pip and maturin

### Installation

1. Clone the repository:
```bash
git clone https://github.com/manoelhc/rupy.git
cd rupy
```

2. Install maturin:
```bash
pip install maturin
```

3. Build and install in development mode:
```bash
maturin develop --release
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
├── src/                   # Rust source code
│   └── lib.rs            # Rust backend implementation
├── python/rupy/          # Python package
│   ├── __init__.py       # Main module with Rupy wrapper
│   ├── routing.py        # HTTP method constants
│   ├── app.py            # Pure Python fallback
│   ├── request.py        # Request class (fallback)
│   └── response.py       # Response class (fallback)
├── examples/             # Example applications
│   ├── simple_app.py    # Basic example
│   ├── json_api.py      # REST API example
│   └── multi_route.py   # Multiple routing patterns
├── Cargo.toml           # Rust dependencies
├── pyproject.toml       # Package metadata
├── test_rupy.py         # Unit tests
├── README.md            # User documentation
├── CONTRIBUTING.md      # This file
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

- **Rust**: Follow standard Rust formatting (`cargo fmt`)
- **Python**: Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all public APIs
- Keep functions focused and small

## Building the Rust Extension

To build the Rust extension:

```bash
# Development build
maturin develop

# Release build
maturin build --release
```

## Testing

- Write tests for new features
- Ensure all existing tests pass
- Test edge cases and error conditions
- Test both Rust and Python fallback implementations

## Rust Backend Development

The Rust backend is implemented using:

- **Axum 0.7**: Modern web framework
- **PyO3 0.22**: Python bindings with abi3 support
- **Tokio**: Async runtime
- **Regex**: Route pattern matching

Key components:
- Route registration and matching
- Request/Response PyO3 classes
- Python handler invocation from Rust
- Async request handling

If you're contributing to the Rust backend:

1. Familiarity with Rust and Axum
2. Experience with PyO3 for Python bindings
3. Understanding of async Rust with Tokio
4. Knowledge of Python C extensions

Please open an issue to discuss significant changes before starting work.
