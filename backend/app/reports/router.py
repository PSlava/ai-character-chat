from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_user
from app.auth.rate_limit import RateLimiter
from app.db.session import get_db
from app.db.models import Report, Character, User

from app.reports.schemas import CreateReportRequest, UpdateReportRequest

router = APIRouter(tags=["reports"])

# 5 reports per hour per user
report_limiter = RateLimiter(max_requests=5, window_seconds=3600)


async def require_admin(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Verify admin role from DB, not just JWT claims."""
    result = await db.execute(select(User).where(User.id == user["id"]))
    db_user = result.scalar_one_or_none()
    if not db_user or (db_user.role or "user") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.post("/api/characters/{character_id}/report", status_code=201)
async def create_report(
    character_id: str,
    body: CreateReportRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Rate limit
    if not report_limiter.check(f"report:{user['id']}"):
        raise HTTPException(status_code=429, detail="Too many reports. Try again later.")

    # Check character exists
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Check no duplicate pending report from same user for same character
    existing = await db.execute(
        select(Report).where(
            Report.reporter_id == user["id"],
            Report.character_id == character_id,
            Report.status == "pending",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You already have a pending report for this character")

    report = Report(
        reporter_id=user["id"],
        character_id=character_id,
        reason=body.reason,
        details=body.details,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return {
        "id": report.id,
        "character_id": report.character_id,
        "reason": report.reason,
        "details": report.details,
        "status": report.status,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.get("/api/admin/reports")
async def list_reports(
    status: str | None = None,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(Report).order_by(Report.created_at.desc())
    if status:
        q = q.where(Report.status == status)

    result = await db.execute(q)
    reports = result.scalars().all()

    items = []
    for r in reports:
        # Fetch reporter info
        reporter_result = await db.execute(select(User).where(User.id == r.reporter_id))
        reporter = reporter_result.scalar_one_or_none()
        # Fetch character info
        char_result = await db.execute(select(Character).where(Character.id == r.character_id))
        character = char_result.scalar_one_or_none()

        items.append({
            "id": r.id,
            "reason": r.reason,
            "details": r.details,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "reporter": {
                "id": reporter.id,
                "username": reporter.username,
            } if reporter else None,
            "character": {
                "id": character.id,
                "name": character.name,
                "slug": character.slug,
                "avatar_url": character.avatar_url,
            } if character else None,
        })

    return items


@router.put("/api/admin/reports/{report_id}")
async def update_report(
    report_id: str,
    body: UpdateReportRequest,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = body.status
    await db.commit()
    await db.refresh(report)

    return {
        "id": report.id,
        "status": report.status,
    }
