import time
import uuid
import structlog
from fastapi import Request

from app.logging_config import logger
from app.metrics import (
    http_requests_total,
    http_request_duration_seconds
)


async def request_context_middleware(
    request: Request,
    call_next
):
    structlog.contextvars.clear_contextvars()

    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid.uuid4())
    )

    request.state.request_id = request_id

    structlog.contextvars.bind_contextvars(
        request_id=request_id
    )

    request_logger = logger.bind(
        request_id=request_id
    )

    request_logger.info(
        "request_started",
        method=request.method,
        path=request.url.path
    )

    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration = (
            time.perf_counter() - start_time
        )

        latency_ms = round(
            duration * 1000,
            2
        )

        http_requests_total.labels(
            method=request.method,
            path=request.url.path,
            status=str(response.status_code)
        ).inc()

        http_request_duration_seconds.observe(
            duration
        )

        response.headers["X-Request-ID"] = request_id

        request_logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=latency_ms
        )

        return response

    except Exception as exc:

        duration = (
            time.perf_counter() - start_time
        )

        http_requests_total.labels(
            method=request.method,
            path=request.url.path,
            status="500"
        ).inc()

        http_request_duration_seconds.observe(
            duration
        )

        request_logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            error=str(exc)
        )

        raise