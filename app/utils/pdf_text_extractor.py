
import pymupdf  # PyMuPDF
from typing import Union


def extract_text_from_pdf(pdf_bytes: Union[bytes, bytearray]) -> str:
    """
    Extracts all text content from a PDF file.

    Args:
        pdf_bytes (bytes): Raw PDF file content in bytes.

    Returns:
        str: Combined text from all pages.
    """
    try:
        text = ""
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")

