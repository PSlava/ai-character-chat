"""Daily cleanup — old page_views + orphan avatar files."""

import logging
from pathlib import Path

from sqlalchemy import text

from app.config import settings
from app.db.session import engine as db_engine

logger = logging.getLogger("autonomous")


async def run_cleanup():
    """Run all cleanup tasks."""
    await _cleanup_old_page_views()
    await _cleanup_orphan_avatars()


async def _cleanup_old_page_views():
    """Delete page_views older than 90 days."""
    try:
        async with db_engine.begin() as conn:
            result = await conn.execute(
                text("DELETE FROM page_views WHERE created_at < NOW() - INTERVAL '90 days'")
            )
            deleted = result.rowcount
            if deleted:
                logger.info("Cleaned up %d old page views", deleted)
    except Exception:
        logger.exception("Page views cleanup failed")


async def _cleanup_orphan_avatars():
    """Delete avatar files that aren't referenced by any character or user."""
    try:
        avatars_dir = Path(settings.upload_dir) / "avatars"
        if not avatars_dir.exists():
            return

        # Get all referenced avatar filenames from DB (+ their thumbnails)
        referenced = set()
        async with db_engine.connect() as conn:
            # Character avatars
            result = await conn.execute(
                text("SELECT avatar_url FROM characters WHERE avatar_url IS NOT NULL")
            )
            for row in result.fetchall():
                url = row[0]
                if url:
                    # Extract filename from /api/uploads/avatars/filename.webp
                    parts = url.rsplit("/", 1)
                    if len(parts) == 2:
                        referenced.add(parts[1])
                        # Also keep thumbnail variant
                        referenced.add(parts[1].replace(".webp", "_thumb.webp"))

            # User avatars
            result = await conn.execute(
                text("SELECT avatar_url FROM users WHERE avatar_url IS NOT NULL")
            )
            for row in result.fetchall():
                url = row[0]
                if url:
                    parts = url.rsplit("/", 1)
                    if len(parts) == 2:
                        referenced.add(parts[1])
                        referenced.add(parts[1].replace(".webp", "_thumb.webp"))

        # Find and delete orphans
        deleted = 0
        for filepath in avatars_dir.iterdir():
            if filepath.is_file() and filepath.name not in referenced:
                # Don't delete seed avatars (00.webp, 01.webp, etc.)
                if filepath.suffix == ".webp" and not filepath.stem.isdigit():
                    filepath.unlink()
                    deleted += 1

        if deleted:
            logger.info("Cleaned up %d orphan avatar files", deleted)

    except Exception:
        logger.exception("Orphan avatar cleanup failed")
