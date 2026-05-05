"""
Application entry point.

Creates the FastAPI app, registers middleware, mounts the router,
and configures global exception handlers + logging.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.models.schemas import ErrorResponse

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan (startup / shutdown hooks) ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs startup logic before yield, shutdown logic after."""
    logger.info("🚀  %s v%s starting up.", settings.application_name, settings.application_version)
    yield
    logger.info("🛑  %s shutting down.", settings.application_name)


# ── App Factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.application_name,
    version=settings.application_version,
    description=settings.application_description,
    lifespan=lifespan,
    # Swagger UI available at /docs; ReDoc at /redoc
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ── CORS Middleware ───────────────────────────────────────────────────────────
# In production, replace ["*"] with your actual frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for any unhandled server error.
    Returns a sanitized 500 — never leaks stack traces to the client.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
        ).model_dump(mode="json"),
    )


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")


# ── Root redirect hint ────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "product": "AI Resume Analyzer API",
        "version": "1.0.0",
        "status": "live",
        "features": [
            "ATS score analysis",
            "Skill gap detection",
            "AI-powered resume improvements"
        ],
        "docs": "/docs",
        "health": "/api/v1/health",
    }
