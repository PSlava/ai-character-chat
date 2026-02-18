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
THUMB_DIMENSION = 160


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


def _save_with_thumb(img: Image.Image, avatars_dir: Path, filename: str) -> None:
    """Save full-size (512) and thumbnail (160) versions of avatar."""
    # Full size
    full = img.copy()
    full.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    buf = BytesIO()
    full.save(buf, format="WEBP", quality=85)
    (avatars_dir / filename).write_bytes(buf.getvalue())

    # Thumbnail
    thumb = img.copy()
    thumb.thumbnail((THUMB_DIMENSION, THUMB_DIMENSION), Image.LANCZOS)
    buf = BytesIO()
    thumb.save(buf, format="WEBP", quality=80)
    thumb_name = filename.replace(".webp", "_thumb.webp")
    (avatars_dir / thumb_name).write_bytes(buf.getvalue())


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

    # Save full + thumb as WebP (strips all EXIF by default)
    filename = f"{uuid.uuid4().hex}.webp"
    _save_with_thumb(img, _get_avatars_dir(), filename)

    return {"url": f"/api/uploads/avatars/{filename}"}


def _extract_api_error(e: Exception, provider: str) -> str:
    """Extract human-readable error message from API exception."""
    if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
        try:
            msg = e.response.json().get("error", {}).get("message", "")
            if msg:
                return f"{provider}: {msg}"
        except Exception:
            pass
        return f"{provider}: HTTP {e.response.status_code}"
    return f"{provider}: {str(e)[:200]}"


async def _generate_via_together(client: httpx.AsyncClient, prompt: str) -> bytes:
    """Generate image via Together AI (FLUX.1 schnell). Returns raw image bytes."""
    response = await client.post(
        "https://api.together.xyz/v1/images/generations",
        json={
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": prompt,
            "n": 1,
            "width": 1024,
            "height": 1024,
            "steps": 4,
            "response_format": "b64_json",
        },
        headers={
            "Authorization": f"Bearer {settings.together_api_key}",
            "Content-Type": "application/json",
        },
    )
    response.raise_for_status()
    b64 = response.json()["data"][0]["b64_json"]
    return base64.b64decode(b64)


async def _generate_via_dalle(client: httpx.AsyncClient, prompt: str) -> bytes:
    """Generate image via DALL-E 3. Returns raw image bytes."""
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
    return base64.b64decode(b64)


@router.post("/generate-avatar")
async def generate_avatar(
    prompt: str = Body(..., max_length=1000, embed=True),
    user=Depends(get_current_user),
):
    """Generate avatar via Together AI (FLUX.1) with DALL-E 3 fallback. Admin only."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    if not settings.together_api_key and not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="Avatar generation not available")

    filename = f"{uuid.uuid4().hex}.webp"

    client_kwargs: dict = {"timeout": 120}
    if settings.proxy_url:
        client_kwargs["proxy"] = settings.proxy_url

    errors: list[str] = []
    img_bytes = None
    provider = ""

    async with httpx.AsyncClient(**client_kwargs) as client:
        # Try Together AI first (FLUX.1 schnell — fast, cheap, no censorship)
        if settings.together_api_key and img_bytes is None:
            try:
                img_bytes = await _generate_via_together(client, prompt)
                provider = "together/FLUX.1-schnell"
            except Exception as e:
                err = _extract_api_error(e, "Together")
                errors.append(err)
                logger.warning("Together AI image gen failed: %s", err)

        # Fallback to DALL-E 3
        if settings.openai_api_key and img_bytes is None:
            try:
                img_bytes = await _generate_via_dalle(client, prompt)
                provider = "openai/dall-e-3"
            except Exception as e:
                err = _extract_api_error(e, "DALL-E")
                errors.append(err)
                logger.warning("DALL-E image gen failed: %s", err)

    if img_bytes is None:
        detail = "; ".join(errors) if errors else "No image generation provider available"
        raise HTTPException(status_code=502, detail=detail)

    try:
        img = Image.open(io.BytesIO(img_bytes))
        avatars_dir = _get_avatars_dir()
        _save_with_thumb(img, avatars_dir, filename)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to process generated image")

    logger.info("Avatar generated via %s: %s (%dKB)", provider, filename, (avatars_dir / filename).stat().st_size // 1024)
    return {"url": f"/api/uploads/avatars/{filename}"}
