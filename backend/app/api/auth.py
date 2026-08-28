"""
Authentication API Endpoints — register, login, me, forgot/reset password.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
import secrets
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.config import settings
from ..core.ratelimit import limiter, AUTH_RATE_LIMIT
from ..core.security import hash_password, verify_password, create_access_token, require_auth
from ..models import User

logger = logging.getLogger(__name__)


def _send_reset_email(to_email: str, token: str) -> None:
    """Send password reset email via SMTP, or log to console if SMTP is not configured."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    if not settings.SMTP_HOST or not settings.SMTP_USER:
        # Dev fallback: log the link so it can be used without email setup
        logger.warning(
            "SMTP not configured — password reset link (DEV ONLY): %s", reset_url
        )
        return

    subject = "Reset your password for Rehnuma"
    body = f"""Hi,

You requested a password reset for your Rehnuma account (University of Karachi admissions assistant).

Click the link below to set a new password (valid for 1 hour):

{reset_url}

If you did not request this, please ignore this email.

Rehnuma, University of Karachi admissions assistant
"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
            smtp.sendmail(msg["From"], to_email, msg.as_string())
    except Exception as exc:
        # Never surface SMTP errors to the caller — just log
        logger.error("Failed to send password reset email to %s: %s", to_email, exc)

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
@limiter.limit(AUTH_RATE_LIMIT)
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    If admin_key matches ADMIN_REGISTRATION_KEY the account gets role="admin".
    Otherwise role="user". The admin_key is never stored or returned.
    """
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    role = "user"
    if payload.admin_key and payload.admin_key == settings.ADMIN_REGISTRATION_KEY:
        role = "admin"

    user = User(
        id=str(uuid.uuid4()),
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return AuthResponse(access_token=token, role=user.role)


@router.post("/auth/login", response_model=AuthResponse)
@limiter.limit(AUTH_RATE_LIMIT)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    """Login and receive a JWT access token."""
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return AuthResponse(access_token=token, role=user.role)


@router.get("/auth/me", response_model=UserProfile)
def me(current_user: User = Depends(require_auth)):
    """Return the current authenticated user's profile."""
    return UserProfile(id=current_user.id, email=current_user.email, role=current_user.role)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/auth/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request a password reset link.

    Always returns 200 regardless of whether the email exists,
    to prevent user enumeration.
    """
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        _send_reset_email(user.email, token)

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/auth/reset-password", status_code=status.HTTP_200_OK)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a valid (unexpired) reset token."""
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    user = db.query(User).filter(
        User.reset_token == request.token,
        User.reset_token_expires > datetime.utcnow(),
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    user.password_hash = hash_password(request.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password reset successfully."}
