"""Evals endpoints for skill-eval API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from skill_eval.api.storage import StorageManager

router = APIRouter()
storage = StorageManager()


class EvalCreate(BaseModel):
    """Model for creating a new eval."""
    id: str
    name: str
    skill: str
    version: str
    config: dict[str, Any]
    metrics: dict[str, Any]
    tasks: list[dict[str, Any]] | None = None


class EvalUpdate(BaseModel):
    """Model for updating an eval."""
    name: str | None = None
    skill: str | None = None
    version: str | None = None
    config: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    tasks: list[dict[str, Any]] | None = None


@router.get("")
async def list_evals():
    """List all eval suites."""
    evals = storage.list_evals()
    return {"evals": evals, "count": len(evals)}


@router.get("/{eval_id}")
async def get_eval(eval_id: str):
    """Get a specific eval suite."""
    eval_data = storage.get_eval(eval_id)
    if not eval_data:
        raise HTTPException(status_code=404, detail="Eval not found")
    return eval_data


@router.post("")
async def create_eval(eval: EvalCreate):
    """Create a new eval suite."""
    # Check if eval already exists
    existing = storage.get_eval(eval.id)
    if existing:
        raise HTTPException(status_code=409, detail="Eval already exists")
    
    # Create eval
    eval_data = eval.model_dump(exclude={"id"})
    result = storage.create_eval(eval.id, eval_data)
    return result


@router.put("/{eval_id}")
async def update_eval(eval_id: str, eval: EvalUpdate):
    """Update an existing eval suite."""
    # Get existing eval
    existing = storage.get_eval(eval_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Eval not found")
    
    # Update only provided fields
    update_data = eval.model_dump(exclude_none=True)
    for key, value in update_data.items():
        existing[key] = value
    
    # Remove metadata fields before saving
    for field in ["id", "path"]:
        existing.pop(field, None)
    
    result = storage.update_eval(eval_id, existing)
    return result


@router.delete("/{eval_id}")
async def delete_eval(eval_id: str):
    """Delete an eval suite."""
    success = storage.delete_eval(eval_id)
    if not success:
        raise HTTPException(status_code=404, detail="Eval not found")
    return {"success": True, "message": f"Eval {eval_id} deleted"}
