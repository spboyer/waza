"""FastAPI application for waza Web UI."""

from __future__ import annotations

import os
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
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
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
# Check multiple possible locations
def _find_static_dir() -> Path | None:
    candidates = [
        # Development: relative to repo root
        Path(__file__).parent.parent.parent / "web" / "dist",
        # Installed package with bundled frontend
        Path(__file__).parent / "static",
        # Environment variable override
        Path(os.environ.get("WAZA_STATIC_DIR", "")) if os.environ.get("WAZA_STATIC_DIR") else None,
    ]
    for candidate in candidates:
        if candidate and candidate.exists() and (candidate / "index.html").exists():
            return candidate
    return None


static_dir = _find_static_dir()
if static_dir:
    from fastapi.responses import FileResponse

    # Mount static assets (js, css, etc.)
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    # Serve favicon
    @app.get("/favicon.svg")
    async def favicon() -> FileResponse:
        return FileResponse(static_dir / "favicon.svg")

    # SPA catch-all - serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        # Return index.html for SPA routing
        return FileResponse(static_dir / "index.html")


def create_app() -> FastAPI:
    """Create and return the FastAPI app."""
    return app
