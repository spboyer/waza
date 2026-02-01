"""Skills Eval Framework - Evaluate Agent Skills like you evaluate AI Agents."""

__version__ = "0.0.1"

from skill_eval.schemas.eval_spec import EvalSpec, ExecutorType
from skill_eval.schemas.task import Task, TaskInput, TaskExpected
from skill_eval.schemas.results import (
    EvalResult,
    TaskResult,
    TrialResult,
    GraderResult,
    MetricResult,
)
from skill_eval.runner import EvalRunner
from skill_eval.graders.base import Grader, GraderType
from skill_eval.executors import BaseExecutor, ExecutionResult, MockExecutor

__all__ = [
    "__version__",
    "EvalSpec",
    "ExecutorType",
    "Task",
    "TaskInput",
    "TaskExpected",
    "EvalResult",
    "TaskResult",
    "TrialResult",
    "GraderResult",
    "MetricResult",
    "EvalRunner",
    "Grader",
    "GraderType",
    "BaseExecutor",
    "ExecutionResult",
    "MockExecutor",
]
