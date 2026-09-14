"""Extract text from uploaded hospital knowledge files."""

import logging
from pathlib import Path
from typing import Any

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def load_document(file_path: str) -> dict[str, Any]:
    """Extract text and return standard dictionary structure."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    file_type = suffix.lstrip(".") or "txt"
    try:
        text = extract_text(file_path)
        return {
            "text": text,
            "metadata": {
                "filename": path.name,
                "file_type": file_type,
            },
        }
    except Exception as exc:
        logger.exception("Failed to load document %s: %s", file_path, exc)
        raise


def extract_text(file_path: str) -> str:
    """Extract UTF-8 text from PDF, DOCX, TXT, or Markdown files."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise AppError(400, f"Unsupported file type: {suffix}", "unsupported_file_type")
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        logger.exception("Text reading failed for %s", file_path)
        raise AppError(400, f"Failed to read file: {exc}", "file_read_error") from exc


def _extract_pdf(path: Path) -> str:
    """Extract text from each PDF page."""
    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                pages.append(extracted)
        text = "\n".join(pages).strip()
        if not text:
            raise AppError(400, "PDF contained no extractable text", "empty_document")
        return text
    except AppError:
        raise
    except Exception as exc:
        logger.exception("PDF extraction failed for %s", path)
        raise AppError(400, f"Invalid PDF file: {exc}", "pdf_extraction_error") from exc


def _extract_docx(path: Path) -> str:
    """Extract paragraph text from a Word document."""
    try:
        document = DocxDocument(str(path))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
        if not text:
            raise AppError(400, "DOCX contained no extractable text", "empty_document")
        return text
    except AppError:
        raise
    except Exception as exc:
        logger.exception("DOCX extraction failed for %s", path)
        raise AppError(400, f"Invalid DOCX file: {exc}", "docx_extraction_error") from exc
