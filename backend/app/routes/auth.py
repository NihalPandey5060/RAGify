from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.models import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services import auth as auth_service
from app.dependencies import get_current_user
from app.db import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_response(user_info: dict) -> UserResponse:
    """Map internal user fields to the public response schema."""
    return UserResponse(
        id=user_info["user_id"],
        email=user_info["email"],
        created_at=user_info["created_at"],
    )


@router.post("/signup", response_model=TokenResponse)
async def signup(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and return access token."""
    try:
        user_info = auth_service.register_user(user_create.email, user_create.password, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    token = auth_service.create_access_token(user_info["email"], user_info["user_id"])
    
    return TokenResponse(
        access_token=token,
        user=_to_user_response(user_info)
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    user_info = auth_service.authenticate_user(user_login.email, user_login.password, db)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token = auth_service.create_access_token(user_info["email"], user_info["user_id"])
    
    return TokenResponse(
        access_token=token,
        user=_to_user_response(user_info)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information (requires authentication)."""
    user_info = auth_service.get_user(current_user["email"], db)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return _to_user_response(user_info)
