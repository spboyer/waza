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


class TaskCreate(BaseModel):
    """Request model for creating a task."""
    name: str
    content: str


class TaskUpdate(BaseModel):
    """Request model for updating a task."""
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


# Task endpoints
@router.get("/{eval_id}/tasks")
async def list_tasks(eval_id: str) -> list[dict[str, Any]]:
    """List all tasks in an eval."""
    eval_data = get_storage().get_eval(eval_id)
    if not eval_data:
        raise HTTPException(status_code=404, detail="Eval not found")
    return get_storage().list_tasks(eval_id)


@router.get("/{eval_id}/tasks/{task_id}")
async def get_task(eval_id: str, task_id: str) -> dict[str, Any]:
    """Get a single task."""
    task = get_storage().get_task(eval_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{eval_id}/tasks")
async def create_task(eval_id: str, data: TaskCreate) -> dict[str, Any]:
    """Create a new task."""
    eval_data = get_storage().get_eval(eval_id)
    if not eval_data:
        raise HTTPException(status_code=404, detail="Eval not found")
    return get_storage().create_task(eval_id, data.name, data.content)


@router.put("/{eval_id}/tasks/{task_id}")
async def update_task(eval_id: str, task_id: str, data: TaskUpdate) -> dict[str, Any]:
    """Update a task."""
    existing = get_storage().get_task(eval_id, task_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")
    return get_storage().save_task(eval_id, task_id, data.content)


@router.post("/{eval_id}/tasks/{task_id}/duplicate")
async def duplicate_task(eval_id: str, task_id: str) -> dict[str, Any]:
    """Duplicate a task."""
    result = get_storage().duplicate_task(eval_id, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.delete("/{eval_id}/tasks/{task_id}")
async def delete_task(eval_id: str, task_id: str) -> dict[str, str]:
    """Delete a task."""
    if not get_storage().delete_task(eval_id, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted"}
