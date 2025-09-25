#!/usr/bin/env python3
"""
Test script for Identity Agent API endpoints.

This script tests the agent communication endpoints to ensure they work correctly
with the backend API.
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import time

# Configuration
API_BASE_URL = "http://localhost:8006"  # Update with your backend URL
AUTH_TOKEN = "demo-token-12345"  # Update with your auth token

# Test data
DEVICE_ID = str(uuid.uuid4())
TEST_DEVICE_INFO = {
    "name": "TEST-LAPTOP-001",
    "hardware_uuid": str(uuid.uuid4()),
    "motherboard_serial": "MB123456789",
    "cpu_id": "CPU123456789",
    "mac_address": "00:11:22:33:44:55",
    "ip_address": "192.168.1.100",
    "os_version": "Windows 11 Pro",
    "manufacturer": "Dell Inc.",
    "model": "Latitude 7420",
    "agent_version": "1.0.0",
    "organization_id": "test-org",
    "fingerprint": "test-fingerprint-123"
}

def make_request(method, endpoint, data=None):
    """Make HTTP request to the API."""
    url = f"{API_BASE_URL}/v1{endpoint}"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"{method} {endpoint} - Status: {response.status_code}")
        
        if response.status_code >= 400:
            print(f"Error: {response.text}")
            return None
        
        try:
            return response.json()
        except:
            return response.text
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_agent_registration():
    """Test agent registration endpoint."""
    print("\n=== Testing Agent Registration ===")
    
    response = make_request("POST", "/agents/register", TEST_DEVICE_INFO)
    
    if response and response.get("success"):
        global DEVICE_ID
        DEVICE_ID = response.get("device_id")
        print(f"✅ Agent registered successfully")
        print(f"   Device ID: {DEVICE_ID}")
        print(f"   Correlation Status: {response.get('correlation_status')}")
        return True
    else:
        print("❌ Agent registration failed")
        return False

def test_heartbeat():
    """Test heartbeat endpoint."""
    print("\n=== Testing Heartbeat ===")
    
    heartbeat_data = {
        "device_id": DEVICE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "Running",
        "agent_version": "1.0.0",
        "ip_address": "192.168.1.100",
        "last_boot_time": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
        "system_uptime": "2:00:00",
        "config_hash": "abc123def456"
    }
    
    response = make_request("POST", "/agents/heartbeat", heartbeat_data)
    
    if response and response.get("success"):
        print("✅ Heartbeat sent successfully")
        print(f"   Next heartbeat: {response.get('next_heartbeat')}")
        return True
    else:
        print("❌ Heartbeat failed")
        return False

def test_event_reporting():
    """Test event reporting endpoint."""
    print("\n=== Testing Event Reporting ===")
    
    events_data = {
        "device_id": DEVICE_ID,
        "batch_timestamp": datetime.utcnow().isoformat() + "Z",
        "events": [
            {
                "id": str(uuid.uuid4()),
                "device_id": DEVICE_ID,
                "event_type": "LOGIN",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "event_data": {
                    "username": "john.doe",
                    "domain": "TESTDOMAIN",
                    "session_id": "12345",
                    "login_type": "Interactive",
                    "source_ip": "192.168.1.100",
                    "is_successful": True
                },
                "user_context": "TESTDOMAIN\\john.doe",
                "risk_score": 5,
                "correlation_id": str(uuid.uuid4())
            },
            {
                "id": str(uuid.uuid4()),
                "device_id": DEVICE_ID,
                "event_type": "PROCESS_START",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "event_data": {
                    "process_id": 1234,
                    "process_name": "notepad.exe",
                    "executable_path": "C:\\Windows\\System32\\notepad.exe",
                    "command_line": "notepad.exe test.txt",
                    "parent_process_id": 5678,
                    "username": "john.doe",
                    "file_hash": "sha256:abc123...",
                    "is_signed": True,
                    "publisher": "Microsoft Corporation"
                },
                "user_context": "TESTDOMAIN\\john.doe",
                "risk_score": 2
            }
        ]
    }
    
    response = make_request("POST", "/agents/events", events_data)
    
    if response and response.get("success"):
        print("✅ Events reported successfully")
        print(f"   Events processed: {response.get('events_processed')}")
        print(f"   Events failed: {response.get('events_failed')}")
        return True
    else:
        print("❌ Event reporting failed")
        return False

def test_discrepancy_reporting():
    """Test discrepancy reporting endpoint."""
    print("\n=== Testing Discrepancy Reporting ===")
    
    discrepancy_data = {
        "device_id": DEVICE_ID,
        "discrepancy_type": "USER_MISMATCH",
        "discrepancy_data": {
            "api_user": "john.smith@company.com",
            "agent_user": "jane.doe@company.com",
            "description": "API shows John Smith as device owner, but Jane Doe is actually logged in",
            "confidence": "high",
            "last_seen": datetime.utcnow().isoformat() + "Z"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent_version": "1.0.0"
    }
    
    response = make_request("POST", "/agents/discrepancies", discrepancy_data)
    
    if response and response.get("success"):
        print("✅ Discrepancy reported successfully")
        print(f"   Action: {response.get('action')}")
        return True
    else:
        print("❌ Discrepancy reporting failed")
        return False

def test_config_retrieval():
    """Test configuration retrieval endpoint."""
    print("\n=== Testing Configuration Retrieval ===")
    
    response = make_request("GET", f"/agents/{DEVICE_ID}/config")
    
    if response:
        print("✅ Configuration retrieved successfully")
        print(f"   Heartbeat interval: {response.get('heartbeat_interval_seconds')}s")
        print(f"   Real-time monitoring: {response.get('enable_real_time_monitoring')}")
        print(f"   Process monitoring: {response.get('enable_process_monitoring')}")
        return True
    else:
        print("❌ Configuration retrieval failed")
        return False

def test_health_check():
    """Test basic health check."""
    print("\n=== Testing Health Check ===")
    
    response = make_request("GET", "/health")
    
    if response:
        print("✅ Health check passed")
        return True
    else:
        print("❌ Health check failed")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Identity Agent API Tests")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Auth Token: {AUTH_TOKEN[:10]}...")
    
    tests = [
        ("Health Check", test_health_check),
        ("Agent Registration", test_agent_registration),
        ("Heartbeat", test_heartbeat),
        ("Event Reporting", test_event_reporting),
        ("Discrepancy Reporting", test_discrepancy_reporting),
        ("Configuration Retrieval", test_config_retrieval)
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
        
        # Small delay between tests
        time.sleep(1)
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Agent endpoints are working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the backend logs for details.")

if __name__ == "__main__":
    main()
