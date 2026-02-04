"""Runs management endpoints with background execution and SSE streaming."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from waza.api.storage import get_storage

router = APIRouter(prefix="/api/runs", tags=["runs"])

# Track active runs for SSE
active_runs: dict[str, dict[str, Any]] = {}


class RunCreate(BaseModel):
    """Request model for starting a run."""
    eval_id: str
    executor: str = "mock"
    model: str = "claude-sonnet-4-20250514"


async def execute_run(run_id: str, eval_id: str, executor: str, model: str) -> None:
    """Execute an eval run in the background."""
    storage = get_storage()

    # Update status to running
    active_runs[run_id] = {"status": "running", "progress": 0, "current_task": ""}
    storage.update_run(run_id, {
        "eval_name": eval_id,
        "status": "running",
        "progress": 0,
    })

    try:
        # Get eval content and path
        eval_data = storage.get_eval(eval_id)
        if not eval_data:
            raise ValueError(f"Eval {eval_id} not found")

        # Get the eval directory path (where tasks/ folder is)
        eval_dir = storage.get_eval_dir(eval_id)

        # Import runner and execute
        from waza.runner import EvalRunner
        from waza.schemas.eval_spec import EvalSpec
        from waza.executors import MockExecutor, get_copilot_executor

        spec = EvalSpec.from_yaml(eval_data["raw"])

        # Create executor based on type
        if executor == "mock":
            exec_instance = MockExecutor()
        else:
            CopilotExecutor = get_copilot_executor()
            if CopilotExecutor is None:
                raise ValueError("Copilot SDK not available. Use 'mock' executor or install copilot SDK.")
            exec_instance = CopilotExecutor(model=model)

        runner = EvalRunner(
            spec,
            executor=exec_instance,
            base_path=eval_dir,  # Pass the eval directory so tasks/*.yaml resolves
        )

        # Run with progress updates
        tasks = runner.load_tasks()
        total_tasks = len(tasks)

        if total_tasks == 0:
            raise ValueError(f"No tasks found in {eval_dir}/tasks/")

        completed = 0

        async def progress_callback(task_name: str) -> None:
            nonlocal completed
            completed += 1
            progress = int((completed / total_tasks) * 100) if total_tasks > 0 else 100
            active_runs[run_id] = {
                "status": "running",
                "progress": progress,
                "current_task": task_name,
            }

        # Run the eval
        results = await runner.run_async(tasks)

        # Convert results to dict
        results_dict = results.model_dump()
        results_dict["status"] = "completed"

        storage.update_run(run_id, results_dict)
        active_runs[run_id] = {"status": "completed", "progress": 100}

    except Exception as e:
        error_result = {
            "eval_name": eval_id,
            "status": "failed",
            "error": str(e),
        }
        storage.update_run(run_id, error_result)
        active_runs[run_id] = {"status": "failed", "error": str(e)}


@router.get("")
async def list_runs(limit: int = 50) -> list[dict[str, Any]]:
    """List recent runs."""
    return get_storage().list_runs(limit=limit)


@router.get("/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    """Get run details."""
    run = get_storage().get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Include live status if running
    if run_id in active_runs:
        run["live_status"] = active_runs[run_id]

    return run


@router.post("")
async def create_run(data: RunCreate, background_tasks: BackgroundTasks) -> dict[str, str]:
    """Start a new eval run."""
    storage = get_storage()

    # Verify eval exists
    eval_data = storage.get_eval(data.eval_id)
    if not eval_data:
        raise HTTPException(status_code=404, detail="Eval not found")

    # Create run
    run_id = storage.create_run(data.eval_id)

    # Start background execution
    background_tasks.add_task(execute_run, run_id, data.eval_id, data.executor, data.model)

    return {"run_id": run_id, "status": "started"}


@router.get("/{run_id}/stream")
async def stream_run(run_id: str, request: Request) -> StreamingResponse:
    """Stream run progress via SSE."""

    async def event_generator():
        last_status = None

        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Get current status
            if run_id in active_runs:
                status = active_runs[run_id]
            else:
                # Check storage for completed run
                run = get_storage().get_run(run_id)
                if run and "results" in run:
                    status = {"status": run["results"].get("status", "completed")}
                else:
                    status = {"status": "unknown"}

            # Only send if changed
            if status != last_status:
                yield f"data: {json.dumps(status)}\n\n"
                last_status = status

            # Exit if completed or failed
            if status.get("status") in ("completed", "failed"):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.delete("/{run_id}")
async def delete_run(run_id: str) -> dict[str, str]:
    """Delete a run."""
    if not get_storage().delete_run(run_id):
        raise HTTPException(status_code=404, detail="Run not found")

    # Clean up active run if present
    if run_id in active_runs:
        del active_runs[run_id]

    return {"status": "deleted"}
