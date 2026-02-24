"""XP / Leveling system -- award XP and calculate levels."""
import math
from sqlalchemy import text
from app.db.session import engine as db_engine


def calc_level(xp: int) -> int:
    """Calculate level from total XP. Level 2=100XP, 5=1600XP, 10=8100XP."""
    return int(math.floor(math.sqrt(xp / 100))) + 1


def xp_for_level(level: int) -> int:
    """XP required to reach a given level."""
    return ((level - 1) ** 2) * 100


async def award_xp(user_id: str, amount: int) -> dict:
    """Atomically award XP and recalculate level.

    Returns {xp_total, level, leveled_up, new_level}.
    """
    async with db_engine.begin() as conn:
        row = await conn.execute(
            text(
                "UPDATE users SET xp_total = COALESCE(xp_total, 0) + :amount "
                "WHERE id = :uid RETURNING xp_total"
            ),
            {"amount": amount, "uid": user_id},
        )
        new_xp = row.scalar()
        if new_xp is None:
            return {"xp_total": 0, "level": 1, "leveled_up": False, "new_level": 1}

        new_level = calc_level(new_xp)
        old_level = calc_level(new_xp - amount)
        leveled_up = new_level > old_level

        if leveled_up:
            await conn.execute(
                text("UPDATE users SET level = :lvl WHERE id = :uid"),
                {"lvl": new_level, "uid": user_id},
            )

        return {
            "xp_total": new_xp,
            "level": new_level,
            "leveled_up": leveled_up,
            "new_level": new_level,
        }
