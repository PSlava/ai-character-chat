"""Achievement checker — runs after user actions, returns newly unlocked achievements."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserAchievement, Chat, Message, MessageRole
from app.achievements.definitions import ACHIEVEMENTS


async def _has(db: AsyncSession, user_id: str, achievement_id: str) -> bool:
    result = await db.execute(
        select(UserAchievement.id).where(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id,
        )
    )
    return result.scalar() is not None


async def _unlock(db: AsyncSession, user_id: str, achievement_id: str) -> bool:
    """Unlock achievement if not already unlocked. Returns True if newly unlocked."""
    if await _has(db, user_id, achievement_id):
        return False
    db.add(UserAchievement(user_id=user_id, achievement_id=achievement_id))
    await db.flush()
    return True


async def check_achievements(db: AsyncSession, user_id: str, trigger: str = "message") -> list[str]:
    """Check and unlock achievements for user. Returns list of newly unlocked achievement IDs.

    trigger: "message" | "rating" | "regenerate"
    """
    newly_unlocked = []

    # first_adventure: has at least 1 chat
    if not await _has(db, user_id, "first_adventure"):
        chat_count = (await db.execute(
            select(func.count()).select_from(Chat).where(Chat.user_id == user_id)
        )).scalar() or 0
        if chat_count >= 1:
            if await _unlock(db, user_id, "first_adventure"):
                newly_unlocked.append("first_adventure")

    # five_adventures: 5 distinct chats
    if not await _has(db, user_id, "five_adventures"):
        chat_count = (await db.execute(
            select(func.count()).select_from(Chat).where(Chat.user_id == user_id)
        )).scalar() or 0
        if chat_count >= 5:
            if await _unlock(db, user_id, "five_adventures"):
                newly_unlocked.append("five_adventures")

    # bookworm: 100 user messages
    if not await _has(db, user_id, "bookworm"):
        msg_count = (await db.execute(
            select(func.count()).select_from(Message)
            .join(Chat, Message.chat_id == Chat.id)
            .where(Chat.user_id == user_id, Message.role == MessageRole.user)
        )).scalar() or 0
        if msg_count >= 100:
            if await _unlock(db, user_id, "bookworm"):
                newly_unlocked.append("bookworm")

    # storyteller: 500 user messages
    if not await _has(db, user_id, "storyteller"):
        if "bookworm" in newly_unlocked or await _has(db, user_id, "bookworm"):
            msg_count = (await db.execute(
                select(func.count()).select_from(Message)
                .join(Chat, Message.chat_id == Chat.id)
                .where(Chat.user_id == user_id, Message.role == MessageRole.user)
            )).scalar() or 0
            if msg_count >= 500:
                if await _unlock(db, user_id, "storyteller"):
                    newly_unlocked.append("storyteller")

    # first_rating / five_ratings — only check on rating trigger
    if trigger == "rating":
        rating_count = (await db.execute(
            select(func.count()).select_from(Chat)
            .where(Chat.user_id == user_id, Chat.rating.isnot(None))
        )).scalar() or 0
        if rating_count >= 1 and not await _has(db, user_id, "first_rating"):
            if await _unlock(db, user_id, "first_rating"):
                newly_unlocked.append("first_rating")
        if rating_count >= 5 and not await _has(db, user_id, "five_ratings"):
            if await _unlock(db, user_id, "five_ratings"):
                newly_unlocked.append("five_ratings")

    # dice_roller: 20 messages with dice_rolls
    if trigger == "message" and not await _has(db, user_id, "dice_roller"):
        dice_count = (await db.execute(
            select(func.count()).select_from(Message)
            .join(Chat, Message.chat_id == Chat.id)
            .where(Chat.user_id == user_id, Message.dice_rolls.isnot(None))
        )).scalar() or 0
        if dice_count >= 20:
            if await _unlock(db, user_id, "dice_roller"):
                newly_unlocked.append("dice_roller")

    # fate_rewriter: tracked via is_regenerate messages count
    # We check regenerations by counting assistant messages that have is_regenerate=True
    # Since we don't track this separately, we'll check if user has enough regenerated messages
    # This is approximated: we skip for now and track via frontend counter in future

    await db.commit()
    return newly_unlocked


async def get_user_achievements(db: AsyncSession, user_id: str) -> list[dict]:
    """Get all achievements for user with unlock status."""
    result = await db.execute(
        select(UserAchievement).where(UserAchievement.user_id == user_id)
    )
    unlocked = {ua.achievement_id: ua.achieved_at for ua in result.scalars().all()}
    return unlocked


async def get_user_progress(db: AsyncSession, user_id: str) -> dict[str, int]:
    """Get current progress values for multi-step achievements."""
    progress = {}

    # Chat count
    chat_count = (await db.execute(
        select(func.count()).select_from(Chat).where(Chat.user_id == user_id)
    )).scalar() or 0
    progress["five_adventures"] = chat_count

    # Message count
    msg_count = (await db.execute(
        select(func.count()).select_from(Message)
        .join(Chat, Message.chat_id == Chat.id)
        .where(Chat.user_id == user_id, Message.role == MessageRole.user)
    )).scalar() or 0
    progress["bookworm"] = min(msg_count, 100)
    progress["storyteller"] = min(msg_count, 500)

    # Rating count
    rating_count = (await db.execute(
        select(func.count()).select_from(Chat)
        .where(Chat.user_id == user_id, Chat.rating.isnot(None))
    )).scalar() or 0
    progress["five_ratings"] = rating_count

    # Dice rolls
    dice_count = (await db.execute(
        select(func.count()).select_from(Message)
        .join(Chat, Message.chat_id == Chat.id)
        .where(Chat.user_id == user_id, Message.dice_rolls.isnot(None))
    )).scalar() or 0
    progress["dice_roller"] = min(dice_count, 20)

    return progress
