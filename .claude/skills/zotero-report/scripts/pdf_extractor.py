"""PDF text extraction utility."""

from typing import Optional


def extract_text_from_pdf(
    pdf_path: str, max_pages: int = 50, max_chars: int = 0
) -> Optional[str]:
    """Extract text from a PDF file using pypdf.

    Args:
        pdf_path: Path to PDF file.
        max_pages: Maximum number of pages to extract.
        max_chars: Maximum characters to return (0 = unlimited).

    Returns:
        Extracted text or None if extraction fails.
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        pages = reader.pages[:max_pages]
        text = "\n\n".join(page.extract_text() or "" for page in pages)
        text = text.strip()
        if not text:
            return None
        if max_chars > 0:
            text = text[:max_chars]
        return text
    except Exception as e:
        print(f"PDF extraction failed for {pdf_path}: {e}")
        return None
