"""Extract plain text from PDF resumes."""

from io import BytesIO

from ugra.core.logging.setup import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required for PDF extraction") from exc

    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text.strip())
    result = "\n\n".join(parts).strip()
    if not result:
        raise ValueError("Could not extract text from PDF — file may be scanned/image-only")
    logger.info("pdf_text_extracted", pages=len(reader.pages), chars=len(result))
    return result
