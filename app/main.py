"""
main.py
───────
FastAPI application factory.
"""

import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# ✅ ADD CORS FIX
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.logging import RequestLoggingMiddleware
from app.routers import credit, customers, offers

from app.database import Base, engine
from app import models

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-grade REST API for managing customer credit profiles, "
            "credit gap analysis, and loan offer lifecycle — built for Softlend."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ✅ CORS FIX (IMPORTANT FOR Swagger UI / browser requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # dev mode (allow all)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 🔥 CREATE TABLES AUTOMATICALLY
    Base.metadata.create_all(bind=engine)

    # Middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Routers
    app.include_router(customers.router)
    app.include_router(credit.router)
    app.include_router(offers.router)

    # ─────────────────────────────────────────────
    # Validation error handler
    # ─────────────────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):

        first_error = exc.errors()[0] if exc.errors() else {}
        location = " → ".join(str(loc) for loc in first_error.get("loc", []))
        message = first_error.get("msg", "Validation error.")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": f"{location}: {message}" if location else message,
                "code": "VALIDATION_ERROR",
            },
        )

    # ─────────────────────────────────────────────
    # Global exception handler (DEBUG MODE)
    # ─────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):

        logger.exception(
            "Unhandled exception on %s %s",
            request.method,
            request.url.path
        )

        print("\n🔥 FULL ERROR TRACEBACK:")
        print(traceback.format_exc())

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": str(exc),   # show real error
                "code": "INTERNAL_SERVER_ERROR",
            },
        )

    # ─────────────────────────────────────────────
    # Health check
    # ─────────────────────────────────────────────
    @app.get("/", tags=["Health"])
    def health_check():
        return {
            "status": "ok",
            "api": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    return app


# Create app instance
app = create_app()
