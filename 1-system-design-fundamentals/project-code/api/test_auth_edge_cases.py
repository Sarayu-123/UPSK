"""
Test auth behavior with edge cases.
This script verifies what happens when:
1. Authorization header is empty string
2. Authorization header is whitespace only
3. Authorization header is missing
4. jwt.decode() is called with empty token
"""

import jwt
import sys
from datetime import datetime, timedelta

# Test 1: What does jwt.decode("") do?
print("=" * 60)
print("TEST 1: jwt.decode with empty string")
print("=" * 60)

try:
    payload = jwt.decode(
        "",
        "test_secret",
        algorithms=["HS256"]
    )
    print(f"✗ PROBLEM: jwt.decode('') returned: {payload}")
except jwt.DecodeError as e:
    print(f"✓ GOOD: jwt.decode('') raised DecodeError: {e}")
except Exception as e:
    print(f"✓ GOOD: jwt.decode('') raised {type(e).__name__}: {e}")

# Test 2: What does jwt.decode(" ") do?
print("\n" + "=" * 60)
print("TEST 2: jwt.decode with whitespace-only string")
print("=" * 60)

try:
    payload = jwt.decode(
        " ",
        "test_secret",
        algorithms=["HS256"]
    )
    print(f"✗ PROBLEM: jwt.decode(' ') returned: {payload}")
except jwt.DecodeError as e:
    print(f"✓ GOOD: jwt.decode(' ') raised DecodeError: {e}")
except Exception as e:
    print(f"✓ GOOD: jwt.decode(' ') raised {type(e).__name__}: {e}")

# Test 3: What does jwt.decode(None) do?
print("\n" + "=" * 60)
print("TEST 3: jwt.decode with None")
print("=" * 60)

try:
    payload = jwt.decode(
        None,
        "test_secret",
        algorithms=["HS256"]
    )
    print(f"✗ PROBLEM: jwt.decode(None) returned: {payload}")
except TypeError as e:
    print(f"✓ EXPECTED: jwt.decode(None) raised TypeError: {e}")
except Exception as e:
    print(f"? jwt.decode(None) raised {type(e).__name__}: {e}")

# Test 4: Create a valid token and verify jwt.decode accepts it
print("\n" + "=" * 60)
print("TEST 4: Valid JWT token encoding/decoding")
print("=" * 60)

data = {"sub": "testuser"}
secret = "test_secret"
algo = "HS256"

token = jwt.encode(data, secret, algorithm=algo)
print(f"Generated token: {token[:50]}...")

try:
    payload = jwt.decode(token, secret, algorithms=[algo])
    print(f"✓ Successfully decoded: {payload}")
except Exception as e:
    print(f"✗ Failed to decode valid token: {e}")

# Test 5: What happens if we call jwt.decode with options={"verify_signature": False}
print("\n" + "=" * 60)
print("TEST 5: jwt.decode('') with verify_signature=False")
print("=" * 60)

try:
    payload = jwt.decode(
        "",
        secret,
        algorithms=[algo],
        options={"verify_signature": False}
    )
    print(f"✗ PROBLEM: jwt.decode('', options={...}) returned: {payload}")
except Exception as e:
    print(f"✓ GOOD: jwt.decode('', options={...}) raised {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("If all tests show jwt.decode() properly rejects empty/invalid tokens,")
print("then the auth bypass must be due to:")
print("  1. OAuth2PasswordBearer not being applied correctly")
print("  2. A different unprotected endpoint being called")
print("  3. Middleware/proxy bypassing auth checks")
print("=" * 60)
