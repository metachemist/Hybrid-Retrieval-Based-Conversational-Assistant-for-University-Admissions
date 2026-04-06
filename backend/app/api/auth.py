"""
Authentication API Endpoints — register, login, me.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from ..core.database import get_db
from ..core.config import settings
from ..core.security import hash_password, verify_password, create_access_token, require_auth
from ..models import User

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    admin_key: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserProfile(BaseModel):
    id: str
    email: str
    role: str


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    If admin_key matches ADMIN_REGISTRATION_KEY the account gets role="admin".
    Otherwise role="user". The admin_key is never stored or returned.
    """
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    role = "user"
    if request.admin_key and request.admin_key == settings.ADMIN_REGISTRATION_KEY:
        role = "admin"

    user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        password_hash=hash_password(request.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role})
    return AuthResponse(access_token=token, role=user.role)


@router.post("/auth/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login and receive a JWT access token."""
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": user.id, "role": user.role})
    return AuthResponse(access_token=token, role=user.role)


@router.get("/auth/me", response_model=UserProfile)
def me(current_user: User = Depends(require_auth)):
    """Return the current authenticated user's profile."""
    return UserProfile(id=current_user.id, email=current_user.email, role=current_user.role)
