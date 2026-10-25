from flask import jsonify, make_response


def success_response(message: str, data: dict | None = None, status_code: int = 200):
    payload = {
        "success": True,
        "message": message,
    }
    if data is not None:
        payload["data"] = data
    return make_response(jsonify(payload), status_code)


def error_response(
    message: str,
    errors: list[dict] | None = None,
    status_code: int = 400,
):
    payload = {
        "success": False,
        "message": message,
    }
    if errors is not None:
        payload["errors"] = errors
    return make_response(jsonify(payload), status_code)
