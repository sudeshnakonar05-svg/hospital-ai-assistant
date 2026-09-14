"""Extractive provider used when Groq is disabled or unavailable."""

from app.llm.base import LLMProvider
from app.schemas.chat import SourceReference
from app.services.prompt_builder import build_retrieval_answer


class RetrievalOnlyProvider(LLMProvider):
    """Answer by concatenating retrieved excerpts without an LLM."""

    name = "retrieval_only"

    def generate(self, question: str, sources: list[SourceReference]) -> str:
        """Return an extractive answer from retrieved chunks."""
        return build_retrieval_answer(question, sources)
