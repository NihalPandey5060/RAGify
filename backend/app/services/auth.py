import os
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
from secrets import token_bytes
from jose import JWTError, jwt
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db import User

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC SHA-256.

    Format: pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>
    This avoids the 72-byte password limit and works for long passwords.
    """
    if password is None:
        raise ValueError("password is required")

    iterations = 200_000
    salt = token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii")
    hash_b64 = base64.urlsafe_b64encode(derived).decode("ascii")
    return f"pbkdf2_sha256${iterations}${salt_b64}${hash_b64}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a PBKDF2-HMAC hash."""
    try:
        algorithm, iterations_str, salt_b64, hash_b64 = hashed_password.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_str)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(hash_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_access_token(email: str, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": email, "user_id": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if email is None or user_id is None:
            return None
        return {"email": email, "user_id": user_id}
    except JWTError:
        return None


def register_user(email: str, password: str, db: Session) -> dict:
    """Register a new user in SQLite."""
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError("User already exists")

    user = User(
        id=str(uuid4()),
        email=email,
        hashed_password=hash_password(password),
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "email": user.email, "created_at": user.created_at}


def authenticate_user(email: str, password: str, db: Session) -> Optional[dict]:
    """Authenticate user and return user info if valid."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return {"user_id": user.id, "email": user.email, "created_at": user.created_at}


def get_user(email: str, db: Session) -> Optional[dict]:
    """Get user by email."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    return {"user_id": user.id, "email": user.email, "created_at": user.created_at}
