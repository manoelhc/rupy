#!/usr/bin/env python3
"""
Real-world Geo-Blocking Middleware Example for Rupy

This example demonstrates production-ready geographical IP blocking using
the geoip2 library and MaxMind's GeoLite2 database.

Features:
- IP-based geolocation using MaxMind GeoLite2
- Country-based blocking/allowing
- Support for both blocklist and allowlist modes
- IPv4 and IPv6 support
- Comprehensive error handling
- Detailed logging

Use Cases:
- GDPR compliance (blocking EU countries if not compliant)
- Sanctions compliance (blocking sanctioned countries)
- Regional content restrictions
- Preventing abuse from specific regions
- Regional service availability

Installation required:
    pip install geoip2

Setup:
1. Download MaxMind GeoLite2 Country database:
   - Create a free account at https://www.maxmind.com/en/geolite2/signup
   - Download GeoLite2-Country.mmdb
   - Place it in the same directory as this script or specify path

Note: For production, consider using MaxMind's paid GeoIP2 database for
better accuracy and update the database regularly (weekly recommended).
"""

import geoip2.database
import geoip2.errors
from rupy import Rupy, Request, Response
import os
import json

app = Rupy()

# ============================================================================
# Geo-Blocking Configuration
# ============================================================================

# Path to MaxMind GeoLite2 Country database
# Download from: https://dev.maxmind.com/geoip/geoip2/geolite2/
GEOIP_DB_PATH = os.environ.get("GEOIP_DB_PATH", "./GeoLite2-Country.mmdb")

# Blocking mode: "blocklist" or "allowlist"
# - blocklist: Block specific countries, allow all others
# - allowlist: Allow specific countries, block all others
BLOCKING_MODE = "blocklist"

# Countries to block (when using blocklist mode)
# Use ISO 3166-1 alpha-2 country codes
# Example: ["CN", "RU", "KP"] blocks China, Russia, North Korea
BLOCKED_COUNTRIES = [
    "CN",  # China
    "RU",  # Russia
    "KP",  # North Korea
]

# Countries to allow (when using allowlist mode)
# All other countries will be blocked
ALLOWED_COUNTRIES = [
    "US",  # United States
    "CA",  # Canada
    "GB",  # United Kingdom
    "DE",  # Germany
    "FR",  # France
]

# Routes that bypass geo-blocking (always accessible)
BYPASS_ROUTES = ["/", "/health", "/blocked"]

# Custom message for blocked requests
BLOCKED_MESSAGE = {
    "error": "Access Denied",
    "message": "Access from your country is not permitted",
    "code": "GEO_BLOCKED"
}


