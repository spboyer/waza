"""JSON-RPC method handlers."""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

from waza.jsonrpc.protocol import JSONRPCError, JSONRPCException
from waza.runner import EvalRunner
from waza.schemas.eval_spec import EvalSpec

logger = logging.getLogger(__name__)


class RunManager:
    """Manages running eval executions."""

    def __init__(self):
        """Initialize run manager."""
        self._runs: dict[str, dict[str, Any]] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def create_run(self, run_id: str, spec: EvalSpec, params: dict[str, Any]) -> None:
        """Create a new run.
        
        Args:
            run_id: Unique run identifier.
            spec: Eval specification.
            params: Run parameters.
        """
        self._runs[run_id] = {
            "id": run_id,
            "status": "running",
            "spec": spec,
            "params": params,
            "result": None,
            "error": None,
        }

    def update_run_status(self, run_id: str, status: str, result: Any = None, error: str | None = None) -> None:
        """Update run status.
        
        Args:
            run_id: Run identifier.
            status: New status.
            result: Run result (if complete).
            error: Error message (if failed).
        """
        if run_id in self._runs:
            self._runs[run_id]["status"] = status
            if result is not None:
                self._runs[run_id]["result"] = result
            if error is not None:
                self._runs[run_id]["error"] = error

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Get run information.
        
        Args:
            run_id: Run identifier.
            
        Returns:
            Run information, or None if not found.
        """
        return self._runs.get(run_id)

    def add_task(self, run_id: str, task: asyncio.Task) -> None:
        """Add an async task for a run.
        
        Args:
            run_id: Run identifier.
            task: Async task.
        """
        self._tasks[run_id] = task

    def cancel_run(self, run_id: str) -> bool:
        """Cancel a running eval.
        
        Args:
            run_id: Run identifier.
            
        Returns:
            True if cancelled, False if not found or not running.
        """
        if run_id not in self._runs:
            return False
        
        if run_id in self._tasks:
            self._tasks[run_id].cancel()
            self.update_run_status(run_id, "cancelled")
            return True
        
        return False

    def cleanup_task(self, run_id: str) -> None:
        """Remove task reference after completion.
        
        Args:
            run_id: Run identifier.
        """
        if run_id in self._tasks:
            del self._tasks[run_id]


class MethodHandler:
    """Handles JSON-RPC method calls."""

    def __init__(self, notification_callback: Any = None):
        """Initialize method handler.
        
        Args:
            notification_callback: Callback for sending notifications.
        """
        self._run_manager = RunManager()
        self._notification_callback = notification_callback

    async def _send_notification(self, method: str, params: dict[str, Any]) -> None:
        """Send a notification to the client.
        
        Args:
            method: Notification method name.
            params: Notification parameters.
        """
        if self._notification_callback:
            await self._notification_callback(method, params)

    async def handle_eval_run(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle eval.run method.
        
        Args:
            params: Method parameters.
            
        Returns:
            Run information.
        """
        # Validate parameters
        if "path" not in params:
            raise JSONRPCException(JSONRPCError.invalid_params("missing 'path' parameter")
)
        
        eval_path = params["path"]
        
        # Check if eval file exists
        if not Path(eval_path).exists():
            raise JSONRPCException(JSONRPCError.eval_not_found(eval_path)
)
        
        # Load eval spec
        try:
            spec = EvalSpec.from_file(eval_path)
        except Exception as e:
            errors = [str(e)]
            raise JSONRPCException(JSONRPCError.validation_failed(errors)
)
        
        # Apply parameter overrides
        if "executor" in params:
            from waza.schemas.eval_spec import ExecutorType
            spec.config.executor = ExecutorType(params["executor"])
        if "model" in params:
            spec.config.model = params["model"]
        if "verbose" in params:
            spec.config.verbose = params["verbose"]
        
        # Generate run ID
        run_id = str(uuid.uuid4())
        
        # Create run
        self._run_manager.create_run(run_id, spec, params)
        
        # Start async execution
        task = asyncio.create_task(self._run_eval(run_id, spec, eval_path, params))
        self._run_manager.add_task(run_id, task)
        
        return {
            "runId": run_id,
            "status": "running",
        }

    async def _run_eval(self, run_id: str, spec: EvalSpec, eval_path: str, params: dict[str, Any]) -> None:
        """Run eval asynchronously.
        
        Args:
            run_id: Run identifier.
            spec: Eval specification.
            eval_path: Path to eval file.
            params: Run parameters.
        """
        try:
            # Create progress callback
            def progress_callback(event: str, **kwargs) -> None:
                # Send progress notification
                asyncio.create_task(self._send_notification("eval.progress", {
                    "runId": run_id,
                    "event": event,
                    **kwargs,
                }))
            
            # Create runner
            base_path = Path(eval_path).parent
            context_dir = params.get("context_dir")
            runner = EvalRunner(spec, base_path=base_path, progress_callback=progress_callback, context_dir=context_dir)
            
            # Run eval
            result = await runner.run_async()
            
            # Update run status
            self._run_manager.update_run_status(run_id, "complete", result=result.model_dump())
            
            # Send completion notification
            await self._send_notification("eval.complete", {
                "runId": run_id,
                "summary": {
                    "total": result.summary.total_tasks,
                    "passed": result.summary.tasks_passed,
                    "failed": result.summary.tasks_failed,
                    "passRate": result.summary.pass_rate,
                },
            })
        except asyncio.CancelledError:
            self._run_manager.update_run_status(run_id, "cancelled")
            raise
        except Exception as e:
            logger.exception(f"Error running eval: {e}")
            self._run_manager.update_run_status(run_id, "failed", error=str(e))
            await self._send_notification("eval.complete", {
                "runId": run_id,
                "error": str(e),
            })
        finally:
            self._run_manager.cleanup_task(run_id)

    async def handle_eval_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle eval.list method.
        
        Args:
            params: Method parameters.
            
        Returns:
            List of available evals.
        """
        # Validate parameters
        if "directory" not in params:
            raise JSONRPCException(JSONRPCError.invalid_params("missing 'directory' parameter"))
        
        directory = Path(params["directory"])
        if not directory.exists():
            raise JSONRPCException(JSONRPCError.eval_not_found(str(directory)))
        
        # Find eval.yaml files
        evals = []
        for eval_file in directory.rglob("eval.yaml"):
            try:
                spec = EvalSpec.from_file(str(eval_file))
                evals.append({
                    "path": str(eval_file),
                    "name": spec.name,
                    "skill": spec.skill,
                    "version": spec.version,
                })
            except Exception as e:
                logger.warning(f"Failed to load eval {eval_file}: {e}")
        
        return {"evals": evals}

    async def handle_eval_get(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle eval.get method.
        
        Args:
            params: Method parameters.
            
        Returns:
            Eval details.
        """
        # Validate parameters
        if "path" not in params:
            raise JSONRPCException(JSONRPCError.invalid_params("missing 'path' parameter"))
        
        eval_path = params["path"]
        
        # Check if eval file exists
        if not Path(eval_path).exists():
            raise JSONRPCException(JSONRPCError.eval_not_found(eval_path))
        
        # Load eval spec
        try:
            spec = EvalSpec.from_file(eval_path)
        except Exception as e:
            raise JSONRPCError.validation_failed([str(e)])
        
        return {
            "path": eval_path,
            "name": spec.name,
            "skill": spec.skill,
            "version": spec.version,
            "config": spec.config.model_dump(),
            "metrics": spec.metrics.model_dump() if spec.metrics else None,
        }

    async def handle_eval_validate(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle eval.validate method.
        
        Args:
            params: Method parameters.
            
        Returns:
            Validation result.
        """
        # Validate parameters
        if "path" not in params:
            raise JSONRPCException(JSONRPCError.invalid_params("missing 'path' parameter"))
        
        eval_path = params["path"]
        
        # Check if eval file exists
        if not Path(eval_path).exists():
            raise JSONRPCException(JSONRPCError.eval_not_found(eval_path))
        
        # Try to load eval spec
        errors = []
        try:
            spec = EvalSpec.from_file(eval_path)
            return {
                "valid": True,
                "name": spec.name,
                "skill": spec.skill,
            }
        except Exception as e:
            errors.append(str(e))
            return {
                "valid": False,
                "errors": errors,
            }

    async def handle_task_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle task.list method.
        
        Args:
            params: Method parameters.
            
        Returns:
            List of tasks for an eval.
        """
        # Validate parameters
        if "path" not in params:
            raise JSONRPCException(JSONRPCError.invalid_params("missing 'path' parameter"))
        
        eval_path = params["path"]
        
        # Check if eval file exists
        if not Path(eval_path).exists():
            raise JSONRPCException(JSONRPCError.eval_not_found(eval_path))
        
        # Load eval spec
        try:
            spec = EvalSpec.from_file(eval_path)
        except Exception as e:
            raise JSONRPCError.validation_failed([str(e)])
        
        # Get tasks
        base_path = Path(eval_path).parent
        tasks = []
        for task_spec in spec.tasks:
            task_path = base_path / task_spec.file
            try:
                from waza.schemas.task import Task
                task = Task.from_file(str(task_path))
                tasks.append({
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "file": task_spec.file,
                })
            except Exception as e:
                logger.warning(f"Failed to load task {task_path}: {e}")
        
        return {"tasks": tasks}

    async def handle_task_get(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle task.get method.
        
        Args:
            params: Method parameters.
            
        Returns:
            Task details.
        """
        # Validate parameters
        if "path" not in params:
            raise JSONRPCException(JSONRPCError.invalid_params("missing 'path' parameter"))
        if "taskId" not in params:
            raise JSONRPCException(JSONRPCError.invalid_params("missing 'taskId' parameter"))
        
        eval_path = params["path"]
        task_id = params["taskId"]
        
        # Check if eval file exists
        if not Path(eval_path).exists():
            raise JSONRPCException(JSONRPCError.eval_not_found(eval_path))
        
        # Load eval spec
        try:
            spec = EvalSpec.from_file(eval_path)
        except Exception as e:
            raise JSONRPCError.validation_failed([str(e)])
        
        # Find task
        base_path = Path(eval_path).parent
        for task_spec in spec.tasks:
            task_path = base_path / task_spec.file
            try:
                from waza.schemas.task import Task
                task = Task.from_file(str(task_path))
                if task.id == task_id:
                    return {
                        "id": task.id,
                        "name": task.name,
                        "description": task.description,
                        "prompt": task.prompt,
                        "graders": [g.model_dump() for g in task.graders] if task.graders else [],
                    }
            except Exception as e:
                logger.warning(f"Failed to load task {task_path}: {e}")
        
        raise JSONRPCException(JSONRPCError.invalid_params(f"task '{task_id}' not found"))

    async def handle_run_status(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle run.status method.
        
        Args:
            params: Method parameters.
            
        Returns:
            Run status.
        """
        # Validate parameters
        if "runId" not in params:
            raise JSONRPCException(JSONRPCError.invalid_params("missing 'runId' parameter"))
        
        run_id = params["runId"]
        
        # Get run
        run = self._run_manager.get_run(run_id)
        if not run:
            raise JSONRPCException(JSONRPCError.invalid_params(f"run '{run_id}' not found"))
        
        return {
            "runId": run_id,
            "status": run["status"],
            "result": run.get("result"),
            "error": run.get("error"),
        }

    async def handle_run_cancel(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle run.cancel method.
        
        Args:
            params: Method parameters.
            
        Returns:
            Cancel result.
        """
        # Validate parameters
        if "runId" not in params:
            raise JSONRPCException(JSONRPCError.invalid_params("missing 'runId' parameter"))
        
        run_id = params["runId"]
        
        # Cancel run
        cancelled = self._run_manager.cancel_run(run_id)
        
        if not cancelled:
            raise JSONRPCException(JSONRPCError.invalid_params(f"run '{run_id}' not found or not running"))
        
        return {
            "runId": run_id,
            "status": "cancelled",
        }
