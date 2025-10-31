#!/usr/bin/env python3
"""
mrhttp benchmark with PostgreSQL operations.
Implements insert/update/select operations for load testing.
Compatible with Rupy benchmark API.

Note: mrhttp is a C extension for Python, providing high-performance HTTP handling.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import mrhttp

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "benchmark")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def init_db():
    """Initialize database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            value VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)
    """)
    
    conn.commit()
    cursor.close()
    conn.close()


def index(request):
    """Health check endpoint."""
    return json.dumps({"status": "ok", "service": "mrhttp-benchmark"})


def list_items(request):
    """List all items with optional pagination."""
    try:
        # Parse query params
        limit = 100
        offset = 0
        if 'limit' in request.args:
            limit = int(request.args['limit'])
        if 'offset' in request.args:
            offset = int(request.args['offset'])
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "SELECT * FROM items ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset)
        )
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return json.dumps([dict(item) for item in items], default=str)
    except Exception as e:
        request.status = 500
        return json.dumps({"error": str(e)})


def get_item(request, item_id):
    """Get a specific item by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if item:
            return json.dumps(dict(item), default=str)
        else:
            request.status = 404
            return json.dumps({"error": "Item not found"})
    except Exception as e:
        request.status = 500
        return json.dumps({"error": str(e)})


def create_item(request):
    """Create a new item."""
    try:
        data = json.loads(request.body) if request.body else {}
        name = data.get('name', '')
        value = data.get('value', '')
        
        if not name or not value:
            request.status = 400
            return json.dumps({"error": "name and value are required"})
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "INSERT INTO items (name, value) VALUES (%s, %s) RETURNING *",
            (name, value)
        )
        item = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        request.status = 201
        return json.dumps(dict(item), default=str)
    except Exception as e:
        request.status = 500
        return json.dumps({"error": str(e)})


def update_item(request, item_id):
    """Update an existing item."""
    try:
        data = json.loads(request.body) if request.body else {}
        name = data.get('name', '')
        value = data.get('value', '')
        
        if not name or not value:
            request.status = 400
            return json.dumps({"error": "name and value are required"})
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "UPDATE items SET name = %s, value = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *",
            (name, value, item_id)
        )
        item = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if item:
            return json.dumps(dict(item), default=str)
        else:
            request.status = 404
            return json.dumps({"error": "Item not found"})
    except Exception as e:
        request.status = 500
        return json.dumps({"error": str(e)})


def upsert_item(request):
    """Insert or update an item based on name.
    
    Note: This implementation uses a SELECT-then-INSERT/UPDATE pattern.
    For production use, consider adding a unique constraint on name and
    using ON CONFLICT for atomic upserts to avoid race conditions.
    """
    try:
        data = json.loads(request.body) if request.body else {}
        name = data.get('name', '')
        value = data.get('value', '')
        
        if not name or not value:
            request.status = 400
            return json.dumps({"error": "name and value are required"})
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if item exists and update or insert accordingly
        cursor.execute("SELECT * FROM items WHERE name = %s", (name,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE items SET value = %s, updated_at = CURRENT_TIMESTAMP WHERE name = %s RETURNING *",
                (value, name)
            )
        else:
            cursor.execute(
                "INSERT INTO items (name, value) VALUES (%s, %s) RETURNING *",
                (name, value)
            )
        
        item = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return json.dumps(dict(item), default=str)
    except Exception as e:
        request.status = 500
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized.")
    
    print("Starting mrhttp benchmark API on http://0.0.0.0:8000")
    
    # Create mrhttp app and register routes
    app = mrhttp.Server()
    
    # Register routes
    app.get("/", index)
    app.get("/items", list_items)
    app.get("/items/<item_id>", get_item)
    app.post("/items", create_item)
    app.put("/items/<item_id>", update_item)
    app.post("/upsert", upsert_item)
    
    # Start server
    app.run("0.0.0.0", 8000)
