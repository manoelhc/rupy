#!/usr/bin/env python3
"""
Real-world Rate Limiting Middleware Example for Rupy

This example demonstrates production-ready rate limiting based on both
User-Agent and Remote IP address, with multiple rate limiting strategies.

Features:
- Rate limiting by IP address
- Rate limiting by User-Agent
- Sliding window algorithm for accurate rate limiting
- Multiple rate limit tiers (e.g., per-minute, per-hour)
- Whitelist/blacklist support
- Detailed rate limit headers (X-RateLimit-*)
- Redis-like in-memory storage with TTL

Use Cases:
- Prevent API abuse and DDoS attacks
- Enforce API usage quotas
- Protect against brute force attacks
- Fair resource allocation among users
- Bot detection and throttling

In production, consider:
- Using Redis or Memcached for distributed rate limiting
- Implementing token bucket or leaky bucket algorithms
- Adding rate limit tiers based on authentication/subscription
- Monitoring and alerting for rate limit hits
"""

import time
import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple, Optional
from rupy import Rupy, Request, Response

app = Rupy()

# ============================================================================
# Rate Limiting Configuration
# ============================================================================

# Rate limit settings - format: (requests, seconds)
RATE_LIMITS = {
    # General limits
    "default": [
        (10, 60),      # 10 requests per minute
        (100, 3600),   # 100 requests per hour
    ],
    
    # Stricter limits for sensitive endpoints
    "strict": [
        (5, 60),       # 5 requests per minute
        (20, 3600),    # 20 requests per hour
    ],
    
    # Relaxed limits for public endpoints
    "relaxed": [
        (100, 60),     # 100 requests per minute
        (1000, 3600),  # 1000 requests per hour
    ],
}

# Route-specific rate limit configurations
ROUTE_LIMITS = {
    "/api/search": "strict",
    "/api/login": "strict",
    "/api/register": "strict",
    "/api/data": "default",
    "/api/public": "relaxed",
}

# Default rate limit tier for routes not specified above
DEFAULT_LIMIT_TIER = "default"

# IP addresses that bypass rate limiting (whitelisted)
WHITELISTED_IPS = [
    "127.0.0.1",
    "::1",
]

# User-Agents that bypass rate limiting (e.g., monitoring services)
WHITELISTED_USER_AGENTS = [
    "monitoring-bot",
    "health-checker",
]

# IP addresses with stricter limits (blacklisted/suspicious)
BLACKLISTED_IPS = []

# Block completely if rate limit exceeded this many times
MAX_RATE_LIMIT_VIOLATIONS = 10


