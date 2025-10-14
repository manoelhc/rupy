#!/usr/bin/env python3
"""
RESTful API example demonstrating all HTTP methods (GET, POST, PUT, PATCH, DELETE).
This example simulates a simple items management API.
"""

from rupy import Rupy, Request, Response

app = Rupy()

# In-memory storage (for demonstration purposes)
items = {
    "1": {"id": "1", "name": "Item 1", "status": "active"},
    "2": {"id": "2", "name": "Item 2", "status": "active"},
}


@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("RESTful API Demo. Try /items")


@app.route("/items", methods=["GET"])
def list_items(request: Request) -> Response:
    """List all items"""
    items_list = ", ".join([f"{k}: {v['name']}" for k, v in items.items()])
    return Response(f"Items: {items_list}")


@app.route("/items/<item_id>", methods=["GET"])
def get_item(request: Request, item_id: str) -> Response:
    """Get a specific item"""
    if item_id in items:
        item = items[item_id]
        return Response(f"Item {item_id}: {item['name']} (status: {item['status']})")
    return Response(f"Item {item_id} not found", 404)


@app.route("/items", methods=["POST"])
def create_item(request: Request) -> Response:
    """Create a new item"""
    # In a real app, you would parse JSON here
    new_id = str(len(items) + 1)
    items[new_id] = {"id": new_id, "name": f"Item {new_id}", "status": "active"}
    return Response(f"Created item {new_id} with data: {request.body}", 201)


@app.route("/items/<item_id>", methods=["PUT"])
def update_item(request: Request, item_id: str) -> Response:
    """Replace an item entirely"""
    if item_id in items:
        items[item_id] = {"id": item_id, "name": "Updated Item", "status": "active"}
        return Response(f"Updated item {item_id} with: {request.body}")
    return Response(f"Item {item_id} not found", 404)


@app.route("/items/<item_id>", methods=["PATCH"])
def patch_item(request: Request, item_id: str) -> Response:
    """Partially update an item"""
    if item_id in items:
        # In a real app, you would apply partial updates from request.body
        items[item_id]["status"] = "updated"
        return Response(f"Patched item {item_id} with: {request.body}")
    return Response(f"Item {item_id} not found", 404)


@app.route("/items/<item_id>", methods=["DELETE"])
def delete_item(request: Request, item_id: str) -> Response:
    """Delete an item"""
    if item_id in items:
        del items[item_id]
        return Response(f"Deleted item {item_id}")
    return Response(f"Item {item_id} not found", 404)


if __name__ == "__main__":
    print("Starting RESTful API on http://127.0.0.1:8000")
    print("\nExample requests:")
    print("  # List all items")
    print("  curl http://127.0.0.1:8000/items")
    print("\n  # Get specific item")
    print("  curl http://127.0.0.1:8000/items/1")
    print("\n  # Create new item")
    print('  curl -X POST -d \'{"name": "New Item"}\' http://127.0.0.1:8000/items')
    print("\n  # Update item")
    print('  curl -X PUT -d \'{"name": "Updated"}\' http://127.0.0.1:8000/items/1')
    print("\n  # Patch item")
    print('  curl -X PATCH -d \'{"status": "inactive"}\' http://127.0.0.1:8000/items/1')
    print("\n  # Delete item")
    print("  curl -X DELETE http://127.0.0.1:8000/items/1")
    app.run(host="127.0.0.1", port=8000)
