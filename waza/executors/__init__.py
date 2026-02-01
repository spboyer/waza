"""Executors for running skill evaluations."""

from waza.executors.base import BaseExecutor, ExecutionResult, SessionEvent
from waza.executors.mock import MockExecutor

__all__ = [
    "BaseExecutor",
    "ExecutionResult",
    "SessionEvent",
    "MockExecutor",
]

# Lazy import for optional Copilot SDK dependency
def get_copilot_executor():
    """Get CopilotExecutor if SDK is available."""
    try:
        from waza.executors.copilot import CopilotExecutor
        return CopilotExecutor
    except ImportError:
        return None
