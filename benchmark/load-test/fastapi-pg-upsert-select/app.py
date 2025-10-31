#!/usr/bin/env python3
"""
FastAPI benchmark with PostgreSQL operations.
Implements insert/update/select operations for load testing.
Compatible with Rupy benchmark API.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "benchmark")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


class Item(BaseModel):
    name: str
    value: str


class ItemResponse(BaseModel):
    id: int
    name: str
    value: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


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
def index():
    """Health check endpoint."""
    return {"status": "ok", "service": "fastapi-benchmark"}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    """Get a specific item by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if item:
            return dict(item)
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/items", status_code=201)
def create_item(item: Item):
    """Create a new item."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "INSERT INTO items (name, value) VALUES (%s, %s) RETURNING *",
            (item.name, item.value)
        )
        new_item = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return dict(new_item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    """Update an existing item."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "UPDATE items SET name = %s, value = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *",
            (item.name, item.value, item_id)
        )
        updated_item = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if updated_item:
            return dict(updated_item)
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upsert")
def upsert_item(item: Item):
    """Insert or update an item based on name.
    
    Note: This implementation uses a SELECT-then-INSERT/UPDATE pattern.
    For production use, consider adding a unique constraint on name and
    using ON CONFLICT for atomic upserts to avoid race conditions.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if item exists and update or insert accordingly
        cursor.execute("SELECT * FROM items WHERE name = %s", (item.name,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE items SET value = %s, updated_at = CURRENT_TIMESTAMP WHERE name = %s RETURNING *",
                (item.value, item.name)
            )
        else:
            cursor.execute(
                "INSERT INTO items (name, value) VALUES (%s, %s) RETURNING *",
                (item.name, item.value)
            )
        
        result_item = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return dict(result_item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/items")
def list_items(limit: int = 100, offset: int = 0):
    """List all items with optional pagination."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "SELECT * FROM items ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset)
        )
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [dict(item) for item in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized.")
    
    print("Starting FastAPI benchmark API on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
