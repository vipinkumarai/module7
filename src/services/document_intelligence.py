"""Azure AI Document Intelligence service layer.

Wraps the prebuilt-read OCR model so the HTTP blueprints stay thin and the
extraction logic is reusable and testable.
"""
import os

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.credentials import AzureKeyCredential


def _client() -> DocumentIntelligenceClient:
    """Build a client from the VISION_ENDPOINT / VISION_KEY app settings."""
    endpoint = os.environ["VISION_ENDPOINT"]
    key = os.environ["VISION_KEY"]
    return DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )


def _analyze(file_bytes: bytes) -> AnalyzeResult:
    """Run the prebuilt-read model over a document (JPG, PNG, TIFF, or PDF)."""
    poller = _client().begin_analyze_document("prebuilt-read", body=file_bytes)
    return poller.result()


def extract_content(file_bytes: bytes) -> dict:
    """Extract text from an image or PDF.

    Returns the full text content, the words, and per-page text so multi-page
    PDFs are usable.
    """
    result = _analyze(file_bytes)

    words: list[str] = []
    pages: list[dict] = []
    if result.pages:
        for page in result.pages:
            page_words = [word.content for word in page.words] if page.words else []
            words.extend(page_words)
            pages.append(
                {
                    "page_number": page.page_number,
                    "text": " ".join(page_words),
                }
            )

    return {
        "content": result.content or "",
        "page_count": len(pages),
        "pages": pages,
        "keywords": words,
    }


def extract_content_from_file(path: str) -> dict:
    """Convenience wrapper that takes a JPG or PDF file path on disk."""
    with open(path, "rb") as f:
        return extract_content(f.read())
