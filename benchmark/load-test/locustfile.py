"""
Locust load testing script for Rupy and FastAPI benchmark.
This script can be used to test both implementations with the same workload.
"""

from locust import HttpUser, task, between
import random
import json


class BenchmarkUser(HttpUser):
    """Simulates a user performing various operations on the API."""
    
    wait_time = between(0.5, 2.0)  # Wait 0.5-2 seconds between tasks
    
    def on_start(self):
        """Called when a user starts. Initialize any needed data."""
        self.item_ids = []
        self.names = [f"item_{i}" for i in range(1000)]
    
    @task(3)
    def create_item(self):
        """Create a new item (30% of traffic)."""
        name = random.choice(self.names)
        value = f"value_{random.randint(1, 10000)}"
        
        response = self.client.post(
            "/items",
            json={"name": name, "value": value},
            headers={"Content-Type": "application/json"},
            name="/items [POST]"
        )
        
        if response.status_code == 201:
            try:
                data = response.json()
                item_id = data.get("id")
                if item_id:
                    self.item_ids.append(item_id)
            except:
                pass
    
    @task(5)
    def get_item(self):
        """Get an item by ID (50% of traffic)."""
        if self.item_ids:
            item_id = random.choice(self.item_ids)
            self.client.get(
                f"/items/{item_id}",
                name="/items/<id> [GET]"
            )
        else:
            # If no items created yet, try a random ID
            item_id = random.randint(1, 100)
            self.client.get(
                f"/items/{item_id}",
                name="/items/<id> [GET]"
            )
    
    @task(2)
    def update_item(self):
        """Update an existing item (20% of traffic)."""
        if self.item_ids:
            item_id = random.choice(self.item_ids)
            name = f"updated_{random.choice(self.names)}"
            value = f"updated_value_{random.randint(1, 10000)}"
            
            self.client.put(
                f"/items/{item_id}",
                json={"name": name, "value": value},
                headers={"Content-Type": "application/json"},
                name="/items/<id> [PUT]"
            )
    
    @task(2)
    def upsert_item(self):
        """Upsert an item (insert or update based on name) (20% of traffic)."""
        name = random.choice(self.names)
        value = f"upsert_value_{random.randint(1, 10000)}"
        
        self.client.post(
            "/upsert",
            json={"name": name, "value": value},
            headers={"Content-Type": "application/json"},
            name="/upsert [POST]"
        )
    
    @task(1)
    def list_items(self):
        """List items with pagination (10% of traffic)."""
        self.client.get(
            "/items",
            name="/items [GET]"
        )
    
    @task(1)
    def health_check(self):
        """Health check endpoint (10% of traffic)."""
        self.client.get(
            "/",
            name="/ [GET]"
        )


class RupyBenchmarkUser(BenchmarkUser):
    """User for testing Rupy API."""
    host = "http://localhost:8001"


class FastAPIBenchmarkUser(BenchmarkUser):
    """User for testing FastAPI."""
    host = "http://localhost:8002"
