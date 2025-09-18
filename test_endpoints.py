#!/usr/bin/env python3
"""Test script to verify endpoints work with proper authentication"""

import requests
import json
import sys

# Default token from config
API_TOKEN = "demo-token-12345"

def get_base_url():
    """Get base URL from command line or use default"""
    if len(sys.argv) > 1:
        return sys.argv[1].rstrip('/')
    return "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def test_endpoint(base_url, endpoint, method="GET"):
    """Test a single endpoint"""
    url = f"{base_url}{endpoint}"
    print(f"Testing {method} {endpoint}...")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json={}, timeout=10)
        else:
            print(f"  ❌ Unsupported method: {method}")
            return
            
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✅ SUCCESS")
            # Show a preview of the response
            try:
                data = response.json()
                if isinstance(data, dict):
                    if 'total' in data:
                        print(f"     Total items: {data.get('total', 'N/A')}")
                    elif 'message' in data:
                        print(f"     Message: {data['message']}")
                elif isinstance(data, list):
                    print(f"     Items returned: {len(data)}")
            except:
                print(f"     Response: {response.text[:100]}...")
        elif response.status_code == 401:
            print(f"  ❌ UNAUTHORIZED - Check token")
        elif response.status_code == 404:
            print(f"  ❌ NOT FOUND - Route might not exist")
        elif response.status_code == 422:
            print(f"  ⚠️  VALIDATION ERROR - Check request format")
            try:
                error_data = response.json()
                print(f"     Details: {error_data}")
            except:
                pass
        else:
            print(f"  ⚠️  Status {response.status_code}: {response.text[:100]}")
            
    except requests.exceptions.ConnectionError:
        print(f"  ❌ CONNECTION ERROR - Server not running at {url}")
    except requests.exceptions.Timeout:
        print(f"  ❌ TIMEOUT - Server took too long to respond")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")

def test_without_auth(base_url, endpoint):
    """Test endpoint without authentication (should fail)"""
    url = f"{base_url}{endpoint}"
    print(f"Testing {endpoint} without auth...")
    
    try:
        response = requests.get(url, timeout=5)  # No headers
        print(f"  Status: {response.status_code}")
        if response.status_code == 401:
            print(f"  ✅ Correctly rejected unauthorized request")
        elif response.status_code == 403:
            print(f"  ✅ Correctly rejected unauthorized request (403)")
        else:
            print(f"  ⚠️  Unexpected response: {response.status_code}")
            print(f"     Response: {response.text[:100]}")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")

def main():
    base_url = get_base_url()
    
    print("API Endpoint Testing Tool")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print(f"Auth Token: {API_TOKEN}")
    print(f"Usage: python {sys.argv[0]} [base_url]")
    print(f"Example: python {sys.argv[0]} https://your-app.railway.app")
    print()
    
    # Test root endpoints first (no auth required)
    print("1. Testing Root Endpoints (No Auth Required):")
    print("-" * 30)
    test_endpoint(base_url, "/", "GET")
    test_endpoint(base_url, "/health", "GET")
    test_endpoint(base_url, "/readiness", "GET")
    test_endpoint(base_url, "/liveness", "GET")
    print()
    
    # Test main API endpoints with auth
    print("2. Testing API v1 Endpoints (Auth Required):")
    print("-" * 30)
    test_endpoint(base_url, "/api/v1/users", "GET")
    test_endpoint(base_url, "/api/v1/devices", "GET")
    test_endpoint(base_url, "/api/v1/policies", "GET")
    test_endpoint(base_url, "/api/v1/apis", "GET")
    test_endpoint(base_url, "/api/v1/history/config", "GET")
    print()
    
    # Test some summary endpoints
    print("3. Testing Summary Endpoints:")
    print("-" * 30)
    test_endpoint(base_url, "/api/v1/devices/summary/counts", "GET")
    test_endpoint(base_url, "/api/v1/policies/summary/by-type", "GET")
    test_endpoint(base_url, "/api/v1/apis/status/summary", "GET")
    print()
    
    # Test without authentication
    print("4. Testing Authentication (Should Fail):")
    print("-" * 30)
    test_without_auth(base_url, "/api/v1/users")
    print()
    
    print("Test Summary:")
    print("=" * 50)
    print("✅ = Success (200)")
    print("❌ = Error (401/404/Connection)")
    print("⚠️  = Warning (Other status)")
    print()
    print("If you see 404 errors on /api/v1/* endpoints:")
    print("1. Check that the server is running correctly")
    print("2. Verify the base URL is correct")
    print("3. Check server logs for import/startup errors")
    print()
    print("If you see 401 errors:")
    print("1. Make sure you're using the correct token")
    print("2. Check that DEMO_API_TOKEN env var is set correctly")

if __name__ == "__main__":
    main()
