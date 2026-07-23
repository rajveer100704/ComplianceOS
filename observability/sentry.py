import logging
from typing import Optional, Any

logger = logging.getLogger("observability_sentry")


def setup_sentry(
    dsn: Optional[str] = None,
    environment: str = "development",
    sample_rate: float = 1.0,
):
    """Configures Sentry SDK error tracking with FastAPI and SQLAlchemy integrations."""
    if not dsn:
        logger.info("Sentry DSN not provided; error tracking disabled.")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        logging_integration = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=sample_rate,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                logging_integration,
            ],
            send_default_pii=False,
        )
        logger.info(
            f"Sentry error tracking initialized for environment '{environment}'."
        )
        return True

    except ImportError:
        logger.warning("sentry-sdk package not installed. Error tracking disabled.")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Sentry SDK: {e}")
        return False


def set_sentry_context(
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    role: Optional[str] = None,
    request_id: Optional[str] = None,
):
    """Hooks security & request metadata into Sentry scope without exposing secrets or PII."""
    try:
        import sentry_sdk

        with sentry_sdk.configure_scope() as scope:
            if user_id:
                scope.set_user({"id": user_id, "role": role or "unknown"})
            if organization_id:
                scope.set_tag("organization_id", organization_id)
            if request_id:
                scope.set_tag("request_id", request_id)
    except Exception:
        pass
