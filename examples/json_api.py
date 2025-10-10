"""
JSON API Example - Demonstrates JSON request/response handling
"""
import sys
import os

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rupy import Rupy, Request, Response

app = Rupy(__name__)

# In-memory storage for demo
users = {
    "1": {"id": "1", "name": "Alice", "email": "alice@example.com"},
    "2": {"id": "2", "name": "Bob", "email": "bob@example.com"},
}

@app.route("/api/users", methods=["GET"])
async def list_users(request: Request) -> Response:
    """List all users"""
    return Response(list(users.values()))

@app.route("/api/users/<user_id>", methods=["GET"])
async def get_user(request: Request, user_id: str) -> Response:
    """Get a specific user"""
    user = users.get(user_id)
    if user:
        return Response(user)
    return Response({"error": "User not found"}, status=404)

@app.route("/api/users", methods=["POST"])
async def create_user(request: Request) -> Response:
    """Create a new user"""
    data = await request.json()
    
    # Simple validation
    if "name" not in data or "email" not in data:
        return Response({"error": "Missing required fields"}, status=400)
    
    # Generate new ID
    new_id = str(len(users) + 1)
    user = {
        "id": new_id,
        "name": data["name"],
        "email": data["email"]
    }
    users[new_id] = user
    
    return Response(user, status=201)

@app.route("/api/users/<user_id>", methods=["PUT"])
async def update_user(request: Request, user_id: str) -> Response:
    """Update an existing user"""
    if user_id not in users:
        return Response({"error": "User not found"}, status=404)
    
    data = await request.json()
    user = users[user_id]
    
    # Update fields
    if "name" in data:
        user["name"] = data["name"]
    if "email" in data:
        user["email"] = data["email"]
    
    return Response(user)

@app.route("/api/users/<user_id>", methods=["DELETE"])
async def delete_user(request: Request, user_id: str) -> Response:
    """Delete a user"""
    if user_id not in users:
        return Response({"error": "User not found"}, status=404)
    
    del users[user_id]
    return Response({"message": "User deleted"})

if __name__ == "__main__":
    print("Starting JSON API Example")
    print("Try these commands:")
    print("  curl http://localhost:8000/api/users")
    print("  curl http://localhost:8000/api/users/1")
    print('  curl -X POST http://localhost:8000/api/users -H "Content-Type: application/json" -d \'{"name": "Charlie", "email": "charlie@example.com"}\'')
    print("  curl -X PUT http://localhost:8000/api/users/1 -H \"Content-Type: application/json\" -d '{\"name\": \"Alice Smith\"}'")
    print("  curl -X DELETE http://localhost:8000/api/users/2")
    print()
    app.run(host="0.0.0.0", port=8000)
