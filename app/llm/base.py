"""LLM provider interface."""

from abc import ABC, abstractmethod

from app.schemas.chat import SourceReference


class LLMProvider(ABC):
    """Generate an answer from a question and retrieved sources."""

    name: str

    @abstractmethod
    def generate(self, question: str, sources: list[SourceReference]) -> str:
        """Return a natural-language answer."""
