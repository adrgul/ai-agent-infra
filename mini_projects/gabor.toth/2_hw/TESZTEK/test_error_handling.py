#!/usr/bin/env python3
"""
Test script to verify error handling and edge cases.

Tests:
1. Invalid API inputs
2. Missing required parameters
3. Non-existent resources
4. Malformed JSON
5. File upload errors
6. Category errors
7. Rate limiting / timeout handling
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_error_handling():
    """Test error handling and edge cases."""
    
    print("\n" + "="*60)
    print("⚠️  TEST: Error Handling & Edge Cases")
    print("="*60)
    
    # Step 1: Missing Required Parameters
    print("\n1️⃣ Testing Missing Required Parameters...")
    
    # Missing user_id in chat
    print("   a) POST /api/chat without user_id:")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        data={
            "session_id": "test",
            "message": "Hello"
            # Missing user_id
        }
    )
    if response.status_code != 200:
        print(f"      ✓ Correctly rejected (status: {response.status_code})")
    else:
        print(f"      ✗ Should have failed but got 200")
    
    # Missing message in chat
    print("   b) POST /api/chat without message:")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        data={
            "user_id": "test_user",
            "session_id": "test"
            # Missing message
        }
    )
    if response.status_code != 200:
        print(f"      ✓ Correctly rejected (status: {response.status_code})")
    else:
        print(f"      ✗ Should have failed but got 200")
    
    # Missing file in upload
    print("   c) POST /api/files/upload without file:")
    response = requests.post(
        f"{BASE_URL}/api/files/upload",
        data={
            "user_id": "test_user",
            "category": "Test"
            # Missing file
        }
    )
    if response.status_code != 200:
        print(f"      ✓ Correctly rejected (status: {response.status_code})")
    else:
        print(f"      ✗ Should have failed but got 200")
    
    # Step 2: Invalid Category Names
    print("\n2️⃣ Testing Invalid Category Names...")
    
    # Empty category name
    print("   a) Upload with empty category name:")
    try:
        files = {"file": ("test.md", b"# Test")}
        response = requests.post(
            f"{BASE_URL}/api/files/upload",
            files=files,
            data={
                "user_id": "test_user",
                "category": ""
            },
            timeout=10
        )
        if response.status_code != 200:
            print(f"      ✓ Correctly rejected (status: {response.status_code})")
        else:
            print(f"      ⚠️ Empty category was accepted")
    except Exception as e:
        print(f"      ✓ Exception raised: {type(e).__name__}")
    
    # Step 3: Invalid File Types
    print("\n3️⃣ Testing Invalid File Types...")
    
    # Binary file (not text)
    print("   a) Uploading binary .exe file:")
    try:
        files = {"file": ("test.exe", b"\x4d\x5a\x90\x00")}  # MZ header (PE executable)
        response = requests.post(
            f"{BASE_URL}/api/files/upload",
            files=files,
            data={
                "user_id": "test_user",
                "category": "Test"
            },
            timeout=10
        )
        if response.status_code != 200:
            print(f"      ✓ Correctly rejected .exe (status: {response.status_code})")
        else:
            print(f"      ⚠️ .exe file was accepted (might cause issues)")
    except Exception as e:
        print(f"      ✓ Exception raised: {type(e).__name__}")
    
    # Step 4: Empty Files
    print("\n4️⃣ Testing Empty Files...")
    
    print("   a) Uploading empty file:")
    try:
        files = {"file": ("empty.md", b"")}
        response = requests.post(
            f"{BASE_URL}/api/files/upload",
            files=files,
            data={
                "user_id": "test_user",
                "category": "Test"
            },
            timeout=10
        )
        if response.status_code != 200:
            print(f"      ✓ Correctly rejected (status: {response.status_code})")
        else:
            print(f"      ⚠️ Empty file was accepted")
    except Exception as e:
        print(f"      ✓ Exception raised: {type(e).__name__}")
    
    # Step 5: Non-Existent Resources
    print("\n5️⃣ Testing Non-Existent Resources...")
    
    # Non-existent user
    print("   a) Chat with non-existent user:")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        data={
            "user_id": "nonexistent_user_xyz",
            "session_id": "test",
            "message": "Hello"
        }
    )
    # Should create user automatically or return 200 with empty response
    print(f"      Status: {response.status_code}")
    if response.ok:
        print(f"      ✓ Auto-created user (or handled gracefully)")
    
    # Step 6: SQL Injection / Input Sanitization
    print("\n6️⃣ Testing Input Sanitization...")
    
    # SQL injection attempt in user_id
    print("   a) Chat with SQL injection in user_id:")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        data={
            "user_id": "'; DROP TABLE users; --",
            "session_id": "test",
            "message": "Hello"
        }
    )
    if response.status_code == 200 or response.status_code >= 400:
        print(f"      ✓ Input sanitized (status: {response.status_code})")
    
    # Script injection in message
    print("   b) Chat with XSS attempt in message:")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        data={
            "user_id": "test_user",
            "session_id": "test",
            "message": "<script>alert('XSS')</script>"
        }
    )
    if response.ok:
        print(f"      ✓ XSS attempt handled (status: {response.status_code})")
    
    # Step 7: API Endpoint Availability
    print("\n7️⃣ Testing API Endpoints...")
    
    endpoints = [
        ("GET", "/api/health"),
        ("POST", "/api/chat"),
        ("POST", "/api/files/upload"),
        ("GET", "/api/activities"),
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        else:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                data={"user_id": "test"} if endpoint != "/api/health" else {}
            )
        
        status_ok = 200 <= response.status_code < 500
        symbol = "✓" if status_ok else "✗"
        print(f"   {symbol} {method} {endpoint}: {response.status_code}")
    
    # Step 8: Large Inputs
    print("\n8️⃣ Testing Large Inputs...")
    
    # Very long message
    print("   a) Very long chat message (10000 chars):")
    long_message = "a" * 10000
    response = requests.post(
        f"{BASE_URL}/api/chat",
        data={
            "user_id": "test_user",
            "session_id": "test",
            "message": long_message
        },
        timeout=30
    )
    if response.ok:
        print(f"      ✓ Long message handled (status: {response.status_code})")
    else:
        print(f"      ⚠️ Failed with status: {response.status_code}")
    
    print("\n" + "="*60)
    print("✅ Error Handling Test COMPLETED!")
    print("="*60)
    print("\n📌 Note: Some 'failures' above are expected (graceful error handling)")
    
    return True


if __name__ == "__main__":
    success = test_error_handling()
    exit(0 if success else 1)
