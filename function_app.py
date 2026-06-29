import json
import os
import logging

import azure.functions as func
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.credentials import AzureKeyCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def _analyze(file_bytes: bytes) -> AnalyzeResult:
    """Run the prebuilt-read model over a document (JPG, PNG, TIFF, or PDF).

    Reads the endpoint and key from the VISION_ENDPOINT and VISION_KEY
    environment variables.
    """
    endpoint = os.environ["VISION_ENDPOINT"]
    key = os.environ["VISION_KEY"]

    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )

    poller = client.begin_analyze_document("prebuilt-read", body=file_bytes)
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


def _load_upload_page() -> str:
    """Read the bundled upload.html page from disk."""
    html_path = os.path.join(os.path.dirname(__file__), "upload.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.route(route="upload", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def upload(req: func.HttpRequest) -> func.HttpResponse:
    """GET serves the upload page; POST extracts content from the posted file."""
    if req.method == "GET":
        return func.HttpResponse(
            _load_upload_page(),
            mimetype="text/html",
            status_code=200,
        )

    # POST: the raw file bytes come in the request body.
    file_bytes = req.get_body()
    if not file_bytes:
        return func.HttpResponse("No file uploaded.", status_code=400)

    try:
        result = extract_content(file_bytes)
    except KeyError:
        return func.HttpResponse(
            "VISION_ENDPOINT and VISION_KEY must be configured.",
            status_code=500,
        )
    except Exception:
        logging.exception("Document analysis failed.")
        return func.HttpResponse("Failed to analyze document.", status_code=502)

    return func.HttpResponse(
        body=json.dumps(result),
        mimetype="application/json",
        status_code=200,
    )


@app.route(route="readkeywords", methods=["POST"])
def readkeywords(req: func.HttpRequest) -> func.HttpResponse:
    """POST a JPG, PNG, TIFF, or PDF in the request body; returns its text."""
    logging.info("OCR content-extractor function processed a request.")

    file_bytes = req.get_body()
    if not file_bytes:
        return func.HttpResponse(
            "Send an image or PDF as the raw request body.",
            status_code=400,
        )

    try:
        result = extract_content(file_bytes)
    except KeyError:
        return func.HttpResponse(
            "VISION_ENDPOINT and VISION_KEY must be configured.",
            status_code=500,
        )
    except Exception:
        logging.exception("Document analysis failed.")
        return func.HttpResponse("Failed to analyze document.", status_code=502)

    return func.HttpResponse(
        body=json.dumps(result),
        mimetype="application/json",
        status_code=200,
    )
