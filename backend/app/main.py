"""
main.py — FastAPI application factory.
Responsibilities:
  - Create the FastAPI app instance
  - Register CORS middleware (frontend origin only)
  - Mount the versioned API router
  - Trigger ML model load on startup
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.router import api_router
from app.integrations.ml_adapter import load_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    load_model()   # non-blocking warning if artifact is missing
    yield
    # add teardown logic here if needed


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="HeatShield API",
        description="Hospital demand forecasting and heat-related capacity-risk monitoring.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # ----------------------------------------------------------------
    # CORS — only allow the configured frontend origin(s)
    # ----------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # ----------------------------------------------------------------
    # Routes
    # ----------------------------------------------------------------
    app.include_router(api_router)

    return app


app = create_app()