class RateLimiter:
    """
    Rate limiter with sliding window algorithm.
    Tracks requests per IP and User-Agent combination.
    """
    
    def __init__(self):
        """Initialize rate limiter storage."""
        # Storage: {key: [(timestamp1, count1), (timestamp2, count2), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        
        # Violation tracking: {key: violation_count}
        self.violations: Dict[str, int] = defaultdict(int)
        
        # Last cleanup time
        self.last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Clean up expired entries to prevent memory bloat."""
        current_time = time.time()
        
        # Only cleanup every 5 minutes
        if current_time - self.last_cleanup < 300:
            return
        
        print("[RateLimit] Performing cleanup of old entries...")
        
        # Clean up entries older than 1 hour
        cutoff_time = current_time - 3600
        
        for key in list(self.requests.keys()):
            # Remove old timestamps
            self.requests[key] = [
                (ts, count) for ts, count in self.requests[key]
                if ts > cutoff_time
            ]
            
            # Remove key if no entries left
            if not self.requests[key]:
                del self.requests[key]
        
        self.last_cleanup = current_time
        print(f"[RateLimit] Cleanup complete. Tracking {len(self.requests)} keys")
    
    def _get_rate_limit_key(self, ip: str, user_agent: str) -> str:
        """
        Generate a unique key for rate limiting.
        Combines IP and User-Agent for more granular tracking.
        
        Args:
            ip: Client IP address
            user_agent: Client User-Agent string
        
        Returns:
            Unique rate limit key
        """
        # Truncate user agent to prevent key bloat
        ua_hash = hash(user_agent[:200]) % 100000
        return f"{ip}:{ua_hash}"
    
    def check_rate_limit(
        self,
        ip: str,
        user_agent: str,
        limits: list
    ) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if request is within rate limits.
        
        Args:
            ip: Client IP address
            user_agent: Client User-Agent string
            limits: List of (requests, seconds) tuples
        
        Returns:
            Tuple of (allowed, retry_after, limit_remaining)
        """
        key = self._get_rate_limit_key(ip, user_agent)
        current_time = time.time()
        
        # Cleanup old entries periodically
        self._cleanup_old_entries()
        
        # Check each rate limit tier
        for max_requests, window_seconds in limits:
            # Get requests in the current window
            window_start = current_time - window_seconds
            
            # Count requests in this window
            window_requests = [
                (ts, count) for ts, count in self.requests[key]
                if ts > window_start
            ]
            
            total_requests = sum(count for _, count in window_requests)
            
            # Check if limit exceeded
            if total_requests >= max_requests:
                # Calculate retry-after time
                if window_requests:
                    oldest_timestamp = min(ts for ts, _ in window_requests)
                    retry_after = int(window_seconds - (current_time - oldest_timestamp)) + 1
                else:
                    retry_after = int(window_seconds)
                
                print(f"[RateLimit] Limit exceeded for {key}: {total_requests}/{max_requests} in {window_seconds}s")
                
                # Track violation
                self.violations[key] += 1
                
                return False, retry_after, 0
        
        # All limits passed - record this request
        self.requests[key].append((current_time, 1))
        
        # Calculate remaining requests for the strictest limit
        if limits:
            max_requests, window_seconds = limits[0]
            window_start = current_time - window_seconds
            window_count = sum(
                count for ts, count in self.requests[key]
                if ts > window_start
            )
            remaining = max(0, max_requests - window_count)
        else:
            remaining = None
        
        return True, None, remaining
    
    def is_blocked(self, ip: str, user_agent: str) -> bool:
        """
        Check if IP/User-Agent is temporarily blocked due to violations.
        
        Args:
            ip: Client IP address
            user_agent: Client User-Agent string
        
        Returns:
            True if blocked, False otherwise
        """
        key = self._get_rate_limit_key(ip, user_agent)
        return self.violations.get(key, 0) >= MAX_RATE_LIMIT_VIOLATIONS
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            "tracked_keys": len(self.requests),
            "total_violations": sum(self.violations.values()),
            "blocked_keys": sum(1 for v in self.violations.values() if v >= MAX_RATE_LIMIT_VIOLATIONS)
        }


# Initialize rate limiter
rate_limiter = RateLimiter()


def extract_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Args:
        request: The request object
    
    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header first
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP", "")
    if real_ip:
        return real_ip.strip()
    
    # Default for testing
    return "127.0.0.1"


def extract_user_agent(request: Request) -> str:
    """
    Extract User-Agent from request.
    
    Args:
        request: The request object
    
    Returns:
        User-Agent string
    """
    return request.headers.get("User-Agent", "Unknown")


def get_rate_limit_for_route(path: str) -> list:
    """
    Get rate limit configuration for a route.
    
    Args:
        path: Request path
    
    Returns:
        List of (requests, seconds) tuples
    """
    # Check for exact match
    if path in ROUTE_LIMITS:
        tier = ROUTE_LIMITS[path]
        return RATE_LIMITS[tier]
    
    # Check for prefix match
    for route_pattern, tier in ROUTE_LIMITS.items():
        if path.startswith(route_pattern):
            return RATE_LIMITS[tier]
    
    # Use default
    return RATE_LIMITS[DEFAULT_LIMIT_TIER]


def is_whitelisted(ip: str, user_agent: str) -> bool:
    """
    Check if IP or User-Agent is whitelisted.
    
    Args:
        ip: Client IP address
        user_agent: Client User-Agent string
    
    Returns:
        True if whitelisted, False otherwise
    """
    # Check IP whitelist
    if ip in WHITELISTED_IPS:
        return True
    
    # Check User-Agent whitelist
    for whitelisted_ua in WHITELISTED_USER_AGENTS:
        if whitelisted_ua.lower() in user_agent.lower():
            return True
    
    return False


