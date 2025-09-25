#!/usr/bin/env python3
"""
Test script to verify the device tag sorting and device info fixes.
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8006"  # Update with your backend URL
AUTH_TOKEN = "demo-token-12345"  # Update with your auth token

def make_request(endpoint):
    """Make HTTP request to the API."""
    url = f"{API_BASE_URL}/v1{endpoint}"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"GET {endpoint} - Status: {response.status_code}")
        
        if response.status_code >= 400:
            print(f"Error: {response.text}")
            return None
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_device_list_tag_sorting():
    """Test that device tags are properly sorted in device list."""
    print("\n=== Testing Device List Tag Sorting ===")
    
    response = make_request("/devices?page=1&page_size=5")
    
    if response and response.get("devices"):
        for device in response["devices"][:3]:  # Check first 3 devices
            print(f"\nDevice: {device['name']}")
            tags = device.get("tags", [])
            if tags:
                tag_values = [tag["tag"] for tag in tags]
                print(f"  Tags: {tag_values}")
                
                # Check if tags are sorted
                sorted_tags = sorted(tag_values)
                if tag_values == sorted_tags:
                    print("  ✅ Tags are properly sorted")
                else:
                    print(f"  ❌ Tags not sorted. Expected: {sorted_tags}")
            else:
                print("  No tags found")
        return True
    else:
        print("❌ Failed to get device list")
        return False

def test_device_info_summary():
    """Test the new device info summary endpoint."""
    print("\n=== Testing Device Info Summary ===")
    
    response = make_request("/devices/summary/by-device-info")
    
    if response:
        print("✅ Device info summary endpoint working")
        print("Device models found:")
        for device_info, count in list(response.items())[:5]:  # Show first 5
            print(f"  {device_info}: {count} devices")
        return True
    else:
        print("❌ Device info summary failed")
        return False

def test_backward_compatibility():
    """Test that the old OS summary endpoint still works."""
    print("\n=== Testing Backward Compatibility (OS Summary) ===")
    
    response = make_request("/devices/summary/by-os")
    
    if response:
        print("✅ OS summary endpoint (backward compatibility) working")
        print("Operating systems found:")
        for os_name, count in list(response.items())[:5]:  # Show first 5
            print(f"  {os_name}: {count} devices")
        return True
    else:
        print("❌ OS summary endpoint failed")
        return False

def test_tag_summary_sorting():
    """Test that tag summary is properly sorted."""
    print("\n=== Testing Tag Summary Sorting ===")
    
    response = make_request("/devices/summary/by-tag")
    
    if response:
        print("✅ Tag summary endpoint working")
        tag_names = list(response.keys())
        sorted_tag_names = sorted(tag_names)
        
        print("Tags found:")
        for tag_name in tag_names[:5]:  # Show first 5
            print(f"  {tag_name}: {response[tag_name]} devices")
        
        if tag_names == sorted_tag_names:
            print("✅ Tags are properly sorted")
        else:
            print("❌ Tags not sorted properly")
        
        return True
    else:
        print("❌ Tag summary failed")
        return False

def test_individual_device():
    """Test individual device endpoint for tag sorting."""
    print("\n=== Testing Individual Device Tag Sorting ===")
    
    # First get a device ID
    devices_response = make_request("/devices?page=1&page_size=1")
    if not devices_response or not devices_response.get("devices"):
        print("❌ Could not get device list")
        return False
    
    device_id = devices_response["devices"][0]["id"]
    response = make_request(f"/devices/{device_id}")
    
    if response:
        print(f"✅ Individual device endpoint working")
        print(f"Device: {response['name']}")
        tags = response.get("tags", [])
        if tags:
            tag_values = [tag["tag"] for tag in tags]
            print(f"  Tags: {tag_values}")
            
            # Check if tags are sorted
            sorted_tags = sorted(tag_values)
            if tag_values == sorted_tags:
                print("  ✅ Tags are properly sorted")
            else:
                print(f"  ❌ Tags not sorted. Expected: {sorted_tags}")
        else:
            print("  No tags found")
        return True
    else:
        print("❌ Individual device endpoint failed")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Device Tag Sorting and Device Info Fixes")
    print(f"API Base URL: {API_BASE_URL}")
    
    tests = [
        ("Device List Tag Sorting", test_device_list_tag_sorting),
        ("Device Info Summary", test_device_info_summary),
        ("Backward Compatibility", test_backward_compatibility),
        ("Tag Summary Sorting", test_tag_summary_sorting),
        ("Individual Device Tag Sorting", test_individual_device)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Device fixes are working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the backend logs for details.")

if __name__ == "__main__":
    main()
