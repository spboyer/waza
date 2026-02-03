"""Configuration management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from waza.api.storage import get_storage

router = APIRouter(prefix="/api/config", tags=["config"])


class ConfigUpdate(BaseModel):
    """Request model for updating config."""
    model: str | None = None
    executor: str | None = None
    theme: str | None = None


@router.get("")
async def get_config() -> dict[str, Any]:
    """Get current configuration."""
    return get_storage().get_config()


@router.put("")
async def update_config(data: ConfigUpdate) -> dict[str, Any]:
    """Update configuration."""
    storage = get_storage()
    config = storage.get_config()
    
    if data.model is not None:
        config["model"] = data.model
    if data.executor is not None:
        config["executor"] = data.executor
    if data.theme is not None:
        config["theme"] = data.theme
    
    storage.save_config(config)
    return config
