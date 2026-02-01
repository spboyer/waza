"""FastAPI application for skill-eval Web UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from skill_eval import __version__
from skill_eval.api import auth
from skill_eval.api.routes import config, evals, runs, skills

# Create FastAPI app
app = FastAPI(
    title="skill-eval API",
    description="API backend for skill-eval Web UI",
    version=__version__,
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(evals.router, prefix="/api/evals", tags=["evals"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(config.router, prefix="/api/config", tags=["config"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": __version__}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "skill-eval API",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/health",
    }
