"""Select an LLM provider from configuration or an explicit mode."""

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.groq_provider import GroqProvider
from app.llm.retrieval_only import RetrievalOnlyProvider


def get_llm(mode: str | None = None) -> LLMProvider:
    """Return Groq or retrieval-only based on mode / settings."""
    selected = (mode or get_settings().LLM_PROVIDER).lower()
    if selected == "retrieval_only":
        return RetrievalOnlyProvider()
    return GroqProvider()
