"""Upload page: serves upload.html (GET) and processes the file (POST).

Anonymous + same-origin, so the browser needs no function key and there is
no CORS to configure.
"""
import json
import logging
import os

import azure.functions as func

from src.services.document_intelligence import extract_content

bp = func.Blueprint()

_HTML_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "upload.html")


def _load_upload_page() -> str:
    with open(_HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


@bp.route(route="upload", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def upload(req: func.HttpRequest) -> func.HttpResponse:
    """GET serves the upload page; POST extracts content from the posted file."""
    if req.method == "GET":
        return func.HttpResponse(
            _load_upload_page(),
            mimetype="text/html",
            status_code=200,
        )

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
