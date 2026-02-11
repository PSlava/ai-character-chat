from datetime import datetime, timedelta
import secrets
import jwt
import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class RegisterRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=6, max_length=128)
    username: str | None = Field(default=None, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email format")
        return v.lower().strip()


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return _bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role or "user",
        "exp": datetime.utcnow() + timedelta(days=30),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _generate_username() -> str:
    return f"user_{secrets.token_hex(3)}"


def _is_admin_email(email: str) -> bool:
    admin_list = settings.admin_emails
    if not admin_list:
        return False
    return email.lower() in [e.strip().lower() for e in admin_list.split(",") if e.strip()]


@router.post("/register")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already taken")

    # Auto-generate username if not provided
    username = body.username
    if not username:
        for _ in range(10):
            candidate = _generate_username()
            check = await db.execute(select(User).where(User.username == candidate))
            if not check.scalar_one_or_none():
                username = candidate
                break
        else:
            username = f"user_{secrets.token_hex(6)}"
    else:
        # Check username uniqueness
        check = await db.execute(select(User).where(User.username == username))
        if check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")

    role = "admin" if _is_admin_email(body.email) else "user"
    user = User(
        email=body.email,
        username=username,
        display_name=username,
        password_hash=hash_password(body.password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_token(user)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "username": user.username, "language": user.language or "ru", "role": user.role or "user"},
    }


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Sync admin role from env (in case ADMIN_EMAILS changed)
    expected_role = "admin" if _is_admin_email(user.email) else "user"
    if (user.role or "user") != expected_role:
        user.role = expected_role
        await db.commit()
        await db.refresh(user)

    token = create_token(user)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "username": user.username, "language": user.language or "ru", "role": user.role or "user"},
    }
