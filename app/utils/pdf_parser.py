"""
PDF parsing utility.

Responsibility: Extract plain text from a PDF binary blob.
Uses PyMuPDF (fitz) — the fastest and most reliable pure-Python PDF parser.

This module has NO business logic. It does one thing: bytes → text.
"""

import io
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFParsingError(Exception):
    """Raised when the PDF cannot be opened or is corrupt."""
    pass


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF given its raw bytes.

    Args:
        file_bytes: Raw bytes of the PDF file.

    Returns:
        A single string containing all extracted text, pages joined by newlines.

    Raises:
        PDFParsingError: If the file is not a valid PDF or is password-protected.
    """
    try:
        # Open the PDF from an in-memory buffer (no temp files needed)
        pdf_document = fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf")
    except Exception as exc:
        logger.error("Failed to open PDF: %s", exc)
        raise PDFParsingError(
            "Could not open the uploaded file. Ensure it is a valid, non-corrupted PDF."
        ) from exc

    if pdf_document.is_encrypted:
        pdf_document.close()
        raise PDFParsingError(
            "The uploaded PDF is password-protected. Please upload an unlocked PDF."
        )

    page_texts: list[str] = []

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        page_text = page.get_text("text")        # plain text, preserving layout
        if page_text.strip():
            page_texts.append(page_text)

    pdf_document.close()

    full_text = "\n".join(page_texts).strip()

    if not full_text:
        raise PDFParsingError(
            "No readable text was found in the PDF. "
            "It may be a scanned image. Please upload a text-based PDF."
        )

    logger.info("PDF parsed successfully — %d characters extracted.", len(full_text))
    return full_text
