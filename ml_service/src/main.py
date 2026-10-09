"""
main.py — FastAPI application entry point for the HeatShield ML Service.

Runs on port 8001 (backend is on 8000).
Start with:
    cd ml_service
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.core.model_registry import ModelRegistry
from src.api.routes import api_router

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s  %(name)-20s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

model_registry: Optional[ModelRegistry] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_registry
    logger.info("Starting HeatShield ML Service")
    try:
        model_registry = ModelRegistry(models_dir=str(settings.model_path))
        loaded = model_registry.load_latest_model()
        if loaded:
            logger.info("Model loaded successfully — version %s", model_registry.get_model_version())
        else:
            logger.warning("No model found in %s — /forecast will return 503", settings.model_path)
    except Exception as exc:
        logger.error("Model registry init failed: %s", exc)
    yield
    logger.info("Shutting down HeatShield ML Service")


app = FastAPI(
    title="HeatShield ML Service",
    description="Demand forecasting for NHS hospitals during extreme heat events.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def root_health():
    global model_registry
    return {
        "status":       "healthy",
        "model_status": "ready" if model_registry and model_registry.is_model_loaded() else "not_loaded",
        "version":      "1.0.0",
    }
