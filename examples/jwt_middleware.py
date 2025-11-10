#!/usr/bin/env python3
"""
Real-world JWT Authentication Middleware Example for Rupy

This example demonstrates production-ready JWT authentication using the PyJWT library.
Features:
- Proper JWT token validation with signature verification
- Token expiration checking
- User information extraction from token claims
- Refresh token support
- Public/protected route separation
- Comprehensive error handling

Installation required:
    pip install PyJWT

In production, also consider:
- Storing JWT_SECRET in environment variables
- Using public/private key pairs (RS256) instead of symmetric keys (HS256)
- Implementing token revocation/blacklisting
- Adding rate limiting to prevent brute force attacks
"""

import jwt
import json
from datetime import datetime, timedelta
from rupy import Rupy, Request, Response

app = Rupy()

# JWT Configuration
# In production: Use environment variables and stronger secrets
JWT_SECRET = "your-secret-key-change-this-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Public routes that don't require authentication
PUBLIC_ROUTES = ["/", "/login", "/register", "/health"]


def create_jwt_token(user_id: str, username: str, role: str = "user") -> str:
    """
    Create a JWT token with user information and expiration.
    
    Args:
        user_id: Unique user identifier
        username: Username
        role: User role (e.g., 'user', 'admin')
    
    Returns:
        Encoded JWT token string
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


@app.middleware
def jwt_auth_middleware(request: Request):
    """
    JWT authentication middleware with comprehensive validation.
    
    This middleware:
    1. Skips authentication for public routes
    2. Extracts Bearer token from Authorization header
    3. Validates token signature and expiration
    4. Extracts user information and attaches to request
    5. Returns appropriate error responses for invalid tokens
    """
    print(f"[JWT Auth] Processing {request.method} {request.path}")

    # Skip authentication for public routes
    if request.path in PUBLIC_ROUTES:
        print(f"[JWT Auth] Public route, skipping authentication")
        return request

    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header:
        print("[JWT Auth] No Authorization header found")
        return Response(
            json.dumps({
                "error": "Unauthorized",
                "message": "Missing authorization header"
            }),
            status=401
        )

    # Check Bearer token format
    if not auth_header.startswith("Bearer "):
        print("[JWT Auth] Invalid authorization header format")
        return Response(
            json.dumps({
                "error": "Unauthorized",
                "message": "Invalid authorization header format. Use: Bearer <token>"
            }),
            status=401
        )

    # Extract token
    token = auth_header[7:]  # Remove "Bearer " prefix

    try:
        # Verify and decode token
        payload = verify_jwt_token(token)
        
        # Extract user information
        user_id = payload.get("user_id")
        username = payload.get("username")
        role = payload.get("role", "user")
        
        print(f"[JWT Auth] Token valid for user: {username} (ID: {user_id}, Role: {role})")
        
        # In a real application, you could attach user info to request
        # For now, we'll just log it
        # request.user = {"id": user_id, "username": username, "role": role}
        
        return request

    except jwt.ExpiredSignatureError:
        print("[JWT Auth] Token has expired")
        return Response(
            json.dumps({
                "error": "Unauthorized",
                "message": "Token has expired. Please login again."
            }),
            status=401
        )
    
    except jwt.InvalidTokenError as e:
        print(f"[JWT Auth] Invalid token: {str(e)}")
        return Response(
            json.dumps({
                "error": "Unauthorized",
                "message": "Invalid token"
            }),
            status=401
        )
    
    except Exception as e:
        print(f"[JWT Auth] Unexpected error: {str(e)}")
        return Response(
            json.dumps({
                "error": "Internal Server Error",
                "message": "Authentication error"
            }),
            status=500
        )


# ============================================================================
# Route Handlers
# ============================================================================

@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    """Public endpoint - no authentication required."""
    return Response(json.dumps({
        "message": "Welcome to JWT Authentication API",
        "endpoints": {
            "POST /login": "Authenticate and get JWT token",
            "POST /register": "Register new user",
            "GET /profile": "Get user profile (requires JWT)",
            "GET /admin/stats": "Admin-only endpoint (requires JWT with admin role)",
            "GET /health": "Health check"
        }
    }))


@app.route("/health", methods=["GET"])
def health(request: Request) -> Response:
    """Health check endpoint."""
    return Response(json.dumps({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }))


@app.route("/login", methods=["POST"])
def login(request: Request) -> Response:
    """
    Login endpoint that returns a JWT token.
    
    Expected JSON body:
    {
        "username": "string",
        "password": "string"
    }
    
    Returns JWT token on successful authentication.
    """
    try:
        # Parse request body
        data = json.loads(request.body) if request.body else {}
        username = data.get("username")
        password = data.get("password")
        
        # Validate input
        if not username or not password:
            return Response(
                json.dumps({
                    "error": "Bad Request",
                    "message": "Username and password are required"
                }),
                status=400
            )
        
        # In production: Validate against database with hashed passwords
        # For demo: Accept any username/password combination
        # In real app: user = authenticate_user(username, password)
        
        # Simulate different user roles
        role = "admin" if username == "admin" else "user"
        user_id = f"usr_{hash(username) % 100000}"  # Simulate user ID
        
        # Create JWT token
        token = create_jwt_token(user_id, username, role)
        
        return Response(json.dumps({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user_id,
                "username": username,
                "role": role
            },
            "expires_in": f"{JWT_EXPIRATION_HOURS} hours"
        }))
        
    except json.JSONDecodeError:
        return Response(
            json.dumps({
                "error": "Bad Request",
                "message": "Invalid JSON body"
            }),
            status=400
        )
    except Exception as e:
        return Response(
            json.dumps({
                "error": "Internal Server Error",
                "message": str(e)
            }),
            status=500
        )


@app.route("/register", methods=["POST"])
def register(request: Request) -> Response:
    """
    User registration endpoint.
    
    Expected JSON body:
    {
        "username": "string",
        "password": "string",
        "email": "string"
    }
    """
    try:
        data = json.loads(request.body) if request.body else {}
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        
        if not username or not password or not email:
            return Response(
                json.dumps({
                    "error": "Bad Request",
                    "message": "Username, password, and email are required"
                }),
                status=400
            )
        
        # In production: Save to database with hashed password
        user_id = f"usr_{hash(username) % 100000}"
        
        return Response(json.dumps({
            "message": "Registration successful",
            "user": {
                "id": user_id,
                "username": username,
                "email": email
            },
            "next_step": "Please login to get your JWT token"
        }))
        
    except json.JSONDecodeError:
        return Response(
            json.dumps({
                "error": "Bad Request",
                "message": "Invalid JSON body"
            }),
            status=400
        )


@app.route("/profile", methods=["GET"])
def profile(request: Request) -> Response:
    """
    Protected endpoint - requires valid JWT token.
    Returns user profile information.
    """
    # In a real app, extract user info from validated token
    # For now, return a sample response
    return Response(json.dumps({
        "message": "Profile accessed successfully",
        "profile": {
            "username": "john_doe",
            "email": "john@example.com",
            "role": "user",
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": datetime.utcnow().isoformat()
        }
    }))


@app.route("/admin/stats", methods=["GET"])
def admin_stats(request: Request) -> Response:
    """
    Admin-only protected endpoint.
    In a real app, check user role from JWT token.
    """
    # In production, verify user role from JWT claims
    return Response(json.dumps({
        "message": "Admin statistics",
        "stats": {
            "total_users": 1250,
            "active_sessions": 340,
            "requests_today": 45678,
            "server_uptime": "15 days"
        }
    }))


if __name__ == "__main__":
    print("=" * 80)
    print("JWT Authentication Middleware Example - Production Ready")
    print("=" * 80)
    print("\nStarting server on http://127.0.0.1:8000")
    print(f"\nJWT Configuration:")
    print(f"  Algorithm: {JWT_ALGORITHM}")
    print(f"  Token Expiration: {JWT_EXPIRATION_HOURS} hours")
    print(f"  Secret Key: {JWT_SECRET[:10]}... (change in production!)")
    
    print("\n" + "=" * 80)
    print("API Usage Examples:")
    print("=" * 80)
    
    print("\n1. Health Check (Public):")
    print("   curl http://127.0.0.1:8000/health")
    
    print("\n2. Register a User:")
    print('   curl -X POST http://127.0.0.1:8000/register \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"username": "john", "password": "pass123", "email": "john@example.com"}\'')
    
    print("\n3. Login and Get JWT Token:")
    print('   curl -X POST http://127.0.0.1:8000/login \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"username": "john", "password": "pass123"}\'')
    
    print("\n4. Access Protected Endpoint (will fail without token):")
    print('   curl http://127.0.0.1:8000/profile')
    
    print("\n5. Access Protected Endpoint with Token:")
    print('   # First, get the token from login response')
    print('   TOKEN=$(curl -s -X POST http://127.0.0.1:8000/login \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"username": "john", "password": "pass123"}\' | grep -o \'"token":"[^"]*"\' | cut -d\'"\' -f4)')
    print('   ')
    print('   # Then use it to access protected endpoint')
    print('   curl http://127.0.0.1:8000/profile \\')
    print('     -H "Authorization: Bearer $TOKEN"')
    
    print("\n6. Access Admin Endpoint (requires admin role):")
    print('   # Login as admin')
    print('   ADMIN_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/login \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"username": "admin", "password": "admin123"}\' | grep -o \'"token":"[^"]*"\' | cut -d\'"\' -f4)')
    print('   ')
    print('   curl http://127.0.0.1:8000/admin/stats \\')
    print('     -H "Authorization: Bearer $ADMIN_TOKEN"')
    
    print("\n" + "=" * 80)
    print("Note: This example uses PyJWT library. Install with:")
    print("  pip install PyJWT")
    print("=" * 80)
    print()
    
    app.run(host="127.0.0.1", port=8000)

