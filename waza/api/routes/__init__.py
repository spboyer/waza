"""API routes package for waza Web UI."""

from waza.api.routes.config import router as config_router
from waza.api.routes.evals import router as evals_router
from waza.api.routes.runs import router as runs_router
from waza.api.routes.skills import router as skills_router

__all__ = ["evals_router", "runs_router", "skills_router", "config_router"]
