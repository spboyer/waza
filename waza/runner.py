"""Eval runner - orchestrates task execution and grading."""

from __future__ import annotations

import asyncio
import contextlib
import glob
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from waza.executors import BaseExecutor, MockExecutor
from waza.graders.base import Grader, GraderContext, GraderRegistry
from waza.schemas.eval_spec import EvalSpec, ExecutorType
from waza.schemas.results import (
    EvalConfig as ResultEvalConfig,
)
from waza.schemas.results import (
    EvalResult,
    EvalSummary,
    MetricResult,
    TaskResult,
    TranscriptSummary,
    TrialResult,
)
from waza.schemas.task import Task


class ProgressCallback(Protocol):
    """Protocol for progress callbacks."""

    def __call__(
        self,
        event: str,
        task_name: str | None = None,
        task_num: int | None = None,
        total_tasks: int | None = None,
        trial_num: int | None = None,
        total_trials: int | None = None,
        status: str | None = None,
        duration_ms: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Report progress."""
        ...


class EvalRunner:
    """Orchestrates evaluation execution."""

    def __init__(
        self,
        spec: EvalSpec,
        executor: BaseExecutor | Callable[[Task], tuple[str, list[dict], dict]] | None = None,
        base_path: Path | None = None,
        progress_callback: ProgressCallback | None = None,
        context_dir: str | None = None,
    ):
        """Initialize eval runner.

        Args:
            spec: The eval specification
            executor: Optional executor instance or legacy callable
            base_path: Base path for resolving relative paths in spec
            progress_callback: Optional callback for progress updates
            context_dir: Optional directory with project files to use as context
        """
        self.spec = spec
        self._legacy_executor = None
        self._executor: BaseExecutor | None = None
        self._progress_callback = progress_callback
        self._context_dir = context_dir

        # Handle different executor types
        if executor is None:
            # Create executor based on spec config
            self._executor = self._create_executor()
        elif isinstance(executor, BaseExecutor):
            self._executor = executor
        else:
            # Legacy callable executor
            self._legacy_executor = executor

        self.base_path = base_path or Path.cwd()
        self._graders: dict[str, Grader] = {}
        self._setup_graders()

    def _report_progress(self, event: str, **kwargs) -> None:
        """Report progress if callback is set."""
        if self._progress_callback:
            self._progress_callback(event, **kwargs)

    def _create_executor(self) -> BaseExecutor:
        """Create executor based on spec configuration."""
        executor_type = self.spec.config.executor
        model = self.spec.config.model

        if executor_type == ExecutorType.COPILOT_SDK:
            # Try to import Copilot executor
            try:
                from waza.executors.copilot import CopilotExecutor
                return CopilotExecutor(
                    model=model,
                    skill_directories=self.spec.config.skill_directories,
                    mcp_servers=self.spec.config.mcp_servers,
                    timeout_seconds=self.spec.config.timeout_seconds,
                )
            except ImportError as e:
                raise ImportError(
                    "Copilot SDK executor requires copilot-sdk package. "
                    "Install with: pip install skill-eval[copilot]"
                ) from e
        else:
            # Default to mock executor
            return MockExecutor(model=model)

    def _setup_graders(self) -> None:
        """Initialize graders from spec."""
        for grader_config in self.spec.graders:
            grader = GraderRegistry.create(
                grader_type=grader_config.type.value,
                name=grader_config.name,
                config={
                    "script": grader_config.script,
                    "rubric": grader_config.rubric,
                    "model": grader_config.model,
                    **grader_config.config,
                },
            )
            self._graders[grader_config.name] = grader

    def load_tasks(self) -> list[Task]:
        """Load all tasks from spec patterns."""
        tasks = []

        for pattern in self.spec.tasks:
            if pattern.startswith("include:"):
                pattern = pattern.replace("include:", "").strip()

            # Resolve glob pattern
            task_files = glob.glob(str(self.base_path / pattern))

            for task_file in task_files:
                task = Task.from_file(task_file)
                if task.enabled:
                    tasks.append(task)

        return tasks

    def run(self, tasks: list[Task] | None = None) -> EvalResult:
        """Run evaluation synchronously."""
        return asyncio.run(self.run_async(tasks))

    async def run_async(self, tasks: list[Task] | None = None) -> EvalResult:
        """Run evaluation asynchronously."""
        start_time = time.time()

        if tasks is None:
            tasks = self.load_tasks()

        eval_id = f"{self.spec.name}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

        # Run tasks
        if self.spec.config.parallel:
            task_results = await self._run_tasks_parallel(tasks)
        else:
            task_results = await self._run_tasks_sequential(tasks)

        # Compute metrics
        metrics = self._compute_metrics(task_results)

        # Build summary
        passed_count = sum(1 for t in task_results if t.status == "passed")
        failed_count = sum(1 for t in task_results if t.status == "failed")
        error_count = sum(1 for t in task_results if t.status == "error")

        # Composite score from weighted metrics
        composite_score = self._compute_composite_score(metrics)

        summary = EvalSummary(
            total_tasks=len(task_results),
            passed=passed_count,
            failed=failed_count,
            errors=error_count,
            skipped=0,
            pass_rate=passed_count / len(task_results) if task_results else 0.0,
            composite_score=composite_score,
            duration_ms=int((time.time() - start_time) * 1000),
        )

        return EvalResult(
            eval_id=eval_id,
            skill=self.spec.skill,
            eval_name=self.spec.name,
            timestamp=datetime.utcnow(),
            config=ResultEvalConfig(
                trials_per_task=self.spec.config.trials_per_task,
                model=self.spec.config.model,
                executor=self.spec.config.executor.value,
                timeout_seconds=self.spec.config.timeout_seconds,
            ),
            summary=summary,
            metrics=metrics,
            tasks=task_results,
        )

    async def _run_tasks_sequential(self, tasks: list[Task]) -> list[TaskResult]:
        """Run tasks one at a time."""
        results = []
        total = len(tasks)

        for i, task in enumerate(tasks, 1):
            self._report_progress(
                "task_start",
                task_name=task.name,
                task_num=i,
                total_tasks=total,
            )

            result = await self._run_task(task, task_num=i, total_tasks=total)
            results.append(result)

            self._report_progress(
                "task_complete",
                task_name=task.name,
                task_num=i,
                total_tasks=total,
                status=result.status,
                duration_ms=result.aggregate.mean_duration_ms if result.aggregate else 0,
                details={"score": result.aggregate.mean_score if result.aggregate else 0},
            )

            if self.spec.config.fail_fast and result.status == "failed":
                break
        return results

    async def _run_tasks_parallel(self, tasks: list[Task]) -> list[TaskResult]:
        """Run tasks in parallel."""
        semaphore = asyncio.Semaphore(self.spec.config.max_workers)
        total = len(tasks)
        completed = 0

        async def run_with_semaphore(task: Task, task_num: int) -> TaskResult:
            nonlocal completed
            async with semaphore:
                self._report_progress(
                    "task_start",
                    task_name=task.name,
                    task_num=task_num,
                    total_tasks=total,
                )

                result = await self._run_task(task, task_num=task_num, total_tasks=total)
                completed += 1

                self._report_progress(
                    "task_complete",
                    task_name=task.name,
                    task_num=completed,
                    total_tasks=total,
                    status=result.status,
                    duration_ms=result.aggregate.mean_duration_ms if result.aggregate else 0,
                )

                return result

        return await asyncio.gather(*[run_with_semaphore(t, i) for i, t in enumerate(tasks, 1)])

    async def _run_task(self, task: Task, task_num: int = 0, total_tasks: int = 0) -> TaskResult:
        """Run a single task with all trials."""
        trials = []
        total_trials = self.spec.config.trials_per_task

        for trial_num in range(1, total_trials + 1):
            self._report_progress(
                "trial_start",
                task_name=task.name,
                task_num=task_num,
                total_tasks=total_tasks,
                trial_num=trial_num,
                total_trials=total_trials,
            )

            trial = await self._run_trial(task, trial_num)
            trials.append(trial)

            self._report_progress(
                "trial_complete",
                task_name=task.name,
                task_num=task_num,
                total_tasks=total_tasks,
                trial_num=trial_num,
                total_trials=total_trials,
                status=trial.status,
                duration_ms=trial.duration_ms,
            )

        # Determine overall status
        passed_trials = sum(1 for t in trials if t.passed)
        if passed_trials == len(trials):
            status = "passed"
        elif passed_trials > 0:
            status = "partial"
        else:
            status = "failed"

        result = TaskResult(
            id=task.id,
            name=task.name,
            status=status,
            trials=trials,
        )
        result.compute_aggregate()

        return result

    async def _run_trial(self, task: Task, trial_num: int) -> TrialResult:
        """Run a single trial of a task."""
        start_time = time.time()

        try:
            # Build context including context_dir files if provided
            exec_context = {}
            if task.inputs.files:
                exec_context["files"] = task.inputs.files

            # Determine context_dir: task-specific overrides global
            effective_context_dir = task.context_dir or self._context_dir

            if effective_context_dir:
                exec_context["context_dir"] = effective_context_dir
                # Read actual files FRESH from context_dir for each task
                # This ensures isolation - each task sees the original fixtures,
                # not modifications made by previous tasks (which are in temp workspaces)
                context_path = Path(effective_context_dir)
                if context_path.exists():
                    project_files = []
                    for ext in ["*.py", "*.js", "*.ts", "*.json", "*.yaml", "*.yml", "*.md"]:
                        for f in context_path.glob(f"**/{ext}"):
                            if f.is_file() and f.stat().st_size < 50000:  # Skip large files
                                with contextlib.suppress(Exception):
                                    project_files.append({
                                        "path": str(f.relative_to(context_path)),
                                        "content": f.read_text()[:5000],  # Truncate
                                    })
                    if project_files:
                        exec_context["project_files"] = project_files[:20]  # Limit files

            # Emit user message event
            self._report_progress(
                "message",
                task_name=task.name,
                trial_num=trial_num,
                details={"role": "user", "content": task.inputs.prompt},
            )

            # Execute the task
            if self._legacy_executor:
                # Legacy callable executor
                output, transcript, outcome = self._legacy_executor(task)
            elif self._executor:
                # New executor interface
                result = await self._executor.execute(
                    prompt=task.inputs.prompt,
                    context=exec_context if exec_context else None,
                    skill_name=self.spec.skill,
                )
                output = result.output
                transcript = [e.__dict__ for e in result.events] if result.events else []
                outcome = {
                    "status": "completed" if result.success else "failed",
                    "error": result.error,
                    "tool_calls": result.tool_calls,
                }

                # Emit message events for real-time display
                for event in result.events or []:
                    if event.type == "assistant.message":
                        self._report_progress(
                            "message",
                            task_name=task.name,
                            trial_num=trial_num,
                            details={"role": "assistant", "content": event.data.get("content", "")},
                        )
                    elif event.type.startswith("tool."):
                        tool_name = event.data.get("toolName") or event.data.get("tool_name") or event.data.get("name") or "tool"
                        self._report_progress(
                            "message",
                            task_name=task.name,
                            trial_num=trial_num,
                            details={
                                "role": "tool",
                                "name": tool_name,
                                "content": str(event.data.get("arguments", ""))[:200],
                            },
                        )
            else:
                output, transcript, outcome = self._mock_execution(task)
                # Emit mock response event
                self._report_progress(
                    "message",
                    task_name=task.name,
                    trial_num=trial_num,
                    details={"role": "assistant", "content": output[:200]},
                )

            # Build conversation transcript (normalized format for graders and display)
            conversation = []
            for event in transcript:
                event_type = event.get("type", "")
                data = event.get("data", {})
                if event_type == "user.message":
                    conversation.append({"role": "user", "content": data.get("content", "")})
                elif event_type == "assistant.message":
                    conversation.append({"role": "assistant", "content": data.get("content", "")})
                elif event_type.startswith("tool."):
                    # Try both camelCase and snake_case for tool name
                    tool_name = data.get("toolName") or data.get("tool_name") or data.get("name") or "tool"
                    conversation.append({"role": "tool", "name": tool_name, "content": str(data.get("arguments", data))[:500]})

            # Build grading context with normalized transcript
            context = GraderContext(
                task=task.model_dump(),
                transcript=conversation,  # Use normalized conversation, not raw events
                output=output,
                outcome=outcome,
                duration_ms=int((time.time() - start_time) * 1000),
            )

            # Run all graders
            grader_results = {}
            for grader_name, grader in self._graders.items():
                grader_results[grader_name] = grader.grade(context)

            # Also run task-specific graders
            for task_grader in task.graders:
                grader = GraderRegistry.create(
                    grader_type=task_grader.type,
                    name=task_grader.name,
                    config={"assertions": task_grader.assertions, "rubric": task_grader.rubric},
                )
                grader_results[task_grader.name] = grader.grade(context)

            # Build transcript summary from raw events
            tool_calls = [t for t in transcript if t.get("type") == "tool_call" or t.get("type", "").startswith("tool.")]
            transcript_summary = TranscriptSummary(
                total_turns=len(transcript),
                tool_calls=len(tool_calls),
                tools_used=list({t.get("tool", t.get("data", {}).get("toolName", "")) for t in tool_calls if t.get("tool") or t.get("data", {}).get("toolName")}),
            )

            # Determine trial status
            all_passed = all(g.passed for g in grader_results.values()) if grader_results else True

            return TrialResult(
                trial_id=trial_num,
                status="passed" if all_passed else "failed",
                duration_ms=int((time.time() - start_time) * 1000),
                grader_results=grader_results,
                transcript_summary=transcript_summary,
                transcript=conversation if conversation else None,
                output=output,
            )

        except TimeoutError:
            return TrialResult(
                trial_id=trial_num,
                status="timeout",
                duration_ms=int((time.time() - start_time) * 1000),
                grader_results={},
                error="Trial timed out",
            )
        except Exception as e:
            return TrialResult(
                trial_id=trial_num,
                status="error",
                duration_ms=int((time.time() - start_time) * 1000),
                grader_results={},
                error=str(e),
            )

    def _mock_execution(self, task: Task) -> tuple[str, list[dict], dict]:
        """Mock execution for testing without a real executor."""
        # Return simulated successful execution
        return (
            f"Mock output for task: {task.name}",
            [
                {"type": "tool_call", "tool": "mock_tool", "args": {}},
                {"type": "response", "content": "Mock response"},
            ],
            {"status": "completed"},
        )

    def _compute_metrics(self, task_results: list[TaskResult]) -> dict[str, MetricResult]:
        """Compute all configured metrics."""
        metrics = {}

        for metric_config in self.spec.metrics:
            if not metric_config.enabled:
                continue

            # Calculate metric score based on task results
            if metric_config.name == "task_completion":
                score = self._calc_task_completion(task_results)
            elif metric_config.name == "trigger_accuracy":
                score = self._calc_trigger_accuracy(task_results)
            elif metric_config.name == "behavior_quality":
                score = self._calc_behavior_quality(task_results)
            else:
                # Default: use pass rate
                score = sum(1 for t in task_results if t.status == "passed") / len(task_results) if task_results else 0.0

            metrics[metric_config.name] = MetricResult(
                name=metric_config.name,
                score=score,
                threshold=metric_config.threshold,
                passed=score >= metric_config.threshold,
                weight=metric_config.weight,
            )

        return metrics

    def _calc_task_completion(self, task_results: list[TaskResult]) -> float:
        """Calculate task completion metric."""
        if not task_results:
            return 0.0

        completed = sum(1 for t in task_results if t.status in ("passed", "partial"))
        return completed / len(task_results)

    def _calc_trigger_accuracy(self, task_results: list[TaskResult]) -> float:
        """Calculate trigger accuracy metric (placeholder)."""
        # This would be calculated from trigger test results
        # For now, use pass rate as proxy
        if not task_results:
            return 0.0
        return sum(1 for t in task_results if t.status == "passed") / len(task_results)

    def _calc_behavior_quality(self, task_results: list[TaskResult]) -> float:
        """Calculate behavior quality metric."""
        if not task_results:
            return 0.0

        # Average the grader scores across all trials
        scores = []
        for task in task_results:
            for trial in task.trials:
                if trial.grader_results:
                    trial_score = sum(g.score for g in trial.grader_results.values()) / len(trial.grader_results)
                    scores.append(trial_score)

        return sum(scores) / len(scores) if scores else 0.0

    def _compute_composite_score(self, metrics: dict[str, MetricResult]) -> float:
        """Compute weighted composite score from metrics."""
        if not metrics:
            return 0.0

        total_weight = sum(m.weight for m in metrics.values())
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(m.score * m.weight for m in metrics.values())
        return weighted_sum / total_weight