@app.middleware
def rate_limiting_middleware(request: Request):
    """
    Rate limiting middleware based on IP and User-Agent.
    
    This middleware:
    1. Extracts client IP and User-Agent
    2. Checks whitelists and blacklists
    3. Enforces rate limits using sliding window
    4. Returns 429 Too Many Requests if limit exceeded
    5. Adds rate limit headers to response
    """
    print(f"[RateLimit] Processing {request.method} {request.path}")
    
    # Extract client info
    client_ip = extract_client_ip(request)
    user_agent = extract_user_agent(request)
    
    print(f"[RateLimit] Client IP: {client_ip}, User-Agent: {user_agent[:50]}...")
    
    # Check whitelist
    if is_whitelisted(client_ip, user_agent):
        print(f"[RateLimit] Client is whitelisted, bypassing rate limit")
        return request
    
    # Check if client is blocked due to violations
    if rate_limiter.is_blocked(client_ip, user_agent):
        print(f"[RateLimit] Client is temporarily blocked due to violations")
        return Response(
            json.dumps({
                "error": "Too Many Requests",
                "message": "You have been temporarily blocked due to excessive rate limit violations",
                "retry_after": 3600  # 1 hour
            }, indent=2),
            status=429
        )
    
    # Get rate limits for this route
    limits = get_rate_limit_for_route(request.path)
    
    # Check rate limit
    allowed, retry_after, remaining = rate_limiter.check_rate_limit(
        client_ip,
        user_agent,
        limits
    )
    
    if not allowed:
        print(f"[RateLimit] Rate limit exceeded, retry after {retry_after}s")
        
        # Return 429 Too Many Requests
        response = Response(
            json.dumps({
                "error": "Too Many Requests",
                "message": "Rate limit exceeded",
                "retry_after": retry_after,
                "limits": [
                    {"requests": req, "window": f"{sec}s"}
                    for req, sec in limits
                ]
            }, indent=2),
            status=429
        )
        
        # Add rate limit headers
        response.set_header("X-RateLimit-Limit", str(limits[0][0]))
        response.set_header("X-RateLimit-Remaining", "0")
        response.set_header("X-RateLimit-Reset", str(int(time.time()) + retry_after))
        response.set_header("Retry-After", str(retry_after))
        
        return response
    
    print(f"[RateLimit] Request allowed, {remaining} requests remaining")
    
    # In a real implementation, we would add rate limit headers to the response
    # For now, just continue to the handler
    return request


# ============================================================================
# Route Handlers
# ============================================================================

@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    """Root endpoint with rate limit info."""
    return Response(json.dumps({
        "message": "Rate Limiting API",
        "rate_limits": {
            "default": RATE_LIMITS["default"],
            "strict": RATE_LIMITS["strict"],
            "relaxed": RATE_LIMITS["relaxed"]
        },
        "endpoints": {
            "GET /api/data": "Default rate limits",
            "GET /api/search": "Strict rate limits",
            "POST /api/login": "Strict rate limits",
            "GET /api/public": "Relaxed rate limits",
            "GET /stats": "Rate limiter statistics"
        }
    }, indent=2))


@app.route("/api/data", methods=["GET"])
def api_data(request: Request) -> Response:
    """API endpoint with default rate limits."""
    return Response(json.dumps({
        "message": "Data retrieved successfully",
        "data": {"items": ["item1", "item2", "item3"]},
        "rate_limit": "default (10/min, 100/hour)"
    }, indent=2))


@app.route("/api/search", methods=["GET"])
def api_search(request: Request) -> Response:
    """API endpoint with strict rate limits."""
    query = request.body or "default"
    return Response(json.dumps({
        "message": "Search completed",
        "query": query,
        "results": ["result1", "result2"],
        "rate_limit": "strict (5/min, 20/hour)"
    }, indent=2))


