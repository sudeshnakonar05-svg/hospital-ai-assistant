"""Groq chat completions provider."""

import logging

from groq import Groq

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.retrieval_only import RetrievalOnlyProvider
from app.schemas.chat import SourceReference
from app.services.prompt_builder import build_rag_prompt

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """Call Groq's OpenAI-compatible chat API."""

    name = "groq"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self._fallback = RetrievalOnlyProvider()

    def generate(self, question: str, sources: list[SourceReference]) -> str:
        """Generate a grounded answer, falling back to retrieval-only on error."""
        if not self.api_key or self.api_key.startswith("your_"):
            logger.warning("GROQ_API_KEY missing; using retrieval-only mode")
            return self._fallback.generate(question, sources)
        try:
            client = Groq(api_key=self.api_key)
            messages = build_rag_prompt(question, sources)
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=700,
            )
            content = completion.choices[0].message.content
            return content.strip() if content else self._fallback.generate(question, sources)
        except Exception:  # noqa: BLE001
            logger.exception("Groq generation failed; using retrieval-only fallback")
            return self._fallback.generate(question, sources)
