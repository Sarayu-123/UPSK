import traceback

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.logging_config import logger
from app.config import settings, Environment


# Headers that should never appear in logs
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "x-api-key",
    "proxy-authorization"
}


def sanitize_headers(headers):
    safe_headers = {}

    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            safe_headers[key] = "[REDACTED]"
        else:
            safe_headers[key] = value

    return safe_headers


async def http_exception_handler(
    request: Request,
    exc: HTTPException
):
    request_id = getattr(
        request.state,
        "request_id",
        "unknown"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "request_id": request_id
            }
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    request_id = getattr(
        request.state,
        "request_id",
        "unknown"
    )

    errors = []

    for err in exc.errors():
        location = " -> ".join(
            str(x) for x in err["loc"]
        )

        errors.append({
            "field": location,
            "message": err["msg"]
        })

    safe_headers = sanitize_headers(request.headers)

    logger.warning(
        f"Validation failed for request {request_id}. "
        f"Headers: {safe_headers}. "
        f"Errors: {errors}"
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": errors,
                "request_id": request_id
            }
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
):
    request_id = getattr(
        request.state,
        "request_id",
        "unknown"
    )

    logger.error(
        {
            "request_id": request_id,
            "path": request.url.path,
            "exception": str(exc),
            "traceback": traceback.format_exc()
        }
    )

    if "ReadOnlySqlTransaction" in str(exc) or "read-only transaction" in str(exc):
        logger.error(f"Partial Failure: Database is in read-only mode. request_id={request_id}")
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Database is currently in read-only mode (e.g., during failover). Write operations are temporarily disabled.",
                    "request_id": request_id
                }
            }
        )

    if settings.app_env in (
        Environment.development,
        Environment.staging
    ):
        message = str(exc)
    else:
        message = "An unexpected error occurred"

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": message,
                "request_id": request_id
            }
        }
    )