"""
utils/responses.py
──────────────────
Factory functions that construct uniform JSON error responses so every router
can raise the same structured payload without duplicating the dict literal.
"""

from fastapi.responses import JSONResponse


def error_response(
    status_code: int,
    error: str,
    code: str,
) -> JSONResponse:
    """
    Return a JSON response that matches the standard error envelope:

        {
            "error": "<human readable message>",
            "code":  "<ERROR_CODE>"
        }

    Args:
        status_code: HTTP status code (e.g. 404, 409, 422).
        error:       Human-readable description of what went wrong.
        code:        Machine-readable error code (SCREAMING_SNAKE_CASE).

    Returns:
        A FastAPI JSONResponse with the given status code and body.
    """
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "code": code},
    )
