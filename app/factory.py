"""FastAPI Application Factory and Lifespan Manager for ComplianceOS (v2.2.0)."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from config.settings import get_settings
from database.engine import engine, init_db
from database.session import get_db_session
from observability.config import setup_logging

logger = logging.getLogger("complianceos.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager handling application startup and shutdown events."""
    logger.info("Initializing ComplianceOS application lifespan...")
    await init_db()
    logger.info("Database initialized successfully.")

    yield

    logger.info("Shutting down ComplianceOS application lifespan...")
    await engine.dispose()
    logger.info("Database engine disposed.")


def create_app(init_database: bool = True) -> FastAPI:
    """FastAPI Application Factory returning configured FastAPI instance."""
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title="ComplianceOS Enterprise AI Platform",
        version="2.2.0",
        description="Autonomous Regulatory Compliance Verification Engine",
        lifespan=lifespan if init_database else None,
    )

    # Configure CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health & Readiness Probes
    @app.get("/health/live", tags=["Health"])
    async def liveness_probe():
        return {"status": "live", "service": "ComplianceOS"}

    @app.get("/health/ready", tags=["Health"])
    async def readiness_probe(response: Response, session=Depends(get_db_session)):
        try:
            await session.execute(text("SELECT 1"))
            return {"status": "ready", "database": "connected"}
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            response.status_code = 503
            return {"status": "unhealthy", "database": str(e)}

    # Register Domain Routers Directly (No main.py import dependency)
    from auth.dependencies import router as auth_router
    from review.services.review_service import router as review_router
    from report.exporters.html_exporter import router as report_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(review_router, prefix="/api/v1/review", tags=["Review"])
    app.include_router(report_router, prefix="/api/v1/reports", tags=["Reports"])

    return app
