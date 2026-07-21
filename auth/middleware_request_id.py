import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("complianceos.access")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware injecting X-Request-ID into request/response contexts and logging request latency."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.time()
        response: Response = await call_next(request)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        response.headers["X-Request-ID"] = request_id

        # Log structured request telemetry
        logger.info(
            f"{request.method} {request.url.path} {response.status_code} - {latency_ms}ms",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
            },
        )
        return response
