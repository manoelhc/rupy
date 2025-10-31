#!/usr/bin/env python3
"""
Quick test script to verify both APIs are working correctly.
This script tests both Rupy and FastAPI implementations.
"""

import requests
import json
import sys
import time

def test_api(base_url, api_name):
    """Test an API endpoint with basic operations."""
    print(f"\n{'='*60}")
    print(f"Testing {api_name} at {base_url}")
    print('='*60)
    
    errors = []
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"✓ Health check passed: {data}")
    except Exception as e:
        errors.append(f"Health check failed: {e}")
        print(f"✗ Health check failed: {e}")
    
    # Test 2: Create an item
    item_id = None
    try:
        payload = {"name": "test-item", "value": "test-value"}
        response = requests.post(
            f"{base_url}/items",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = response.json()
        item_id = data.get("id")
        assert item_id is not None, "No ID returned"
        print(f"✓ Create item passed: ID={item_id}")
    except Exception as e:
        errors.append(f"Create item failed: {e}")
        print(f"✗ Create item failed: {e}")
    
    # Test 3: Get the created item
    if item_id:
        try:
            response = requests.get(f"{base_url}/items/{item_id}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert data.get("id") == item_id, "ID mismatch"
            assert data.get("name") == "test-item", "Name mismatch"
            print(f"✓ Get item passed: {data.get('name')}")
        except Exception as e:
            errors.append(f"Get item failed: {e}")
            print(f"✗ Get item failed: {e}")
    
    # Test 4: Update the item
    if item_id:
        try:
            payload = {"name": "updated-item", "value": "updated-value"}
            response = requests.put(
                f"{base_url}/items/{item_id}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert data.get("name") == "updated-item", "Name not updated"
            print(f"✓ Update item passed: {data.get('name')}")
        except Exception as e:
            errors.append(f"Update item failed: {e}")
            print(f"✗ Update item failed: {e}")
    
    # Test 5: Upsert an item
    try:
        payload = {"name": "upsert-test", "value": "upsert-value"}
        response = requests.post(
            f"{base_url}/upsert",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("name") == "upsert-test", "Upsert failed"
        print(f"✓ Upsert item passed: {data.get('name')}")
    except Exception as e:
        errors.append(f"Upsert item failed: {e}")
        print(f"✗ Upsert item failed: {e}")
    
    # Test 6: List items
    try:
        response = requests.get(f"{base_url}/items")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list"
        print(f"✓ List items passed: {len(data)} items")
    except Exception as e:
        errors.append(f"List items failed: {e}")
        print(f"✗ List items failed: {e}")
    
    # Summary
    print(f"\n{api_name} Test Summary:")
    if errors:
        print(f"✗ {len(errors)} test(s) failed")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✓ All tests passed!")
        return True


def wait_for_service(url, timeout=30):
    """Wait for a service to be ready."""
    print(f"Waiting for service at {url}...", end='', flush=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print(" Ready!")
                return True
        except:
            pass
        time.sleep(1)
        print(".", end='', flush=True)
    print(" Timeout!")
    return False


def main():
    """Main test runner."""
    print("API Compatibility Test Suite")
    print("="*60)
    
    # Check if services are available
    apis = [
        ("Rupy", "http://localhost:8001"),
        ("FastAPI", "http://localhost:8002"),
        ("Django", "http://localhost:8003"),
        ("Flask", "http://localhost:8004"),
        ("Robyn", "http://localhost:8005"),
        ("mrhttp", "http://localhost:8006"),
    ]
    
    results = []
    any_ready = False
    
    for api_name, api_url in apis:
        if wait_for_service(api_url):
            any_ready = True
            results.append((api_name, test_api(api_url, f"{api_name} API")))
    
    if not any_ready:
        print("\nError: No APIs are available.")
        print("Please start the services with: docker-compose up")
        sys.exit(1)
    
    # Final summary
    print(f"\n{'='*60}")
    print("Final Test Summary")
    print('='*60)
    for api_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{api_name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n✓ All APIs passed compatibility tests!")
        sys.exit(0)
    else:
        print("\n✗ Some APIs failed compatibility tests.")
        sys.exit(1)


if __name__ == "__main__":
    main()
