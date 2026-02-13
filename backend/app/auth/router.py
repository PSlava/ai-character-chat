from datetime import datetime, timedelta
import secrets
import jwt
import bcrypt as _bcrypt
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.rate_limit import check_auth_rate, check_reset_rate
from app.utils.email import send_reset_email
import logging

from authlib.integrations.starlette_client import OAuth as AuthlibOAuth
from starlette.responses import RedirectResponse

from app.config import settings
from app.db.session import get_db
from app.db.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

_oauth = AuthlibOAuth()
if settings.google_client_id:
    _oauth.register(
        name='google',
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )


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


class ForgotPasswordRequest(BaseModel):
    email: str = Field(max_length=254)


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=6, max_length=128)


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return _bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role or "user",
        "exp": datetime.utcnow() + timedelta(days=7),
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
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    check_auth_rate(request)
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
        "user": {"id": user.id, "email": user.email, "username": user.username, "language": user.language or "en", "role": user.role or "user"},
    }


@router.post("/login")
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    check_auth_rate(request)
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if getattr(user, 'is_banned', False):
        raise HTTPException(status_code=403, detail="Account is banned")

    # Sync admin role from env (in case ADMIN_EMAILS changed)
    expected_role = "admin" if _is_admin_email(user.email) else "user"
    if (user.role or "user") != expected_role:
        user.role = expected_role
        await db.commit()
        await db.refresh(user)

    token = create_token(user)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "username": user.username, "language": user.language or "en", "role": user.role or "user"},
    }


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    email = body.email.lower().strip()
    check_reset_rate(request, email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user and user.password_hash:
        # HMAC of password hash — changes when password is reset, but never exposes hash
        import hashlib, hmac as _hmac
        pwd_fingerprint = _hmac.new(
            settings.jwt_secret.encode(), user.password_hash.encode(), hashlib.sha256
        ).hexdigest()[:16]
        reset_payload = {
            "sub": user.id,
            "purpose": "reset",
            "pfp": pwd_fingerprint,
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        reset_token = jwt.encode(reset_payload, settings.jwt_secret, algorithm="HS256")
        reset_url = f"{settings.frontend_url}/auth/reset-password?token={reset_token}"

        try:
            await send_reset_email(user.email, reset_url)
        except Exception:
            logging.getLogger(__name__).exception("Failed to send reset email")

    return {"message": "If this email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    check_auth_rate(request)

    try:
        payload = jwt.decode(body.token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset link has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid reset link")

    if payload.get("purpose") != "reset":
        raise HTTPException(status_code=400, detail="Invalid reset link")

    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset link")

    # Verify password fingerprint — ensures token is invalidated after password change
    import hashlib, hmac as _hmac
    if not user.password_hash:
        raise HTTPException(status_code=400, detail="This reset link has already been used")
    expected_pfp = _hmac.new(
        settings.jwt_secret.encode(), user.password_hash.encode(), hashlib.sha256
    ).hexdigest()[:16]
    if expected_pfp != payload.get("pfp"):
        raise HTTPException(status_code=400, detail="This reset link has already been used")

    user.password_hash = hash_password(body.password)
    await db.commit()

    return {"message": "Password has been reset successfully"}


@router.get("/providers")
async def auth_providers():
    return {"google": bool(settings.google_client_id)}


@router.get("/google")
async def google_login(request: Request):
    if not settings.google_client_id:
        raise HTTPException(status_code=404, detail="Google OAuth is not configured")
    redirect_uri = f"{settings.frontend_url}/api/auth/google/callback"
    return await _oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.google_client_id:
        raise HTTPException(status_code=404, detail="Google OAuth is not configured")

    try:
        token = await _oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=400, detail="OAuth authentication failed")

    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(status_code=400, detail="Could not retrieve user info from Google")

    email = userinfo.get("email", "").lower().strip()
    oauth_id = userinfo.get("sub")
    name = userinfo.get("name") or email.split("@")[0]

    if not email or not oauth_id:
        raise HTTPException(status_code=400, detail="Missing email or ID from Google")

    # Find existing user by oauth_id or email
    result = await db.execute(
        select(User).where(User.oauth_provider == "google", User.oauth_id == oauth_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Check if user with this email already exists (link accounts)
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            # Link existing account to Google
            user.oauth_provider = "google"
            user.oauth_id = oauth_id
            await db.commit()
            await db.refresh(user)

    if not user:
        # Create new user
        username = None
        for _ in range(10):
            candidate = _generate_username()
            check = await db.execute(select(User).where(User.username == candidate))
            if not check.scalar_one_or_none():
                username = candidate
                break
        if not username:
            username = f"user_{secrets.token_hex(6)}"

        role = "admin" if _is_admin_email(email) else "user"
        user = User(
            email=email,
            username=username,
            display_name=name,
            oauth_provider="google",
            oauth_id=oauth_id,
            role=role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if getattr(user, 'is_banned', False):
        raise HTTPException(status_code=403, detail="Account is banned")

    # Sync admin role
    expected_role = "admin" if _is_admin_email(user.email) else "user"
    if (user.role or "user") != expected_role:
        user.role = expected_role
        await db.commit()
        await db.refresh(user)

    jwt_token = create_token(user)

    params = urlencode({
        "token": jwt_token,
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role or "user",
    })
    redirect_url = f"{settings.frontend_url}/auth/oauth-callback?{params}"
    return RedirectResponse(url=redirect_url)
