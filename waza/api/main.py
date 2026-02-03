"""FastAPI application for waza Web UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from waza import __version__
from waza.api.auth import router as auth_router
from waza.api.routes import config_router, evals_router, runs_router, skills_router

app = FastAPI(
    title="waza",
    description="Evaluate Agent Skills like you evaluate AI Agents",
    version=__version__,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(evals_router)
app.include_router(runs_router)
app.include_router(skills_router)
app.include_router(config_router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": __version__}


# Mount static files for production build (if exists)
static_dir = Path(__file__).parent.parent.parent / "web" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


def create_app() -> FastAPI:
    """Create and return the FastAPI app."""
    return app
