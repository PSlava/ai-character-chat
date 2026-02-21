"""Dice rolling system for D&D-style expressions."""

import random
import re
from dataclasses import dataclass, asdict

# Pattern: optional count, 'd', sides, optional modifier, optional keep
# Examples: d20, 2d6+3, 4d8-2, 2d20kh1, 2d20kl1
_DICE_RE = re.compile(
    r'^(\d*)d(\d+)'           # NdM
    r'(?:(kh|kl)(\d+))?'      # optional keep highest/lowest
    r'([+-]\d+)?$',           # optional modifier
    re.IGNORECASE
)

MAX_DICE = 100
MAX_SIDES = 100


@dataclass
class DiceResult:
    expression: str
    rolls: list[int]
    kept: list[int] | None  # non-None if kh/kl was used
    modifier: int
    total: int

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["kept"] is None:
            del d["kept"]
        return d


def roll(expression: str) -> DiceResult:
    """Roll dice from an expression like '2d6+3', 'd20', '2d20kh1'.

    Raises ValueError for invalid expressions.
    """
    expr = expression.strip().lower().replace(" ", "")
    m = _DICE_RE.match(expr)
    if not m:
        raise ValueError(f"Invalid dice expression: {expression}")

    count = int(m.group(1)) if m.group(1) else 1
    sides = int(m.group(2))
    keep_type = m.group(3)  # 'kh' or 'kl' or None
    keep_count = int(m.group(4)) if m.group(4) else None
    modifier = int(m.group(5)) if m.group(5) else 0

    if count < 1 or count > MAX_DICE:
        raise ValueError(f"Dice count must be 1-{MAX_DICE}, got {count}")
    if sides < 2 or sides > MAX_SIDES:
        raise ValueError(f"Dice sides must be 2-{MAX_SIDES}, got {sides}")
    if keep_count is not None and keep_count > count:
        raise ValueError(f"Cannot keep {keep_count} from {count} dice")

    rolls = [random.randint(1, sides) for _ in range(count)]

    kept = None
    if keep_type == "kh" and keep_count:
        kept = sorted(rolls, reverse=True)[:keep_count]
    elif keep_type == "kl" and keep_count:
        kept = sorted(rolls)[:keep_count]

    dice_sum = sum(kept) if kept is not None else sum(rolls)
    total = dice_sum + modifier

    return DiceResult(
        expression=expression.strip(),
        rolls=rolls,
        kept=kept,
        modifier=modifier,
        total=total,
    )


def roll_advantage() -> DiceResult:
    """Roll d20 with advantage (2d20, keep highest)."""
    return roll("2d20kh1")


def roll_disadvantage() -> DiceResult:
    """Roll d20 with disadvantage (2d20, keep lowest)."""
    return roll("2d20kl1")
