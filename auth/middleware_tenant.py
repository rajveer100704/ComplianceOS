import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Extracts and attaches the active organization context to each request.

    Resolution priority:
      1. X-Organization-Id request header
      2. org_id cookie
      3. None (downstream handlers resolve from default membership)

    Attaches:
      request.state.organization_id  — raw string or None
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        org_id: Optional[str] = (
            request.headers.get("X-Organization-Id")
            or request.cookies.get("org_id")
        )

        if org_id:
            request.state.organization_id = org_id.strip()
            logger.debug(
                "TenantMiddleware: resolved org_id=%s for path=%s",
                org_id,
                request.url.path,
            )
        else:
            request.state.organization_id = None

        response = await call_next(request)
        return response
