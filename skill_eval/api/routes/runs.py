"""Runs endpoints for skill-eval API."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from skill_eval.api.storage import StorageManager
from skill_eval.runner import EvalRunner
from skill_eval.schemas.eval_spec import EvalSpec

router = APIRouter()
storage = StorageManager()

# Track active runs with detailed progress
active_runs: dict[str, dict[str, Any]] = {}


class RunCreate(BaseModel):
    """Model for creating a new run."""
    eval_id: str
    tasks: list[str] | None = None


async def execute_run(run_id: str, eval_id: str, eval_spec: EvalSpec, tasks: list[str] | None):
    """Execute an eval run in the background with progress tracking."""
    try:
        # Initialize progress
        active_runs[run_id] = {
            "status": "initializing",
            "progress": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "current_task": None,
            "current_trial": 0,
            "results": [],
        }
        
        # Create runner
        eval_path = storage.evals_dir / f"{eval_id}.yaml"
        runner = EvalRunner(spec=eval_spec, base_path=eval_path.parent)
        
        # Load tasks
        all_tasks = runner.load_tasks()
        if tasks:
            all_tasks = [t for t in all_tasks if t.id in tasks]
        
        total_tasks = len(all_tasks)
        active_runs[run_id].update({
            "status": "running",
            "total_tasks": total_tasks,
        })
        
        # Progress callback
        def progress_callback(
            event: str,
            task_name: str | None = None,
            task_num: int | None = None,
            trial_num: int | None = None,
            status: str | None = None,
            **kwargs
        ):
            if run_id in active_runs:
                if event == "task_start":
                    active_runs[run_id].update({
                        "current_task": task_name,
                        "current_trial": trial_num or 1,
                    })
                elif event == "task_complete":
                    completed = active_runs[run_id]["completed_tasks"] + 1
                    active_runs[run_id].update({
                        "completed_tasks": completed,
                        "progress": int((completed / total_tasks) * 100) if total_tasks else 0,
                    })
                    if status:
                        active_runs[run_id].setdefault("results", []).append({
                            "task": task_name,
                            "status": status,
                        })
        
        # Run eval with progress callback
        results = runner.run(progress_callback=progress_callback)
        
        # Save results
        storage.save_run_results(run_id, results)
        
        # Update final status
        active_runs[run_id].update({
            "status": "completed",
            "progress": 100,
            "completed_tasks": total_tasks,
        })
        
    except Exception as e:
        if run_id in active_runs:
            active_runs[run_id].update({
                "status": "failed",
                "error": str(e),
            })


@router.get("")
async def list_runs():
    """List all eval runs."""
    runs = storage.list_runs()
    return {"runs": runs, "count": len(runs)}


@router.get("/{run_id}")
async def get_run(run_id: str):
    """Get a specific run."""
    # Check if run is active
    if run_id in active_runs:
        return {
            "run_id": run_id,
            "status": active_runs[run_id].get("status", "running"),
            "progress": active_runs[run_id].get("progress", 0),
            "total_tasks": active_runs[run_id].get("total_tasks", 0),
            "completed_tasks": active_runs[run_id].get("completed_tasks", 0),
        }
    
    # Get completed run
    run_data = storage.get_run(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return run_data


@router.post("")
async def create_run(run: RunCreate, background_tasks: BackgroundTasks):
    """Create and execute a new run."""
    # Get eval
    eval_data = storage.get_eval(run.eval_id)
    if not eval_data:
        raise HTTPException(status_code=404, detail="Eval not found")
    
    # Create run
    run_id = storage.create_run(run.eval_id)
    
    # Load eval spec
    from pathlib import Path
    eval_path = storage.evals_dir / f"{run.eval_id}.yaml"
    try:
        eval_spec = EvalSpec.from_file(str(eval_path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid eval spec: {e}")
    
    # Start background execution
    background_tasks.add_task(execute_run, run_id, run.eval_id, eval_spec, run.tasks)
    
    return {
        "run_id": run_id,
        "eval_id": run.eval_id,
        "status": "queued",
    }


@router.get("/{run_id}/stream")
async def stream_run(run_id: str):
    """Stream run progress via Server-Sent Events."""
    
    async def event_generator():
        """Generate SSE events for run progress."""
        while True:
            if run_id not in active_runs:
                # Check if run is completed
                run_data = storage.get_run(run_id)
                if run_data:
                    yield f"data: {{'status': 'completed', 'run_id': '{run_id}'}}\n\n"
                    break
                else:
                    yield f"data: {{'status': 'not_found', 'run_id': '{run_id}'}}\n\n"
                    break
            
            status = active_runs[run_id]
            import json
            yield f"data: {json.dumps(status)}\n\n"
            
            if status.get("status") in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
