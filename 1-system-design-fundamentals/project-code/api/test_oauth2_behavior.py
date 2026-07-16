"""
Test OAuth2PasswordBearer behavior with edge cases.
This tests the actual FastAPI security mechanism without needing a full app.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

# Simulate the FastAPI setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """This is what app/auth.py does"""
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
        raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

# Now test what OAuth2PasswordBearer actually does
print("=" * 70)
print("Testing FastAPI OAuth2PasswordBearer behavior")
print("=" * 70)

# OAuth2PasswordBearer is a dependency that extracts the token from the 
# Authorization header. Let's trace what it would do:

print("\n1. Authorization: Bearer <valid-token>")
print("   OAuth2PasswordBearer extracts: '<valid-token>'")
print("   Expected result: Passed to jwt.decode()")

print("\n2. Authorization: \"\" (empty string)")
print("   OAuth2PasswordBearer behavior with empty header value:")
print("   - IMPORTANT: It depends on how the HTTP framework parses it")
print("   - If header exists but is empty, OAuth2PasswordBearer might:")
print("     a) Return empty string '' to the dependency")
print("     b) Raise 403 Forbidden immediately")
print("   - We need to test this empirically")

print("\n3. Authorization: \" \" (whitespace only)")
print("   Similar issue as #2")

print("\n4. No Authorization header")
print("   OAuth2PasswordBearer: Raises HTTPException(403)")
print("   → Request returns 401/403, NOT 200")

print("\n" + "=" * 70)
print("KEY INSIGHT")
print("=" * 70)
print("""
The vulnerability described in the scenario hinges on this:

If OAuth2PasswordBearer passes an empty string to get_current_user(),
then jwt.decode("") will raise jwt.DecodeError, which is caught and
converted to HTTPException(401).

So the DELETE should return 401, not 200.

UNLESS:
1. The DELETE endpoint doesn't actually use Depends(get_current_user)
2. There's a different DELETE route that IS unprotected
3. OAuth2PasswordBearer has a framework-specific bug
4. Middleware is intercepting and removing the auth check
""")

# Let's check the actual FastAPI source to understand better
print("\n" + "=" * 70)
print("TESTING: What does JWT decode do with empty string?")
print("=" * 70)

import jwt as pyjwt

try:
    result = pyjwt.decode("", "secret", algorithms=["HS256"])
    print(f"✗ jwt.decode('') returned: {result}")
except pyjwt.PyJWTError as e:
    print(f"✓ jwt.decode('') raised {type(e).__name__}: {e}")
    print(f"  This error WILL be caught by get_current_user()")
    print(f"  → Returns HTTPException(401)")
