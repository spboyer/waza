"""Data models for eval results."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GraderResult(BaseModel):
    """Result from a single grader."""

    name: str = Field(..., description="Grader name")
    type: str = Field(..., description="Grader type (code/llm/human)")
    score: float = Field(..., ge=0.0, le=1.0, description="Score from 0-1")
    passed: bool = Field(..., description="Whether the grader passed")
    message: str = Field(default="", description="Human-readable result message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")
    duration_ms: int = Field(default=0, description="Time taken to grade in milliseconds")


class TranscriptSummary(BaseModel):
    """Summary of a skill execution transcript."""

    total_turns: int = Field(default=0, description="Number of conversation turns")
    tool_calls: int = Field(default=0, description="Total tool calls made")
    tokens_input: int = Field(default=0, description="Input tokens used")
    tokens_output: int = Field(default=0, description="Output tokens used")
    tokens_total: int = Field(default=0, description="Total tokens used")
    tools_used: list[str] = Field(default_factory=list, description="List of tools used")
    errors: list[str] = Field(default_factory=list, description="Errors encountered")


class TrialResult(BaseModel):
    """Result from a single trial of a task."""

    trial_id: int = Field(..., description="Trial number (1-indexed)")
    status: str = Field(..., description="Trial status (passed/failed/error/timeout)")
    duration_ms: int = Field(default=0, description="Trial duration in milliseconds")
    grader_results: dict[str, GraderResult] = Field(
        default_factory=dict, description="Results from each grader"
    )
    transcript_summary: TranscriptSummary = Field(
        default_factory=TranscriptSummary, description="Summary of execution transcript"
    )
    transcript: list[dict[str, Any]] | None = Field(
        default=None, description="Full transcript (if captured)"
    )
    output: str = Field(default="", description="Final output from the skill")
    error: str | None = Field(default=None, description="Error message if failed")

    @property
    def score(self) -> float:
        """Calculate average score across graders."""
        if not self.grader_results:
            return 0.0
        scores = [g.score for g in self.grader_results.values()]
        return sum(scores) / len(scores)

    @property
    def passed(self) -> bool:
        """Check if all graders passed."""
        if not self.grader_results:
            return self.status == "passed"
        return all(g.passed for g in self.grader_results.values())


class TaskAggregate(BaseModel):
    """Aggregate statistics for a task across trials."""

    pass_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of trials that passed")
    mean_score: float = Field(..., ge=0.0, le=1.0, description="Mean score across trials")
    min_score: float = Field(..., ge=0.0, le=1.0, description="Minimum score")
    max_score: float = Field(..., ge=0.0, le=1.0, description="Maximum score")
    mean_duration_ms: int = Field(default=0, description="Mean duration in milliseconds")


class TaskResult(BaseModel):
    """Result for a single task across all trials."""

    id: str = Field(..., description="Task ID")
    name: str = Field(..., description="Task name")
    status: str = Field(..., description="Overall status (passed/failed/error)")
    trials: list[TrialResult] = Field(default_factory=list, description="Results from each trial")
    aggregate: TaskAggregate | None = Field(default=None, description="Aggregate statistics")

    def compute_aggregate(self) -> None:
        """Compute aggregate statistics from trials."""
        if not self.trials:
            return

        scores = [t.score for t in self.trials]
        passed_count = sum(1 for t in self.trials if t.passed)
        durations = [t.duration_ms for t in self.trials]

        self.aggregate = TaskAggregate(
            pass_rate=passed_count / len(self.trials),
            mean_score=sum(scores) / len(scores),
            min_score=min(scores),
            max_score=max(scores),
            mean_duration_ms=int(sum(durations) / len(durations)),
        )


class MetricResult(BaseModel):
    """Result for a single metric."""

    name: str = Field(..., description="Metric name")
    score: float = Field(..., ge=0.0, le=1.0, description="Metric score")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Pass threshold")
    passed: bool = Field(..., description="Whether metric passed threshold")
    weight: float = Field(default=1.0, description="Weight in composite score")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")


class EvalSummary(BaseModel):
    """Summary statistics for an eval run."""

    total_tasks: int = Field(..., description="Total number of tasks")
    passed: int = Field(..., description="Number of tasks passed")
    failed: int = Field(..., description="Number of tasks failed")
    errors: int = Field(default=0, description="Number of tasks with errors")
    skipped: int = Field(default=0, description="Number of tasks skipped")
    pass_rate: float = Field(..., ge=0.0, le=1.0, description="Overall pass rate")
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Weighted composite score")
    duration_ms: int = Field(default=0, description="Total duration in milliseconds")


class EvalConfig(BaseModel):
    """Configuration used for the eval run."""

    trials_per_task: int = Field(default=1, description="Trials per task")
    model: str = Field(default="", description="Model used for execution")
    executor: str = Field(default="mock", description="Executor type used")
    timeout_seconds: int = Field(default=300, description="Timeout per trial")


class EvalResult(BaseModel):
    """Complete result for an eval run."""

    eval_id: str = Field(..., description="Unique eval run identifier")
    skill: str = Field(..., description="Skill that was evaluated")
    eval_name: str = Field(..., description="Name of the eval suite")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When eval was run")
    config: EvalConfig = Field(default_factory=EvalConfig, description="Eval configuration")
    summary: EvalSummary = Field(..., description="Summary statistics")
    metrics: dict[str, MetricResult] = Field(
        default_factory=dict, description="Results for each metric"
    )
    tasks: list[TaskResult] = Field(default_factory=list, description="Results for each task")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> EvalResult:
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)

    def to_file(self, path: str) -> None:
        """Write results to JSON file."""
        from pathlib import Path

        Path(path).write_text(self.to_json())

    @classmethod
    def from_file(cls, path: str) -> EvalResult:
        """Load results from JSON file."""
        from pathlib import Path

        return cls.from_json(Path(path).read_text())
