"""Prompt construction for grounded hospital answers."""

from app.schemas.chat import SourceReference

SYSTEM_PROMPT = """You are the Hospital Knowledge Assistant for a real hospital information desk.
Answer ONLY using the provided context excerpts from official hospital documents.
If the context is insufficient, say you do not have that information in the knowledge base.
Never invent doctors, hours, treatments, or policies.
Do not provide a diagnosis or prescribe medication.
Keep answers concise and cite source filenames when relevant.
If the question is a medical emergency, tell the user to call local emergency services immediately.
"""


def build_rag_prompt(question: str, sources: list[SourceReference]) -> list[dict[str, str]]:
    """Build chat messages for the LLM using retrieved context."""
    context_blocks = []
    for index, source in enumerate(sources, start=1):
        context_blocks.append(
            f"[Source {index}] file={source.filename} chunk={source.chunk_index}\n{source.excerpt}"
        )
    context = "\n\n".join(context_blocks) if context_blocks else "(no matching documents)"
    user_content = (
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context. List the source filenames you used."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_retrieval_answer(question: str, sources: list[SourceReference]) -> str:
    """Compose an extractive answer without calling an LLM."""
    if not sources:
        return (
            "I could not find this information in the hospital knowledge base. "
            "Please rephrase the question or ask a staff member at the information desk."
        )
    lines = [
        "I found the following information in the hospital knowledge base:",
        "",
    ]
    for source in sources:
        lines.append(f"- From {source.filename}: {source.excerpt}")
    lines.append("")
    lines.append("This is an extractive summary. For clinical advice, speak with a licensed clinician.")
    return "\n".join(lines)
