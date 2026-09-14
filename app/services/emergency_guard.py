"""Detect emergency language and return a safety-first response."""

import re

EMERGENCY_PATTERNS = [
    r"\bchest pain\b",
    r"\bcan't breathe\b",
    r"\bcannot breathe\b",
    r"\bdifficulty breathing\b",
    r"\btrouble breathing\b",
    r"\bshortness of breath\b",
    r"\bsuicide\b",
    r"\bkill myself\b",
    r"\boverdose\b",
    r"\bstroke\b",
    r"\bface droop",
    r"\bunconscious\b",
    r"\bnot breathing\b",
    r"\bsevere bleeding\b",
    r"\bheavy bleeding\b",
    r"\banaphylaxis\b",
    r"\bheart attack\b",
    r"\bseizure\b",
    r"\bchoking\b",
    r"\bpoison",
    r"\b911\b",
    r"\bmedical emergency\b",
    r"\bemergency (?:right now|help)\b",
    r"\bcall (?:an? )?emergency (?:number|services)\b",
]

EMERGENCY_RESPONSE = (
    "This sounds like a medical emergency. Call your local emergency number "
    "(for example 911) or go to the nearest Emergency Department immediately. "
    "Do not wait for a chatbot answer. If you are with the person, stay with them "
    "and follow instructions from emergency dispatchers."
)


def is_emergency(text: str) -> bool:
    """Return True when the user message appears to describe an emergency."""
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in EMERGENCY_PATTERNS)


def emergency_response() -> str:
    """Return the canned emergency safety message."""
    return EMERGENCY_RESPONSE
