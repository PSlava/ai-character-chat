"""Campaign and game API routes (fiction mode only)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.middleware import get_current_user
from app.db.session import get_db
from app.db.models import Campaign, CampaignSession, Chat, Character, DiceRoll
from app.game.dice import roll as dice_roll

router = APIRouter(prefix="/api", tags=["game"])


# ── Schemas ──────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    description: str | None = None
    character_id: str  # story/adventure template
    system: str = "dnd5e"


class RollRequest(BaseModel):
    expression: str


# ── Campaigns ────────────────────────────────────────────

@router.post("/campaigns")
async def create_campaign(
    body: CampaignCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new campaign."""
    # Verify character exists
    result = await db.execute(select(Character).where(Character.id == body.character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    campaign = Campaign(
        creator_id=user["id"],
        name=body.name,
        description=body.description,
        system=body.system,
    )
    db.add(campaign)
    await db.flush()

    # Auto-create first session
    chat = Chat(
        user_id=user["id"],
        character_id=body.character_id,
        campaign_id=campaign.id,
    )
    db.add(chat)
    await db.flush()

    session = CampaignSession(
        campaign_id=campaign.id,
        chat_id=chat.id,
        number=1,
    )
    db.add(session)
    await db.commit()

    return {
        "id": campaign.id,
        "name": campaign.name,
        "description": campaign.description,
        "system": campaign.system,
        "status": campaign.status,
        "session": {
            "id": session.id,
            "chat_id": chat.id,
            "number": 1,
        },
    }


@router.get("/campaigns")
async def list_campaigns(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's campaigns."""
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.sessions))
        .where(Campaign.creator_id == user["id"])
        .order_by(Campaign.created_at.desc())
    )
    campaigns = result.scalars().all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "system": c.system,
            "status": c.status,
            "session_count": len(c.sessions),
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in campaigns
    ]


@router.get("/campaigns/recent")
async def recent_campaigns(
    limit: int = 3,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return user's most recently active campaigns with character info."""
    from sqlalchemy import desc

    # Get active campaigns with their latest session
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.sessions))
        .where(Campaign.creator_id == user["id"], Campaign.status == "active")
        .order_by(desc(Campaign.created_at))
        .limit(limit)
    )
    campaigns = result.scalars().all()

    items = []
    for c in campaigns:
        if not c.sessions:
            continue
        latest_session = max(c.sessions, key=lambda s: s.number)
        if not latest_session.chat_id:
            continue

        # Get chat with character
        chat_result = await db.execute(
            select(Chat)
            .options(selectinload(Chat.character))
            .where(Chat.id == latest_session.chat_id)
        )
        chat = chat_result.scalar_one_or_none()
        if not chat:
            continue

        items.append({
            "id": c.id,
            "name": c.name,
            "character_name": chat.character.name if chat.character else None,
            "character_avatar_url": chat.character.avatar_url if chat.character else None,
            "session_number": latest_session.number,
            "chat_id": chat.id,
            "last_played": chat.updated_at.isoformat() if chat.updated_at else c.created_at.isoformat(),
        })
    return items


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get campaign details with sessions."""
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.sessions))
        .where(Campaign.id == campaign_id, Campaign.creator_id == user["id"])
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    sessions = sorted(campaign.sessions, key=lambda s: s.number)
    return {
        "id": campaign.id,
        "name": campaign.name,
        "description": campaign.description,
        "system": campaign.system,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "sessions": [
            {
                "id": s.id,
                "chat_id": s.chat_id,
                "number": s.number,
                "summary": s.summary,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
    }


@router.post("/campaigns/{campaign_id}/sessions")
async def create_session(
    campaign_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new session in a campaign."""
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.sessions))
        .where(Campaign.id == campaign_id, Campaign.creator_id == user["id"])
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Find the character from the first session's chat
    first_session = min(campaign.sessions, key=lambda s: s.number) if campaign.sessions else None
    if not first_session or not first_session.chat_id:
        raise HTTPException(status_code=400, detail="Campaign has no initial session")

    chat_result = await db.execute(select(Chat).where(Chat.id == first_session.chat_id))
    first_chat = chat_result.scalar_one_or_none()
    if not first_chat:
        raise HTTPException(status_code=400, detail="Initial session chat not found")

    next_number = max(s.number for s in campaign.sessions) + 1

    chat = Chat(
        user_id=user["id"],
        character_id=first_chat.character_id,
        campaign_id=campaign.id,
    )
    db.add(chat)
    await db.flush()

    session = CampaignSession(
        campaign_id=campaign.id,
        chat_id=chat.id,
        number=next_number,
    )
    db.add(session)
    await db.commit()

    # Award XP for starting a new session
    try:
        from app.users.xp import award_xp
        await award_xp(user["id"], 15)
    except Exception:
        pass

    return {
        "id": session.id,
        "chat_id": chat.id,
        "number": next_number,
    }


@router.delete("/campaigns/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a campaign and all its sessions."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.creator_id == user["id"])
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await db.delete(campaign)
    await db.commit()


# ── Dice Rolling ─────────────────────────────────────────

@router.post("/game/roll")
async def roll_dice(
    body: RollRequest,
    user=Depends(get_current_user),
):
    """Roll dice with a D&D expression."""
    try:
        result = dice_roll(body.expression)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result.to_dict()


# ── Encounter State ──────────────────────────────────────

@router.get("/chats/{chat_id}/encounter-state")
async def get_encounter_state(
    chat_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get encounter state for a campaign chat."""
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user["id"])
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"encounter_state": chat.encounter_state}
