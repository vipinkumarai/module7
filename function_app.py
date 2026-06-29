"""Azure Functions entry point.

Keeps the app thin: it only wires the feature blueprints into the
FunctionApp. Each feature lives under src/blueprints, backed by reusable
services under src/services.
"""
import azure.functions as func

from src.blueprints.hello import bp as hello_bp
from src.blueprints.ocr import bp as ocr_bp
from src.blueprints.upload import bp as upload_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

app.register_functions(hello_bp)
app.register_functions(ocr_bp)
app.register_functions(upload_bp)