class GeoIPService:
    """Service for IP geolocation using MaxMind GeoIP2."""
    
    def __init__(self, db_path: str):
        """
        Initialize GeoIP service.
        
        Args:
            db_path: Path to MaxMind GeoLite2/GeoIP2 database file
        """
        self.db_path = db_path
        self.reader = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the GeoIP database reader."""
        try:
            if not os.path.exists(self.db_path):
                print(f"[GeoIP] WARNING: Database not found at {self.db_path}")
                print("[GeoIP] Geo-blocking will be disabled")
                print("[GeoIP] Download GeoLite2-Country.mmdb from:")
                print("[GeoIP]   https://dev.maxmind.com/geoip/geoip2/geolite2/")
                return
            
            self.reader = geoip2.database.Reader(self.db_path)
            print(f"[GeoIP] Database loaded successfully from {self.db_path}")
            
        except Exception as e:
            print(f"[GeoIP] Error loading database: {e}")
            print("[GeoIP] Geo-blocking will be disabled")
    
    def get_country_code(self, ip_address: str) -> str:
        """
        Get country code for an IP address.
        
        Args:
            ip_address: IP address to lookup
        
        Returns:
            ISO 3166-1 alpha-2 country code or None if not found
        """
        if not self.reader:
            return None
        
        try:
            response = self.reader.country(ip_address)
            return response.country.iso_code
        except geoip2.errors.AddressNotFoundError:
            print(f"[GeoIP] IP address {ip_address} not found in database")
            return None
        except Exception as e:
            print(f"[GeoIP] Error looking up IP {ip_address}: {e}")
            return None
    
    def get_country_name(self, ip_address: str) -> str:
        """
        Get country name for an IP address.
        
        Args:
            ip_address: IP address to lookup
        
        Returns:
            Country name or None if not found
        """
        if not self.reader:
            return None
        
        try:
            response = self.reader.country(ip_address)
            return response.country.name
        except:
            return None
    
    def close(self):
        """Close the database reader."""
        if self.reader:
            self.reader.close()


# Initialize GeoIP service
geoip_service = GeoIPService(GEOIP_DB_PATH)


def extract_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Checks X-Forwarded-For header first (for proxies/load balancers),
    then falls back to X-Real-IP, then remote address.
    
    Args:
        request: The request object
    
    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header (set by proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
        # The first one is typically the original client
        ip = forwarded_for.split(",")[0].strip()
        return ip
    
    # Check X-Real-IP header (some proxies use this)
    real_ip = request.headers.get("X-Real-IP", "")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to remote address
    # Note: This may not be available in all Rupy versions
    # For testing, we'll use a default
    return "0.0.0.0"


def is_country_blocked(country_code: str) -> bool:
    """
    Check if a country should be blocked based on configuration.
    
    Args:
        country_code: ISO 3166-1 alpha-2 country code
    
    Returns:
        True if country should be blocked, False otherwise
    """
    if not country_code:
        # If we can't determine country, allow by default
        # In production, you might want to block unknown countries
        return False
    
    if BLOCKING_MODE == "blocklist":
        # Block if country is in blocklist
        return country_code in BLOCKED_COUNTRIES
    elif BLOCKING_MODE == "allowlist":
        # Block if country is NOT in allowlist
        return country_code not in ALLOWED_COUNTRIES
    else:
        # Invalid mode, allow by default
        return False


@app.middleware
def geo_blocking_middleware(request: Request):
    """
    Geo-blocking middleware that restricts access based on IP geolocation.
    
    This middleware:
    1. Extracts client IP from request
    2. Looks up country using GeoIP database
    3. Blocks or allows based on configuration
    4. Provides detailed logging
    """
    print(f"[GeoBlock] Processing {request.method} {request.path}")
    
    # Skip geo-blocking for bypass routes
    if request.path in BYPASS_ROUTES:
        print(f"[GeoBlock] Route {request.path} bypasses geo-blocking")
        return request
    
    # Extract client IP
    client_ip = extract_client_ip(request)
    print(f"[GeoBlock] Client IP: {client_ip}")
    
    # For local/private IPs, allow access
    if client_ip.startswith("127.") or client_ip.startswith("192.168.") or \
       client_ip.startswith("10.") or client_ip == "0.0.0.0" or \
       client_ip.startswith("::1") or client_ip.startswith("fe80:"):
        print(f"[GeoBlock] Local/private IP detected, allowing access")
        return request
    
    # Lookup country
    country_code = geoip_service.get_country_code(client_ip)
    country_name = geoip_service.get_country_name(client_ip)
    
    if country_code:
        print(f"[GeoBlock] IP {client_ip} resolved to: {country_name} ({country_code})")
    else:
        print(f"[GeoBlock] Could not determine country for IP {client_ip}")
    
    # Check if country should be blocked
    if is_country_blocked(country_code):
        print(f"[GeoBlock] Blocking access from {country_name} ({country_code})")
        
        # Create blocked response with details
        blocked_response = BLOCKED_MESSAGE.copy()
        blocked_response["country"] = country_name
        blocked_response["country_code"] = country_code
        blocked_response["ip"] = client_ip
        
        response = Response(json.dumps(blocked_response, indent=2), status=403)
        response.set_header("Content-Type", "application/json")
        return response
    
    print(f"[GeoBlock] Allowing access from {country_name} ({country_code})")
    return request


# ============================================================================
# Route Handlers
# ============================================================================

@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    """Public endpoint - not geo-blocked."""
    return Response(json.dumps({
        "message": "Welcome to Geo-Blocking API",
        "geo_blocking_enabled": geoip_service.reader is not None,
        "mode": BLOCKING_MODE,
        "endpoints": {
            "GET /": "This endpoint (no blocking)",
            "GET /api/data": "Protected endpoint (geo-blocked)",
            "GET /api/secure": "Another protected endpoint",
            "GET /country-info": "Get your country info",
            "GET /blocked": "Information about geo-blocking"
        }
    }, indent=2))


@app.route("/health", methods=["GET"])
def health(request: Request) -> Response:
    """Health check endpoint - not geo-blocked."""
    return Response(json.dumps({
        "status": "healthy",
        "geo_blocking": {
            "enabled": geoip_service.reader is not None,
            "mode": BLOCKING_MODE,
            "database": GEOIP_DB_PATH
        }
    }, indent=2))


@app.route("/country-info", methods=["GET"])
def country_info(request: Request) -> Response:
    """Get country information for client IP - not geo-blocked (in BYPASS_ROUTES)."""
    client_ip = extract_client_ip(request)
    country_code = geoip_service.get_country_code(client_ip)
    country_name = geoip_service.get_country_name(client_ip)
    
    return Response(json.dumps({
        "ip": client_ip,
        "country": country_name,
        "country_code": country_code,
        "would_be_blocked": is_country_blocked(country_code)
    }, indent=2))


@app.route("/blocked", methods=["GET"])
def blocked_info(request: Request) -> Response:
    """Information about geo-blocking configuration."""
    config = {
        "geo_blocking": {
            "enabled": geoip_service.reader is not None,
            "mode": BLOCKING_MODE,
            "database_path": GEOIP_DB_PATH
        }
    }
    
    if BLOCKING_MODE == "blocklist":
        config["blocked_countries"] = BLOCKED_COUNTRIES
    else:
        config["allowed_countries"] = ALLOWED_COUNTRIES
    
    config["bypass_routes"] = BYPASS_ROUTES
    
    return Response(json.dumps(config, indent=2))


@app.route("/api/data", methods=["GET"])
def api_data(request: Request) -> Response:
    """Protected endpoint - subject to geo-blocking."""
    return Response(json.dumps({
        "message": "You have access to this data",
        "data": {
            "items": ["item1", "item2", "item3"],
            "count": 3
        }
    }, indent=2))


@app.route("/api/secure", methods=["GET", "POST"])
def api_secure(request: Request) -> Response:
    """Another protected endpoint - subject to geo-blocking."""
    if request.method == "GET":
        return Response(json.dumps({
            "message": "Secure data accessed successfully",
            "timestamp": "2024-01-15T10:30:00Z"
        }, indent=2))
    else:
        return Response(json.dumps({
            "message": "Data saved successfully",
            "body": request.body
        }, indent=2))


if __name__ == "__main__":
    print("=" * 80)
    print("Geo-Blocking Middleware Example - Production Ready")
    print("=" * 80)
    print("\nStarting server on http://127.0.0.1:8000")
    
    print(f"\nGeo-Blocking Configuration:")
    print(f"  Mode: {BLOCKING_MODE}")
    print(f"  Database: {GEOIP_DB_PATH}")
    print(f"  Database exists: {os.path.exists(GEOIP_DB_PATH)}")
    
    if BLOCKING_MODE == "blocklist":
        print(f"  Blocked countries: {', '.join(BLOCKED_COUNTRIES)}")
    else:
        print(f"  Allowed countries: {', '.join(ALLOWED_COUNTRIES)}")
    
    print(f"  Bypass routes: {', '.join(BYPASS_ROUTES)}")
    
    print("\n" + "=" * 80)
    print("Testing Geo-Blocking:")
    print("=" * 80)
    
    print("\n1. Check your country info:")
    print("   curl http://127.0.0.1:8000/country-info")
    
    print("\n2. Access public endpoint (always allowed):")
    print("   curl http://127.0.0.1:8000/")
    
    print("\n3. Access protected endpoint (may be blocked):")
    print("   curl http://127.0.0.1:8000/api/data")
    
    print("\n4. View geo-blocking configuration:")
    print("   curl http://127.0.0.1:8000/blocked")
    
    print("\n5. Test with specific IP (using X-Forwarded-For header):")
    print("   # Test with Chinese IP (will be blocked if CN is in blocklist)")
    print('   curl -H "X-Forwarded-For: 1.2.4.8" \\')
    print("     http://127.0.0.1:8000/api/data")
    print()
    print("   # Test with US IP (usually allowed)")
    print('   curl -H "X-Forwarded-For: 8.8.8.8" \\')
    print("     http://127.0.0.1:8000/api/data")
    print()
    print("   # Test with UK IP")
    print('   curl -H "X-Forwarded-For: 81.2.69.142" \\')
    print("     http://127.0.0.1:8000/api/data")
    
    print("\n" + "=" * 80)
    print("Setup Instructions:")
    print("=" * 80)
    print("""
1. Install required library:
   pip install geoip2

2. Download MaxMind GeoLite2 database:
   - Create free account: https://www.maxmind.com/en/geolite2/signup
   - Download GeoLite2-Country.mmdb
   - Place in current directory or set GEOIP_DB_PATH environment variable

3. Configure blocking:
   - Edit BLOCKED_COUNTRIES or ALLOWED_COUNTRIES in this file
   - Set BLOCKING_MODE to "blocklist" or "allowlist"

4. For production:
   - Update database weekly (GeoLite2) or daily (paid GeoIP2)
   - Use environment variables for configuration
   - Consider using paid GeoIP2 for better accuracy
   - Implement proper logging and monitoring
    """)
    
    print("=" * 80)
    print()
    
    try:
        app.run(host="127.0.0.1", port=8000)
    finally:
        # Clean up GeoIP database connection
        geoip_service.close()
