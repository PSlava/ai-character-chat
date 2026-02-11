import uuid
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from PIL import Image

from app.auth.middleware import get_current_user
from app.config import settings

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
        raise HTTPException(status_code=400, detail="File too large (max 2MB)")

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
