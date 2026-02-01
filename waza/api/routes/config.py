"""Config endpoints for skill-eval API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from waza.api.storage import StorageManager

router = APIRouter()
storage = StorageManager()


class ConfigUpdate(BaseModel):
    """Model for updating configuration."""
    model: str | None = None
    executor: str | None = None
    theme: str | None = None
    github_token: str | None = None


@router.get("")
async def get_config():
    """Get user configuration."""
    config = storage.get_config()
    return config


@router.put("")
async def update_config(config: ConfigUpdate):
    """Update user configuration."""
    update_data = config.model_dump(exclude_none=True)
    result = storage.update_config(update_data)
    return result
