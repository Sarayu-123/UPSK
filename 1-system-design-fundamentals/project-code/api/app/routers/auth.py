from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import create_access_token
from app.limiter import limiter

router = APIRouter()

@router.post("/login")
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    valid_credentials = {
        "admin@example.com": "password123",
        "user_b@example.com": "password123",
        "member@example.com": "password123",
        "viewer@example.com": "password123",
        "admin_user@example.com": "password123"
    }
    
    username = form_data.username
    password = form_data.password
    
    if username not in valid_credentials or valid_credentials[username] != password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password"
        )
    access_token = create_access_token(
        {"sub": username}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

