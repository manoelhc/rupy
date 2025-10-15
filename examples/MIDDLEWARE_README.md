# Rupy Middleware Examples - Production Ready

This directory contains comprehensive, production-ready middleware examples for the Rupy web framework. Each example demonstrates real-world implementations with proper error handling, security best practices, and detailed documentation.

## Overview

These examples showcase four essential middleware patterns:

1. **JWT Authentication** - Token-based authentication with proper validation
2. **CORS** - Cross-Origin Resource Sharing with security best practices
3. **Geo-Blocking** - IP-based geographical access control
4. **Rate Limiting** - Request throttling based on IP and User-Agent

## Examples

### 1. JWT Authentication Middleware (`jwt_middleware.py`)

Production-ready JWT authentication using the PyJWT library.

**Features:**
- Real JWT token creation and validation with PyJWT
- Token signature verification and expiration checking
- User role support (user/admin)
- Comprehensive error handling
- Login, registration, and protected endpoints

**Installation:**
```bash
pip install PyJWT
```

**Usage:**
```bash
python examples/jwt_middleware.py
```

**Test it:**
```bash
# Get a token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "pass123"}' | \
  grep -o '"token":"[^"]*"' | cut -d'"' -f4)

# Access protected endpoint
curl http://127.0.0.1:8000/profile \
  -H "Authorization: Bearer $TOKEN"
```

**Key Concepts:**
- Bearer token authentication
- JWT token structure (header.payload.signature)
- Token expiration handling
- Public vs. protected routes

---

### 2. CORS Middleware (`cors_middleware.py`)

Production-ready CORS handling with comprehensive support for cross-origin requests.

**Features:**
- Configurable allowed origins (specific domains or wildcard)
- Preflight OPTIONS request handling
- Support for credentials (cookies, authorization headers)
- Configurable allowed methods and headers
- Security best practices

**Usage:**
```bash
python examples/cors_middleware.py
```

**Test it:**
```bash
# Simple CORS request
curl -H "Origin: http://localhost:3000" \
  http://127.0.0.1:8000/

# Preflight request
curl -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  http://127.0.0.1:8000/api/users
```

**Key Concepts:**
- Origin-based access control
- Preflight requests for non-simple requests
- Credentials and cookie handling
- CORS security implications

---

### 3. Geo-Blocking Middleware (`geo_blocking_middleware.py`)

IP-based geographical access control using MaxMind GeoLite2 database.

**Features:**
- IP geolocation using MaxMind GeoLite2
- Blocklist and allowlist modes
- Country-based access control
- IPv4 and IPv6 support
- X-Forwarded-For header support for proxies

**Installation:**
```bash
pip install geoip2
```

**Setup:**
1. Create a free MaxMind account at https://www.maxmind.com/en/geolite2/signup
2. Download GeoLite2-Country.mmdb
3. Place it in the same directory or set `GEOIP_DB_PATH` environment variable

**Usage:**
```bash
python examples/geo_blocking_middleware.py
```

**Test it:**
```bash
# Check your country
curl http://127.0.0.1:8000/country-info

# Test with specific IP (using proxy header)
curl -H "X-Forwarded-For: 8.8.8.8" \
  http://127.0.0.1:8000/api/data
```

**Key Concepts:**
- IP geolocation databases
- Proxy header handling (X-Forwarded-For)
- Blocklist vs. allowlist strategies
- GDPR and regional compliance

---

### 4. Rate Limiting Middleware (`rate_limiting_middleware.py`)

Request throttling based on IP address and User-Agent with sliding window algorithm.

**Features:**
- Sliding window rate limiting algorithm
- Multiple rate limit tiers (default, strict, relaxed)
- Rate limiting by IP and User-Agent combination
- Route-specific configurations
- Whitelist/blacklist support
- X-RateLimit-* headers
- Violation tracking and temporary blocking

**Usage:**
```bash
python examples/rate_limiting_middleware.py
```

**Test it:**
```bash
# Test rate limiting
for i in {1..15}; do
  echo "Request $i:"
  curl http://127.0.0.1:8000/api/data
  echo
done

# View statistics
curl http://127.0.0.1:8000/stats
```

**Load Testing:**
```bash
# Using Apache Bench
ab -n 100 -c 10 http://127.0.0.1:8000/api/data
```

**Key Concepts:**
- Sliding window algorithm
- Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining)
- Retry-After header
- Distributed rate limiting considerations

---

## Production Considerations

### Security Best Practices

1. **JWT Authentication**
   - Use strong secrets (environment variables)
   - Consider RS256 (asymmetric) over HS256 (symmetric)
   - Implement token revocation/blacklisting
   - Add refresh token mechanism
   - Use HTTPS in production

2. **CORS**
   - Avoid wildcard (*) with credentials
   - Specify exact origins in production
   - Limit allowed methods and headers
   - Be cautious with Access-Control-Allow-Credentials

3. **Geo-Blocking**
   - Update GeoIP database regularly (weekly for GeoLite2)
   - Consider paid GeoIP2 for better accuracy
   - Log blocked requests for monitoring
   - Handle edge cases (VPNs, proxies)

4. **Rate Limiting**
   - Use Redis/Memcached for distributed systems
   - Implement different tiers based on authentication
   - Monitor rate limit violations
   - Consider adaptive rate limiting based on load

### Scaling Considerations

1. **Distributed Systems**
   - Use Redis for shared state (rate limiting, sessions)
   - Implement consistent hashing for geo data
   - Consider CDN for geo-distributed applications
   - Use load balancer with proper header forwarding

2. **Performance**
   - Cache GeoIP lookups
   - Use efficient data structures (sliding window)
   - Implement connection pooling for databases
   - Monitor middleware overhead

3. **Monitoring**
   - Log authentication failures
   - Track rate limit violations
   - Monitor geo-blocking patterns
   - Set up alerts for suspicious activity

### Environment Configuration

Use environment variables for production configuration:

```bash
# JWT
export JWT_SECRET="your-strong-secret-key"
export JWT_ALGORITHM="RS256"
export JWT_EXPIRATION_HOURS="24"

# CORS
export ALLOWED_ORIGINS="https://app.example.com,https://admin.example.com"
export ALLOW_CREDENTIALS="true"

# Geo-Blocking
export GEOIP_DB_PATH="/var/geoip/GeoLite2-Country.mmdb"
export BLOCKING_MODE="blocklist"
export BLOCKED_COUNTRIES="CN,RU,KP"

# Rate Limiting
export REDIS_URL="redis://localhost:6379"
export RATE_LIMIT_DEFAULT="10,60"
```

## Dependencies

Install all required dependencies:

```bash
pip install PyJWT geoip2 requests
```

For production with Redis:
```bash
pip install redis
```

## Testing

Each example includes comprehensive curl-based testing examples. For automated testing:

```bash
# Run middleware tests
python -m pytest tests/test_middlewares.py

# Run specific middleware tests
python -m pytest tests/test_jwt_auth.py
python -m pytest tests/test_cors.py
```

## License

These examples are part of the Rupy project and are provided under the MIT License.

## Contributing

Improvements and additional middleware examples are welcome! Please ensure:
- Production-ready code quality
- Comprehensive documentation
- Security best practices
- Test coverage
- Real-world use cases

## Resources

- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [CORS Specification](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [MaxMind GeoIP2](https://www.maxmind.com/en/geoip2-services-and-databases)
- [Rate Limiting Patterns](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
- [OWASP Security Guidelines](https://owasp.org/www-project-web-security-testing-guide/)
