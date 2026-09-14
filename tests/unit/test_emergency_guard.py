"""Unit tests for emergency safety guard."""

from app.services.emergency_guard import is_emergency, emergency_response


def test_emergency_messages_detected() -> None:
    """Obvious emergency phrases must trigger the guard."""
    emergency_inputs = [
        "I am having severe chest pain",
        "I cannot breathe, help me",
        "Someone is unconscious on the floor",
        "There is heavy bleeding from an injury",
        "I think I am having a heart attack",
        "Patient is choking and turning blue",
    ]
    for text in emergency_inputs:
        assert is_emergency(text) is True, f"Failed to detect emergency for: {text}"


def test_normal_messages_not_detected() -> None:
    """Routine hospital questions must not trigger the emergency guard."""
    normal_inputs = [
        "What are the visiting hours for the cardiology ward?",
        "Where is the outpatient pharmacy located?",
        "Where is the Emergency Department?",
        "How can I book an appointment with Dr. Smith?",
        "Do you have a neurology department?",
        "Can I bring my child for a routine checkup?",
    ]
    for text in normal_inputs:
        assert is_emergency(text) is False, f"False positive emergency for: {text}"


def test_emergency_response_message() -> None:
    """The safety response provides clear guidance."""
    resp = emergency_response()
    assert "emergency" in resp.lower()
    assert len(resp) > 20
