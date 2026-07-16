"""
Minimal FastAPI app to test OAuth2PasswordBearer behavior.
This tests what actually happens when Authorization: "" is sent.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.testclient import TestClient
import jwt

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Mimics app/auth.py get_current_user"""
    print(f"  [DEBUG] get_current_user called with token: {repr(token)}")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(
            token,
            "test_secret",
            algorithms=["HS256"]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.ExpiredSignatureError:
        print("  [DEBUG] ExpiredSignatureError caught")
        raise credentials_exception
    except jwt.PyJWTError as e:
        print(f"  [DEBUG] PyJWTError caught: {type(e).__name__}: {e}")
        raise credentials_exception

@app.delete("/links/{link_id}", status_code=204)
async def delete_short_link(
    link_id: int,
    current_user: str = Depends(get_current_user)
):
    """Mimics the DELETE endpoint"""
    print(f"  [DEBUG] delete_short_link called with user={current_user}")
    return None  # 204 response

# Test it
client = TestClient(app)

print("=" * 70)
print("TEST 1: No Authorization header")
print("=" * 70)
response = client.delete("/links/1")
print(f"Status: {response.status_code}")
print(f"Body: {response.json() if response.text else '(no body)'}")

print("\n" + "=" * 70)
print("TEST 2: Authorization: \"\" (empty string)")
print("=" * 70)
response = client.delete("/links/1", headers={"Authorization": ""})
print(f"Status: {response.status_code}")
print(f"Body: {response.json() if response.text else '(no body)'}")

print("\n" + "=" * 70)
print("TEST 3: Authorization: \" \" (whitespace only)")
print("=" * 70)
response = client.delete("/links/1", headers={"Authorization": " "})
print(f"Status: {response.status_code}")
print(f"Body: {response.json() if response.text else '(no body)'}")

print("\n" + "=" * 70)
print("TEST 4: Authorization: Bearer (no token)")
print("=" * 70)
response = client.delete("/links/1", headers={"Authorization": "Bearer"})
print(f"Status: {response.status_code}")
print(f"Body: {response.json() if response.text else '(no body)'}")

print("\n" + "=" * 70)
print("TEST 5: Authorization: Bearer (with space but no token)")
print("=" * 70)
response = client.delete("/links/1", headers={"Authorization": "Bearer "})
print(f"Status: {response.status_code}")
print(f"Body: {response.json() if response.text else '(no body)'}")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)
print("""
If any of Tests 1-5 returned 204 (success), that would explain the alert.
That would mean the auth check was bypassed somehow.

If all returned 401/403, then the auth is working correctly,
and the vulnerability must be elsewhere (e.g., different route, middleware).
""")
