"""Skills Eval Framework - Evaluate Agent Skills like you evaluate AI Agents."""

__version__ = "0.0.2"

from waza.executors import BaseExecutor, ExecutionResult, MockExecutor
from waza.graders.base import Grader, GraderType
from waza.runner import EvalRunner
from waza.schemas.eval_spec import EvalSpec, ExecutorType
from waza.schemas.results import (
    EvalResult,
    GraderResult,
    MetricResult,
    TaskResult,
    TrialResult,
)
from waza.schemas.task import Task, TaskExpected, TaskInput

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
