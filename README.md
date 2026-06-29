# Module 7 — Azure Functions: Document OCR

An Azure Functions (Python v2) app that extracts text from images and PDFs
using **Azure AI Document Intelligence** (`prebuilt-read`), plus a browser
upload page and a simple hello-world endpoint.

## Project structure

```
module7/
├── function_app.py              # Entry point — registers the blueprints
├── host.json                    # Functions host config
├── local.settings.json          # Local env vars (not deployed)
├── requirements.txt             # Python dependencies
├── README.md
└── src/
    ├── blueprints/              # One module per feature (HTTP routes)
    │   ├── hello.py             #   GET  /api/funcmodule7
    │   ├── ocr.py               #   POST /api/readkeywords
    │   └── upload.py            #   GET/POST /api/upload  (+ static page)
    ├── services/
    │   └── document_intelligence.py   # Reusable OCR logic (prebuilt-read)
    └── static/
        └── upload.html          # Browser upload UI
```


### To run 

cd /private/tmp/module7
func azure functionapp publish app-module7 --python



The entry point stays thin and only wires feature **blueprints** into the
`FunctionApp`; each blueprint calls the shared **service layer**, so the OCR
logic is reusable and testable.

## The functions

### Hello world — `GET /api/funcmodule7`
A minimal HTTP trigger used as a sanity check / template. Returns a greeting;
pass `?name=...` for a personalized response.

### OCR — `POST /api/readkeywords` (key-protected)
Send an image (JPG/PNG/TIFF) or a PDF as the **raw request body**. It runs the
Document Intelligence `prebuilt-read` model and returns the full text, the
per-page text, a page count, and the flat word list as JSON.

### Upload page — `GET/POST /api/upload` (anonymous)
`GET` serves `upload.html`; the page posts the chosen file back to the same
endpoint, which extracts the content and renders it on the page. Same-origin,
so no function key is exposed in the browser and no CORS setup is needed.

## Configuration

These app settings (env vars) must point at an Azure AI Document Intelligence
resource:

| Setting | Value |
|---------|-------|
| `VISION_ENDPOINT` | `https://<your-resource>.cognitiveservices.azure.com/` |
| `VISION_KEY`      | the resource key |

Set them locally in `local.settings.json`, and in Azure with:

```bash
az functionapp config appsettings set -n app-module7 -g CSC425-ResourceGroup \
  --settings VISION_ENDPOINT="https://text-extractor-engine-f428e.cognitiveservices.azure.com/" \
             VISION_KEY="<your-key>"
```

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
func start
```

Then:

```bash
# Hello world
curl "http://localhost:7071/api/funcmodule7?name=Vipin"

# OCR (image or PDF) — returns JSON
curl -X POST "http://localhost:7071/api/readkeywords" \
  --data-binary "@ai_news.pdf" -H "Content-Type: application/octet-stream"

# Upload page — open in a browser
open http://localhost:7071/api/upload
```

## Deploy

```bash
func azure functionapp publish app-module7 --python
```

`func` packages the project (honoring `.funcignore`), uploads it, and Azure
runs a remote build to install `requirements.txt`.

## Use the deployed app

```bash
# Upload page (no key needed)
open https://app-module7.azurewebsites.net/api/upload

# OCR API (function key required)
KEY=$(az functionapp keys list -n app-module7 -g CSC425-ResourceGroup \
  --query "functionKeys.default" -o tsv)

curl -X POST "https://app-module7.azurewebsites.net/api/readkeywords?code=$KEY" \
  --data-binary "@ai_news.pdf" -H "Content-Type: application/octet-stream"
```

### Example response

```json
{
  "content": "full document text ...",
  "page_count": 2,
  "pages": [
    { "page_number": 1, "text": "text from page 1 ..." },
    { "page_number": 2, "text": "text from page 2 ..." }
  ],
  "keywords": ["word1", "word2"]
}
```

> **Note:** On the free **F0** Document Intelligence tier only the first 2 pages
> of a PDF are processed. Use the **S0** tier for full multi-page documents.
