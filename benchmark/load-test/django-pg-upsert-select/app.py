#!/usr/bin/env python3
"""
Django REST Framework benchmark with PostgreSQL operations.
Implements insert/update/select operations for load testing.
Compatible with Rupy benchmark API.
"""

import os
import django
from django.conf import settings

import logging

logger = logging.getLogger("django-pg-upsert-select.app")
logging.basicConfig(level=logging.INFO)
# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY='benchmark-secret-key-not-for-production',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('DB_NAME', 'benchmark'),
                'USER': os.getenv('DB_USER', 'postgres'),
                'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
                'HOST': os.getenv('DB_HOST', 'postgres'),
                'PORT': os.getenv('DB_PORT', '5432'),
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'rest_framework',
        ],
        ROOT_URLCONF=__name__,
        MIDDLEWARE=[],
        ALLOWED_HOSTS=['*'],
    )
    django.setup()

from django.db import models, connection
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.urls import path
from django.core.wsgi import get_wsgi_application


def init_db():
    """Initialize database schema."""
    with connection.cursor() as cursor:
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


class ItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    value = serializers.CharField(max_length=255)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


@api_view(['GET'])
def index(request):
    """Health check endpoint."""
    return Response({"status": "ok", "service": "django-benchmark"})


@api_view(['GET'])
def list_items(request):
    """List all items with optional pagination."""
    try:
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM items ORDER BY id LIMIT %s OFFSET %s",
                [limit, offset]
            )
            columns = [col[0] for col in cursor.description]
            items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return Response(items)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_item(request, item_id):
    """Get a specific item by ID."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM items WHERE id = %s", [item_id])
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            
            if row:
                item = dict(zip(columns, row))
                return Response(item)
            else:
                return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception("Exception in get_item")
        return Response({"error": "An internal error has occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_item(request):
    """Create a new item."""
    try:
        data = request.data
        name = data.get('name', '')
        value = data.get('value', '')
        
        if not name or not value:
            return Response(
                {"error": "name and value are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO items (name, value) VALUES (%s, %s) RETURNING *",
                [name, value]
            )
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            item = dict(zip(columns, row))
        
        return Response(item, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception("Exception in create_item")
        return Response({"error": "An internal error has occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def update_item(request, item_id):
    """Update an existing item."""
    try:
        data = request.data
        name = data.get('name', '')
        value = data.get('value', '')
        
        if not name or not value:
            return Response(
                {"error": "name and value are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE items SET name = %s, value = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *",
                [name, value, item_id]
            )
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            
            if row:
                item = dict(zip(columns, row))
                return Response(item)
            else:
                return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception("Exception in update_item")
        return Response({"error": "An internal error has occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def upsert_item(request):
    """Insert or update an item based on name.
    
    Note: This implementation uses a SELECT-then-INSERT/UPDATE pattern.
    For production use, consider adding a unique constraint on name and
    using ON CONFLICT for atomic upserts to avoid race conditions.
    """
    try:
        data = request.data
        name = data.get('name', '')
        value = data.get('value', '')
        
        if not name or not value:
            return Response(
                {"error": "name and value are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with connection.cursor() as cursor:
            # Check if item exists and update or insert accordingly
            cursor.execute("SELECT * FROM items WHERE name = %s", [name])
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute(
                    "UPDATE items SET value = %s, updated_at = CURRENT_TIMESTAMP WHERE name = %s RETURNING *",
                    [value, name]
                )
            else:
                cursor.execute(
                    "INSERT INTO items (name, value) VALUES (%s, %s) RETURNING *",
                    [name, value]
                )
            
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            item = dict(zip(columns, row))
        
        return Response(item)
    except Exception as e:
        logger.exception("Exception in upsert_item")
        return Response({"error": "An internal error has occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# URL patterns
urlpatterns = [
    path('', index),
    path('items', list_items),
    path('items/', list_items),
    path('items/<int:item_id>', get_item),
    path('items/<int:item_id>/', get_item),
    path('upsert', upsert_item),
    path('upsert/', upsert_item),
]

# WSGI application
application = get_wsgi_application()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized.")
    
    print("Starting Django REST Framework benchmark API on http://0.0.0.0:8000")
    
    # Use gunicorn in production, but for testing we can use Django's dev server
    import sys
    from django.core.management import execute_from_command_line
    sys.argv = ['manage.py', 'runserver', '0.0.0.0:8000']
    execute_from_command_line(sys.argv)
