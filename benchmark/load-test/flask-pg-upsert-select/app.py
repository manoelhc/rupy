#!/usr/bin/env python3
"""
Flask-RESTful benchmark with PostgreSQL operations.
Implements insert/update/select operations for load testing.
Compatible with Rupy benchmark API.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

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


class HealthCheck(Resource):
    """Health check endpoint."""
    def get(self):
        return {"status": "ok", "service": "flask-benchmark"}


class ItemList(Resource):
    """List all items or create a new item."""
    
    def get(self):
        """List all items with optional pagination."""
        try:
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                "SELECT * FROM items ORDER BY id LIMIT %s OFFSET %s",
                (limit, offset)
            )
            items = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(item) for item in items], 200
        except Exception as e:
            return {"error": str(e)}, 500
    
    def post(self):
        """Create a new item."""
        try:
            data = request.get_json() or {}
            name = data.get('name', '')
            value = data.get('value', '')
            
            if not name or not value:
                return {"error": "name and value are required"}, 400
            
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
            
            return dict(item), 201
        except Exception as e:
            return {"error": str(e)}, 500


class Item(Resource):
    """Get or update a specific item."""
    
    def get(self, item_id):
        """Get a specific item by ID."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
            item = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if item:
                return dict(item), 200
            else:
                return {"error": "Item not found"}, 404
        except Exception as e:
            return {"error": str(e)}, 500
    
    def put(self, item_id):
        """Update an existing item."""
        try:
            data = request.get_json() or {}
            name = data.get('name', '')
            value = data.get('value', '')
            
            if not name or not value:
                return {"error": "name and value are required"}, 400
            
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
                return dict(item), 200
            else:
                return {"error": "Item not found"}, 404
        except Exception as e:
            return {"error": str(e)}, 500


class Upsert(Resource):
    """Insert or update an item based on name."""
    
    def post(self):
        """Insert or update an item based on name.
        
        Note: This implementation uses a SELECT-then-INSERT/UPDATE pattern.
        For production use, consider adding a unique constraint on name and
        using ON CONFLICT for atomic upserts to avoid race conditions.
        """
        try:
            data = request.get_json() or {}
            name = data.get('name', '')
            value = data.get('value', '')
            
            if not name or not value:
                return {"error": "name and value are required"}, 400
            
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
            
            return dict(item), 200
        except Exception as e:
            return {"error": str(e)}, 500


# Add resources to API
api.add_resource(HealthCheck, '/')
api.add_resource(ItemList, '/items')
api.add_resource(Item, '/items/<int:item_id>')
api.add_resource(Upsert, '/upsert')


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized.")
    
    print("Starting Flask-RESTful benchmark API on http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
