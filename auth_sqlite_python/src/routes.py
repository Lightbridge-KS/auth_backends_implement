from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone

from src.schemas import UserCreate, UserLogin, Token, User
from database import get_db_connection
from src.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register a new user"""
    conn = get_db_connection()

    # Check if user already exists
    existing_user = conn.execute(
        "SELECT username FROM users WHERE username = ?", (user_data.username,)
    ).fetchone()

    if existing_user:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Hash password and create user
    hashed_password = hash_password(user_data.password)

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)",
        (user_data.username, hashed_password, user_data.full_name),
    )

    conn.commit()
    conn.close()

    return {"message": "User registered successfully"}


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authenticate user and return access token"""
    from database import get_user_by_username

    user = get_user_by_username(user_credentials.username)

    if not user or not verify_password(
        user_credentials.password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Update last login
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?",
        (user_credentials.username,),
    )
    conn.commit()
    conn.close()

    # Create access token
    access_token = create_access_token(data={"sub": user["username"]})

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current user information"""
    return User(
        id=current_user["id"],
        username=current_user["username"],
        full_name=current_user["full_name"],
        created_at=current_user["created_at"],
        last_login=current_user["last_login"],
        is_active=bool(current_user["is_active"]),
    )


@router.get("/protected")
async def protected_route(current_user=Depends(get_current_user)):
    """Example protected route"""
    return {
        "message": f"Hello {current_user['username']}, this is a protected route!",
        "user_id": current_user["id"],
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}
