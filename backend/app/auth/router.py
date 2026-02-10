from datetime import datetime, timedelta
import secrets
import jwt
import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str | None = None  # auto-generated if not provided


class LoginRequest(BaseModel):
    email: str
    password: str


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

    user = User(
        email=body.email,
        username=username,
        display_name=username,
        password_hash=hash_password(body.password),
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

    token = create_token(user)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "username": user.username, "language": user.language or "ru", "role": user.role or "user"},
    }
