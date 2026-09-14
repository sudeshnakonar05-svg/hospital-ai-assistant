"""Unit tests for emergency and medical safety guards."""

from app.services.emergency_guard import emergency_response, is_emergency
from app.services.medical_guard import DISCLAIMER, apply_medical_guard


def test_emergency_keywords_are_detected() -> None:
    """Chest pain and similar phrases trigger the emergency path."""
    assert is_emergency("I have severe chest pain right now")
    assert is_emergency("Please call 911")
    assert is_emergency("She is unconscious")


def test_routine_questions_are_not_emergencies() -> None:
    """Ordinary hospital FAQ text is not treated as an emergency."""
    assert not is_emergency("What are visiting hours in the ICU?")
    assert not is_emergency("How do I book a cardiology appointment?")


def test_emergency_response_instructs_to_call_help() -> None:
    """The canned message tells the user to seek emergency care."""
    message = emergency_response()
    assert "911" in message
    assert "Emergency" in message


def test_medical_guard_appends_disclaimer() -> None:
    """Non-emergency answers get a non-diagnostic disclaimer."""
    guarded = apply_medical_guard("ICU visiting is 11 AM to 1 PM.")
    assert DISCLAIMER in guarded


def test_medical_guard_skips_emergency_answers() -> None:
    """Emergency banners are left unchanged."""
    raw = emergency_response()
    assert apply_medical_guard(raw, emergency=True) == raw
