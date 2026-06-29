"""Hello-world HTTP function (sanity check / template)."""
import logging

import azure.functions as func

bp = func.Blueprint()


@bp.route(route="funcmodule7")
def funcmodule7(req: func.HttpRequest) -> func.HttpResponse:
    """Return a greeting; pass ?name=... for a personalized response."""
    logging.info("Python HTTP trigger function processed a request.")

    name = req.params.get("name")
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get("name")

    if name:
        return func.HttpResponse(
            f"Hello, {name}. This HTTP triggered function executed successfully."
        )
    return func.HttpResponse(
        "This HTTP triggered function executed successfully. "
        "Pass a name in the query string or in the request body for a personalized response.",
        status_code=200,
    )
