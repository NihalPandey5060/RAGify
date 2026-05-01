#!/usr/bin/env python
"""
Test script for RAG API backend.
Tests all major endpoints: signup, login, upload, and query.
"""

import requests
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(success, message):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")


def test_health_check():
    """Test health check endpoint."""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        success = response.status_code == 200
        print_result(success, f"Health check: {response.json()}")
        return success
    except Exception as e:
        print_result(False, f"Health check failed: {e}")
        return False


def test_signup():
    """Test user signup."""
    print_section("2. User Signup")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            token = data.get("access_token")
            user_id = data.get("user", {}).get("id")
            print_result(success, f"Signup successful for {TEST_EMAIL}")
            print(f"  User ID: {user_id}")
            print(f"  Token (first 20 chars): {token[:20]}...")
            return token
        else:
            print_result(success, f"Signup failed: {response.json()}")
            return None
    except Exception as e:
        print_result(False, f"Signup failed: {e}")
        return None


def test_duplicate_signup():
    """Test that signing up with an existing email is rejected."""
    print_section("2b. Duplicate Signup")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        success = response.status_code == 400
        if success:
            print_result(success, f"Duplicate signup correctly rejected: {response.json()}")
            return True

        print_result(False, f"Unexpected duplicate signup response: {response.status_code} {response.text}")
        return False
    except Exception as e:
        print_result(False, f"Duplicate signup test failed: {e}")
        return False


def test_invalid_login():
    """Test invalid login is rejected."""
    print_section("3. Invalid Login")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": TEST_EMAIL, "password": "wrongpassword"}
        )
        success = response.status_code == 401
        if success:
            print_result(success, f"Invalid login correctly rejected: {response.json()}")
            return True

        print_result(False, f"Unexpected invalid login response: {response.status_code} {response.text}")
        return False
    except Exception as e:
        print_result(False, f"Invalid login test failed: {e}")
        return False


def test_get_user(token):
    """Test get current user."""
    print_section("4. Get Current User")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        success = response.status_code == 200
        if success:
            data = response.json()
            print_result(success, f"Retrieved user: {data['email']}")
            return success
        else:
            print_result(success, f"Get user failed: {response.json()}")
            return False
    except Exception as e:
        print_result(False, f"Get user failed: {e}")
        return False


def test_upload_document(token):
    """Test document upload."""
    print_section("5. Upload Document")
    
    # Look for a sample document
    pdf_path = Path("../data/BU_HR_Manual_.pdf")
    if not pdf_path.exists():
        print_result(False, f"Test PDF not found at {pdf_path}")
        print("  Please upload a PDF document manually or place one at ../data/BU_HR_Manual_.pdf")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        with open(pdf_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                headers=headers,
                files=files
            )
        
        success = response.status_code == 200
        if success:
            data = response.json()
            print_result(success, f"Document uploaded successfully")
            print(f"  Chunks created: {data['chunk_count']}")
            print(f"  Status: {data['status']}")
            return True
        else:
            print_result(success, f"Upload failed: {response.json()}")
            return False
    except Exception as e:
        print_result(False, f"Upload failed: {e}")
        return False


def test_query(token):
    """Test query endpoint."""
    print_section("6. Query Endpoint")
    
    query_text = "What is the annual leave policy?"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/query/ask",
            headers=headers,
            json={"query": query_text, "top_k": 3}
        )
        
        success = response.status_code == 200
        if success:
            data = response.json()
            print_result(success, f"Query processed successfully")
            print(f"  Question: {data['question']}")
            print(f"  Cache hit: {data['cache_hit']}")
            print(f"  Retrieved chunks: {len(data['retrieved_chunks'])}")
            if data['answer']:
                answer_preview = data['answer'][:100] + "..." if len(data['answer']) > 100 else data['answer']
                print(f"  Answer preview: {answer_preview}")
            return True
        else:
            print_result(success, f"Query failed: {response.json()}")
            return False
    except Exception as e:
        print_result(False, f"Query failed: {e}")
        return False


def test_query_streaming(token):
    """Test streaming query endpoint."""
    print_section("7. Streaming Query Endpoint")
    
    query_text = "What is the exit interview process?"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/query/ask-stream",
            headers=headers,
            json={"query": query_text, "top_k": 3},
            stream=True
        )
        
        success = response.status_code == 200
        if success:
            print_result(success, f"Streaming query started")
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    data = json.loads(line)
                    if data.get("type") == "retrieval_complete":
                        print(f"  Retrieval complete: {data.get('chunk_count')} chunks")
                    elif data.get("type") == "complete":
                        print(f"  Streaming complete")
            print(f"  Total chunks streamed: {chunk_count}")
            return True
        else:
            print_result(success, f"Streaming query failed: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Streaming query failed: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("  RAG API Backend Test Suite")
    print("="*60)
    print(f"\nTesting API at: {BASE_URL}")
    print("Make sure the backend is running: python -m uvicorn app.main:app --reload\n")
    
    # Run tests
    health_ok = test_health_check()
    if not health_ok:
        print("\n❌ Backend is not running. Start it with:")
        print("  python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    token = test_signup()
    if not token:
        print("\n❌ Signup failed. Cannot continue tests.")
        sys.exit(1)
    
    test_duplicate_signup()
    test_invalid_login()
    test_get_user(token)
    upload_ok = test_upload_document(token)
    
    if upload_ok:
        test_query(token)
        test_query_streaming(token)
    else:
        print("\n⚠️  Document upload failed. Query tests skipped.")
        print("Please upload a document manually and try again.")
    
    print_section("Test Summary")
    print("✅ Backend is operational!")
    print(f"\nAPI Documentation: http://localhost:8000/docs")
    print(f"Test user created: {TEST_EMAIL}")


if __name__ == "__main__":
    main()
