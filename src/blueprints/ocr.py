"""OCR API: extract text content from an image or PDF (key-protected)."""
import json
import logging

import azure.functions as func

from src.services.document_intelligence import extract_content

bp = func.Blueprint()

_USAGE = (
    "OCR endpoint. This URL only extracts text via POST.\n\n"
    "Usage:\n"
    "  curl -X POST \"<this-url>?code=<function-key>\" \\\n"
    "       --data-binary \"@yourfile.pdf\" \\\n"
    "       -H \"Content-Type: application/octet-stream\"\n\n"
    "Accepts JPG, PNG, TIFF, or PDF. Returns JSON with the extracted text.\n"
    "Prefer a browser? Use the upload page at /api/upload instead.\n"
)


@bp.route(route="readkeywords", methods=["GET", "POST"])
def readkeywords(req: func.HttpRequest) -> func.HttpResponse:
    """GET shows usage; POST extracts text from a JPG, PNG, TIFF, or PDF."""
    if req.method == "GET":
        return func.HttpResponse(_USAGE, mimetype="text/plain", status_code=200)

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
