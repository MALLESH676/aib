"""
FastAPI main application entry point.
"""
import sys
import os

# Ensure backend root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from models.database import init_db
from api.routes import analyze, dashboard, investigations, audit, demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print(f"[INFO] Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    await init_db()
    print("[SUCCESS] Database initialized")

    # Pre-load models
    try:
        from agents.risk_agent.model import get_risk_model
        from agents.coordinator.coordinator import get_coordinator
        model = get_risk_model()
        coordinator = get_coordinator()

        # Train risk model on synthetic data
        print("[INFO] Training Risk Agent model on synthetic data...")
        from data.synthetic.train_risk_model import train_risk_model
        train_risk_model(model)
        print("[SUCCESS] Risk Agent ready")
    except Exception as e:
        print(f"[WARNING] Model pre-loading partial: {e}")

    # Pre-warm sentence transformers
    try:
        from agents.review_agent.agent import ReviewAgent
        agent = ReviewAgent()
        agent._get_embedder()  # pre-load
        print("[SUCCESS] Review Agent embedder ready")
    except Exception as e:
        print(f"[WARNING] Review Agent pre-warm failed: {e}")

    # Seed demo data
    try:
        from data.synthetic.seed_db import seed_demo_cases
        await seed_demo_cases()
        print("[SUCCESS] Demo scenarios seeded")
    except Exception as e:
        print(f"[WARNING] Demo seed failed: {e}")

    yield

    print("[INFO] Shutting down TrustShield...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Trust & Safety Platform — Multi-agent fraud detection",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(investigations.router, prefix="/api/v1", tags=["Investigations"])
app.include_router(audit.router, prefix="/api/v1", tags=["Audit"])
app.include_router(demo.router, prefix="/api/v1", tags=["Demo"])


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_model": settings.LLM_MODEL,
        "demo_mode": settings.DEMO_MODE,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
