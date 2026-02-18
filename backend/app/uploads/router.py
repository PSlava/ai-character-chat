import base64
import io
import logging
import uuid
from io import BytesIO
from pathlib import Path

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File
from PIL import Image

from app.auth.middleware import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["uploads"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

# Magic byte signatures
_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"GIF8": "image/gif",
}

MAX_DIMENSION = 512


def _check_magic_bytes(data: bytes) -> str | None:
    """Return detected MIME type from magic bytes, or None."""
    for signature, mime in _MAGIC.items():
        if data[:len(signature)] == signature:
            return mime
    # WebP: starts with RIFF....WEBP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _get_avatars_dir() -> Path:
    d = Path(settings.upload_dir) / "avatars"
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP and GIF images are allowed")

    # Read file into memory
    data = await file.read()
    if len(data) > settings.max_avatar_size:
        mb = settings.max_avatar_size // (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"File too large (max {mb}MB)")

    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    # Validate magic bytes
    detected = _check_magic_bytes(data)
    if detected is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Process with Pillow — validates the image is real
    try:
        img = Image.open(BytesIO(data))
        img.load()  # Force decode to catch corrupted files
    except Exception:
        raise HTTPException(status_code=400, detail="Cannot read image file")

    # Convert RGBA/P to RGB for WebP compatibility
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Resize to max 512x512, preserving aspect ratio
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    # Save as WebP (strips all EXIF by default)
    filename = f"{uuid.uuid4().hex}.webp"
    out_path = _get_avatars_dir() / filename

    buf = BytesIO()
    img.save(buf, format="WEBP", quality=85)
    out_path.write_bytes(buf.getvalue())

    return {"url": f"/api/uploads/avatars/{filename}"}


@router.post("/generate-avatar")
async def generate_avatar(
    prompt: str = Body(..., max_length=1000, embed=True),
    user=Depends(get_current_user),
):
    """Generate avatar via DALL-E 3. Admin only."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="Avatar generation not available")

    filename = f"{uuid.uuid4().hex}.webp"
    filepath = _get_avatars_dir() / filename

    try:
        client_kwargs: dict = {"timeout": 120}
        if settings.proxy_url:
            client_kwargs["proxy"] = settings.proxy_url

        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "standard",
                    "response_format": "b64_json",
                },
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()

        b64 = response.json()["data"][0]["b64_json"]
        img_bytes = base64.b64decode(b64)

        img = Image.open(io.BytesIO(img_bytes))
        img = img.resize((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        img.save(filepath, "WEBP", quality=85)

        logger.info("Avatar generated: %s (%dKB)", filename, filepath.stat().st_size // 1024)
        return {"url": f"/api/uploads/avatars/{filename}"}

    except httpx.HTTPStatusError as e:
        body = e.response.text[:500] if e.response else ""
        logger.error("DALL-E API error %s: %s", e.response.status_code, body)
        # Return OpenAI error details to admin
        try:
            error_msg = e.response.json().get("error", {}).get("message", "")
        except Exception:
            error_msg = ""
        detail = error_msg or "Avatar generation failed"
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:
        logger.exception("Avatar generation failed: %s", str(e)[:200])
        raise HTTPException(status_code=500, detail="Avatar generation failed")
