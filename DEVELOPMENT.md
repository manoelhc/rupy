# Rupy Development Notes

## Rust Backend Implementation Status

### ✅ Completed

- [x] Rust project setup with Cargo.toml
- [x] PyO3 bindings for Request, Response classes
- [x] Axum HTTP server integration
- [x] Route pattern compilation and matching
- [x] Path parameter extraction
- [x] Query parameter support
- [x] Maturin build configuration
- [x] Python wrapper for Rust backend
- [x] Wheel building and packaging

### 🔨 In Progress / Known Issues

- [ ] **Async Python handler support**: Currently investigating best approach for calling async Python functions from Rust
  - Python async functions return coroutines that need to be awaited
  - Options: pyo3-asyncio, manual event loop handling, or sync wrapper
  - Server starts but handlers don't respond yet due to async handling

- [ ] Error handling improvements
  - Better error messages for Python exceptions
  - Proper HTTP error responses

### 📋 Future Enhancements

- [ ] Middleware support
- [ ] WebSocket support
- [ ] Static file serving
- [ ] Request/Response streaming
- [ ] Connection pooling optimizations
- [ ] Performance benchmarks vs FastAPI/Flask
- [ ] Comprehensive integration tests

## Technical Notes

### Async Handling Approaches

1. **pyo3-asyncio**: Integrate Python's asyncio with Tokio
   - Pros: Proper async support
   - Cons: Complex integration, additional dependency

2. **Sync Wrapper**: Call Python handlers synchronously
   - Pros: Simpler implementation
   - Cons: Loses async benefits

3. **Manual await**: Detect coroutines and await them
   - Pros: Flexible approach
   - Cons: Requires careful handling of event loops

### Build System

Using maturin with:
- `python-source = "python"`: Python files in python/ directory
- `module-name = "rupy.rupy_core"`: Rust extension module name  
- abi3 support for compatibility across Python versions

### Performance Considerations

- Route matching uses compiled regex patterns
- Handler lookups use Arc<Mutex<>> for thread-safe sharing
- PyO3 GIL handling for Python calls
- Body reading done async with http-body-util

## Development Workflow

```bash
# Build and test cycle
maturin develop --release
python test_rust_app.py

# Check Rust code
cargo check
cargo clippy

# Format code
cargo fmt
```

## References

- [PyO3 Guide](https://pyo3.rs/v0.22.0/)
- [Axum Documentation](https://docs.rs/axum/latest/axum/)
- [Maturin Documentation](https://www.maturin.rs/)
- [pyo3-asyncio](https://github.com/awestlake87/pyo3-asyncio)
