"""Proof-of-Work challenge for registration anti-bot protection.

Client must find a nonce such that SHA256(challenge + nonce) starts with N hex zeros.
Difficulty 4 ≈ 65k iterations ≈ 50-200ms in browser, blocks simple bots.
"""

import hashlib
import secrets
import time

_challenges: dict[str, float] = {}  # challenge → created_at (monotonic)
DIFFICULTY = 4  # number of leading hex zeros required
CHALLENGE_TTL = 300  # 5 minutes


def create_challenge() -> str:
    """Generate a new PoW challenge."""
    # Cleanup expired challenges
    now = time.monotonic()
    expired = [k for k, v in _challenges.items() if now - v > CHALLENGE_TTL]
    for k in expired:
        _challenges.pop(k, None)

    challenge = secrets.token_hex(16)
    _challenges[challenge] = now
    return challenge


def verify_pow(challenge: str, nonce: str) -> bool:
    """Verify a PoW solution. Each challenge can only be used once."""
    if not challenge or not nonce:
        return False
    ts = _challenges.pop(challenge, None)
    if ts is None:
        return False
    if time.monotonic() - ts > CHALLENGE_TTL:
        return False
    h = hashlib.sha256(f"{challenge}{nonce}".encode()).hexdigest()
    return h[:DIFFICULTY] == "0" * DIFFICULTY
