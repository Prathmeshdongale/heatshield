"""
FastAPI application entry point for ThermoCare AI.

This module initializes the FastAPI application, configures middleware,
registers routes, and sets up model status tracking.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ml.model_registry import ModelRegistry
from app.api.routes import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global model registry instance
model_registry: Optional[ModelRegistry] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events including model loading.
    """
    global model_registry

    logger.info("Starting ThermoCare AI application")

    # Startup: Initialize model registry
    try:
        model_registry = ModelRegistry(models_dir=settings.models_dir)
        model_registry.load_latest_model()
        logger.info("Model registry initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model registry: {e}")
        model_registry = None

    yield

    # Shutdown: Cleanup
    logger.info("Shutting down ThermoCare AI application")


# Create FastAPI application
app = FastAPI(
    title="ThermoCare AI",
    description="Healthcare demand forecasting for extreme heat events in England",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns the application status and model availability.
    """
    global model_registry

    status = {
        "status": "healthy",
        "model_status": "not_loaded",
        "version": "1.0.0",
    }

    if model_registry is not None:
        if model_registry.is_model_loaded():
            status["model_status"] = "ready"
        else:
            status["model_status"] = "not_loaded"

    return status


@app.get("/api/v1/model/status", tags=["model"])
async def model_status():
    """
    Get detailed model status information.

    Returns model version, training date, and performance metrics.
    """
    global model_registry

    if model_registry is None:
        return {
            "status": "error",
            "message": "Model registry not initialized",
        }

    if not model_registry.is_model_loaded():
        return {
            "status": "unavailable",
            "message": "No model loaded",
        }

    return model_registry.get_model_info()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
