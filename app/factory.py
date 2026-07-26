"""FastAPI Application Factory and Lifespan Manager for ComplianceOS (v2.1.0)."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import get_settings
from database.engine import engine, init_db
from observability.config import setup_logging

logger = logging.getLogger("complianceos.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager handling application startup and shutdown events."""
    logger.info("Initializing ComplianceOS application lifespan...")
    # Perform database initialization on startup
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
        version="2.1.0",
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

    # Register Routers
    from main import (
        router as main_router,
        auth_router,
        admin_router,
        review_router,
        report_router,
    )

    app.include_router(main_router)
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(review_router, prefix="/api/v1/review", tags=["Review"])
    app.include_router(report_router, prefix="/api/v1/reports", tags=["Reports"])

    return app
