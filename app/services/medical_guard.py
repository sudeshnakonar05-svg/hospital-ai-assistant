"""Medical-safety guardrails for chatbot answers."""

DISCLAIMER = (
    "This assistant shares hospital information from indexed documents. "
    "It is not a substitute for professional medical advice, diagnosis, or treatment."
)


def apply_medical_guard(answer: str, emergency: bool = False) -> str:
    """Append a non-diagnostic disclaimer unless an emergency banner already applies."""
    if emergency:
        return answer
    if DISCLAIMER.lower() in answer.lower():
        return answer
    return f"{answer.rstrip()}\n\n{DISCLAIMER}"
