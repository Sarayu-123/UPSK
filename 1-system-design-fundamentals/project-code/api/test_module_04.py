import requests
import sys
import time

import random

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
BASE_URL = ""
SESSION_IP = f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}"

def test_unauthorized_access():
    print("Testing unauthorized POST /links...")
    resp = client.post(
        f"{BASE_URL}/links",
        json={"long_url": "https://google.com"},
        headers={"X-Forwarded-For": SESSION_IP}
    )
    print(f"Status Code: {resp.status_code}, Body: {resp.json()}")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    print("Unauthorized access check passed!")

def login(username, password):
    resp = client.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password},
        headers={"X-Forwarded-For": SESSION_IP}
    )
    if resp.status_code != 200:
        print(f"Login failed for {username}: {resp.status_code} - {resp.text}")
        sys.exit(1)
    return resp.json()["access_token"]

def flush_redis():
    try:
        import redis
        r = redis.from_url("redis://localhost:6379")
        r.flushdb()
        print("Redis rate limiter cache flushed.")
    except Exception as e:
        print(f"Warning: Failed to flush redis: {e}")

shared_code = None

def test_owner_scoping():
    global shared_code
    flush_redis()
    print("\n--- Testing Owner Scoping (IDOR Protection) ---")
    token_a = login("admin@example.com", "password123")
    token_b = login("user_b@example.com", "password123")
    
    # 1. User A creates a link
    headers_a = {
        "Authorization": f"Bearer {token_a}",
        "X-Forwarded-For": SESSION_IP
    }
    create_resp = client.post(
        f"{BASE_URL}/links",
        json={"long_url": "https://example.com/user_a_secret_page"},
        headers=headers_a
    )
    assert create_resp.status_code == 201, f"Expected 201, got {create_resp.status_code}"
    link_data = create_resp.json()
    link_id = link_data["id"]
    code = link_data["code"]
    print(f"User A created link: id={link_id}, code={code}")
    
    # 2. User B tries to retrieve User A's link by ID -> Expected: 404 Not Found (decision to hide existence)
    headers_b = {
        "Authorization": f"Bearer {token_b}",
        "X-Forwarded-For": SESSION_IP
    }
    get_resp = client.get(f"{BASE_URL}/links/{link_id}", headers=headers_b)
    print(f"User B trying to GET User A's link: Status={get_resp.status_code}, Body={get_resp.text}")
    assert get_resp.status_code == 404, f"Expected 404 for unauthorized access, got {get_resp.status_code}"
    
    # 3. User B tries to delete User A's link by ID -> Expected: 404 Not Found
    delete_resp = client.delete(f"{BASE_URL}/links/{link_id}", headers=headers_b)
    print(f"User B trying to DELETE User A's link: Status={delete_resp.status_code}, Body={delete_resp.text}")
    assert delete_resp.status_code == 404, f"Expected 404 for unauthorized delete, got {delete_resp.status_code}"
    
    # 4. User A retrieves their own link -> Expected: 200 OK
    get_a_resp = client.get(f"{BASE_URL}/links/{link_id}", headers=headers_a)
    print(f"User A retrieving their own link: Status={get_a_resp.status_code}")
    assert get_a_resp.status_code == 200, f"Expected 200, got {get_a_resp.status_code}"
    
    # 5. User A lists their links -> Expected to contain User A's link
    list_a_resp = client.get(f"{BASE_URL}/links", headers=headers_a)
    list_a_data = list_a_resp.json()
    assert any(l["id"] == link_id for l in list_a_data), "User A's link missing from User A's list"
    print("User A's list contains their own link.")
    
    # 6. User B lists their links -> Expected not to contain User A's link
    list_b_resp = client.get(f"{BASE_URL}/links", headers=headers_b)
    list_b_data = list_b_resp.json()
    assert not any(l["id"] == link_id for l in list_b_data), "User A's link leaked in User B's list!"
    print("User B's list does not contain User A's link (isolation works!).")
    
    shared_code = code
    print("Owner scoping checks passed!")

def test_rate_limiting_login():
    flush_redis()
    print("\n--- Testing Login Rate Limiting (10/minute) ---")
    # Send 12 requests in a row quickly to trip the limit
    triggered = False
    for i in range(1, 15):
        resp = client.post(
            f"{BASE_URL}/auth/login",
            data={"username": "admin@example.com", "password": "wrongpassword"}
        )
        print(f"Login request #{i}: Status Code={resp.status_code}")
        if resp.status_code == 429:
            print(f"Rate limit triggered successfully at request #{i}!")
            triggered = True
            break
    assert triggered, "Failed to trigger rate limit on login endpoint"

def test_rate_limiting_redirect():
    global shared_code
    if shared_code is None:
        test_owner_scoping()
    else:
        # flush redis so redirect requests start with 0 count
        flush_redis()
    code = shared_code
    print(f"\n--- Testing Redirect Rate Limiting (120/minute) on code {code} ---")
    # Send 130 requests to trigger the 120/minute rate limit
    triggered = False
    for i in range(1, 140):
        resp = client.get(f"{BASE_URL}/{code}", follow_redirects=False)
        if resp.status_code == 429:
            print(f"Rate limit triggered successfully at redirect request #{i}!")
            triggered = True
            break
    assert triggered, "Failed to trigger rate limit on redirect endpoint"

if __name__ == "__main__":
    test_unauthorized_access()
    test_owner_scoping()
    # Test rate limits (run separately to avoid blocking other calls)
    test_rate_limiting_login()
    test_rate_limiting_redirect()
    print("\nAll tests completed successfully!")