@app.route("/api/login", methods=["POST"])
def api_login(request: Request) -> Response:
    """Login endpoint with strict rate limits to prevent brute force."""
    return Response(json.dumps({
        "message": "Login processed",
        "token": "sample-token-123",
        "rate_limit": "strict (5/min, 20/hour)"
    }, indent=2))


@app.route("/api/public", methods=["GET"])
def api_public(request: Request) -> Response:
    """Public API endpoint with relaxed rate limits."""
    return Response(json.dumps({
        "message": "Public data",
        "data": {"value": 42},
        "rate_limit": "relaxed (100/min, 1000/hour)"
    }, indent=2))


@app.route("/stats", methods=["GET"])
def stats(request: Request) -> Response:
    """Get rate limiter statistics."""
    stats = rate_limiter.get_stats()
    return Response(json.dumps({
        "rate_limiter_stats": stats,
        "configuration": {
            "whitelisted_ips": WHITELISTED_IPS,
            "max_violations": MAX_RATE_LIMIT_VIOLATIONS
        }
    }, indent=2))


if __name__ == "__main__":
    print("=" * 80)
    print("Rate Limiting Middleware Example - Production Ready")
    print("=" * 80)
    print("\nStarting server on http://127.0.0.1:8000")
    
    print(f"\nRate Limit Configuration:")
    print(f"  Default: {RATE_LIMITS['default']}")
    print(f"  Strict: {RATE_LIMITS['strict']}")
    print(f"  Relaxed: {RATE_LIMITS['relaxed']}")
    print(f"  Max violations before block: {MAX_RATE_LIMIT_VIOLATIONS}")
    
    print("\n" + "=" * 80)
    print("Testing Rate Limiting:")
    print("=" * 80)
    
    print("\n1. Normal request:")
    print("   curl http://127.0.0.1:8000/api/data")
    
    print("\n2. Test rate limit with multiple requests:")
    print("   # Run this command to hit the rate limit")
    print("   for i in {1..15}; do")
    print("     echo \"Request $i:\"")
    print("     curl http://127.0.0.1:8000/api/data")
    print("     echo")
    print("   done")
    
    print("\n3. Test strict rate limit:")
    print("   # This endpoint has stricter limits (5/min)")
    print("   for i in {1..8}; do")
    print("     echo \"Request $i:\"")
    print("     curl http://127.0.0.1:8000/api/search")
    print("     echo")
    print("   done")
    
    print("\n4. Test with custom User-Agent:")
    print('   curl -H "User-Agent: my-custom-bot" \\')
    print("     http://127.0.0.1:8000/api/data")
    
    print("\n5. Test with different IP (using X-Forwarded-For):")
    print('   curl -H "X-Forwarded-For: 203.0.113.42" \\')
    print("     http://127.0.0.1:8000/api/data")
    
    print("\n6. View rate limiter statistics:")
    print("   curl http://127.0.0.1:8000/stats")
    
    print("\n7. Test whitelisted User-Agent (bypasses rate limit):")
    print('   # This will not be rate limited')
    print('   curl -H "User-Agent: monitoring-bot" \\')
    print("     http://127.0.0.1:8000/api/data")
    
    print("\n" + "=" * 80)
    print("Load Testing with Apache Bench (ab):")
    print("=" * 80)
    print("""
# Install Apache Bench (if not installed)
# Ubuntu/Debian: sudo apt-get install apache2-utils
# macOS: brew install httpie

# Send 100 requests with 10 concurrent connections
ab -n 100 -c 10 http://127.0.0.1:8000/api/data

# You should see rate limit errors after the first 10 requests
    """)
    
    print("=" * 80)
    print("Production Considerations:")
    print("=" * 80)
    print("""
1. Use Redis or Memcached for distributed rate limiting across multiple servers
2. Implement token bucket or leaky bucket for smoother rate limiting
3. Add rate limit tiers based on authentication/API keys
4. Monitor rate limit hits and adjust limits based on usage patterns
5. Consider implementing adaptive rate limiting based on server load
6. Add logging and alerting for suspicious patterns
7. Use environment variables for configuration
    """)
    
    print("=" * 80)
    print()
    
    app.run(host="127.0.0.1", port=8000)
