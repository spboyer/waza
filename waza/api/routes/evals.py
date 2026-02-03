"""Evals CRUD endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from waza.api.storage import get_storage

router = APIRouter(prefix="/api/evals", tags=["evals"])


class EvalCreate(BaseModel):
    """Request model for creating an eval."""
    name: str
    content: str


class EvalUpdate(BaseModel):
    """Request model for updating an eval."""
    content: str


@router.get("")
async def list_evals() -> list[dict[str, Any]]:
    """List all eval suites."""
    return get_storage().list_evals()


@router.get("/{eval_id}")
async def get_eval(eval_id: str) -> dict[str, Any]:
    """Get eval by ID."""
    eval_data = get_storage().get_eval(eval_id)
    if not eval_data:
        raise HTTPException(status_code=404, detail="Eval not found")
    return eval_data


@router.post("")
async def create_eval(data: EvalCreate) -> dict[str, Any]:
    """Create a new eval."""
    return get_storage().create_eval(data.name, data.content)


@router.put("/{eval_id}")
async def update_eval(eval_id: str, data: EvalUpdate) -> dict[str, Any]:
    """Update an existing eval."""
    existing = get_storage().get_eval(eval_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Eval not found")
    return get_storage().save_eval(eval_id, data.content)


@router.delete("/{eval_id}")
async def delete_eval(eval_id: str) -> dict[str, str]:
    """Delete an eval."""
    if not get_storage().delete_eval(eval_id):
        raise HTTPException(status_code=404, detail="Eval not found")
    return {"status": "deleted"}
