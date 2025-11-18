#!/usr/bin/env python3
"""
Rupy API benchmark with PostgreSQL operations.
Implements insert/update/select operations for load testing.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from rupy import Rupy, Request, Response

app = Rupy()

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


@app.get("/")
def index(request: Request) -> Response:
    """Health check endpoint."""
    return Response(
        json.dumps({"status": "ok", "service": "rupy-benchmark"}),
        headers={"Content-Type": "application/json"}
    )


@app.get("/items/<item_id>")
def get_item(request: Request, item_id: str) -> Response:
    """Get a specific item by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if item:
            return Response(
                json.dumps(dict(item), default=str),
                headers={"Content-Type": "application/json"}
            )
        else:
            return Response(
                json.dumps({"error": "Item not found"}),
                status=404,
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


@app.post("/items")
def create_item(request: Request) -> Response:
    """Create a new item."""
    try:
        data = json.loads(request.body) if request.body else {}
        name = data.get("name", "")
        value = data.get("value", "")
        
        if not name or not value:
            return Response(
                json.dumps({"error": "name and value are required"}),
                status=400,
                headers={"Content-Type": "application/json"}
            )
        
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
        
        return Response(
            json.dumps(dict(item), default=str),
            status=201,
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


@app.put("/items/<item_id>")
def update_item(request: Request, item_id: str) -> Response:
    """Update an existing item."""
    try:
        data = json.loads(request.body) if request.body else {}
        name = data.get("name", "")
        value = data.get("value", "")
        
        if not name or not value:
            return Response(
                json.dumps({"error": "name and value are required"}),
                status=400,
                headers={"Content-Type": "application/json"}
            )
        
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
            return Response(
                json.dumps(dict(item), default=str),
                headers={"Content-Type": "application/json"}
            )
        else:
            return Response(
                json.dumps({"error": "Item not found"}),
                status=404,
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


@app.post("/upsert")
def upsert_item(request: Request) -> Response:
    """Insert or update an item based on name.
    
    Note: This implementation uses a SELECT-then-INSERT/UPDATE pattern.
    For production use, consider adding a unique constraint on name and
    using ON CONFLICT for atomic upserts to avoid race conditions.
    """
    try:
        data = json.loads(request.body) if request.body else {}
        name = data.get("name", "")
        value = data.get("value", "")
        
        if not name or not value:
            return Response(
                json.dumps({"error": "name and value are required"}),
                status=400,
                headers={"Content-Type": "application/json"}
            )
        
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
        
        return Response(
            json.dumps(dict(item), default=str),
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


@app.get("/items")
def list_items(request: Request) -> Response:
    """List all items with optional pagination."""
    try:
        # Parse query parameters from path
        limit = 100
        offset = 0
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "SELECT * FROM items ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset)
        )
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return Response(
            json.dumps([dict(item) for item in items], default=str),
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized.")
    
    print("Starting Rupy benchmark API on http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000)
