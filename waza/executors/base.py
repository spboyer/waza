"""Base executor interface for skill evaluation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionEvent:
    """Event from a skill execution session.

    Compatible with Copilot SDK session events.
    """

    type: str
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def message_id(self) -> str | None:
        return self.data.get("messageId")

    @property
    def content(self) -> str | None:
        return self.data.get("content")

    @property
    def delta_content(self) -> str | None:
        return self.data.get("deltaContent")

    @property
    def tool_name(self) -> str | None:
        return self.data.get("toolName")

    @property
    def tool_call_id(self) -> str | None:
        return self.data.get("toolCallId")

    @property
    def arguments(self) -> Any:
        return self.data.get("arguments")

    @property
    def success(self) -> bool | None:
        return self.data.get("success")


@dataclass
class ExecutionResult:
    """Result of executing a skill with a prompt."""

    # Core output
    output: str = ""

    # Session events (transcript)
    events: list[SessionEvent] = field(default_factory=list)

    # Metadata
    model: str = ""
    skill_name: str | None = None
    duration_ms: int = 0

    # Tool call tracking
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    # Error info
    error: str | None = None
    success: bool = True

    def get_assistant_messages(self) -> list[str]:
        """Get all assistant messages from events."""
        messages: dict[str, str] = {}

        for event in self.events:
            if event.type == "assistant.message" and event.message_id and event.content:
                messages[event.message_id] = event.content
            elif event.type == "assistant.message_delta" and event.message_id:
                if event.message_id in messages:
                    messages[event.message_id] += event.delta_content or ""
                else:
                    messages[event.message_id] = event.delta_content or ""

        return list(messages.values())

    def is_skill_invoked(self, skill_name: str) -> bool:
        """Check if a specific skill was invoked."""
        for event in self.events:
            if event.type == "tool.execution_start" and event.tool_name == "skill":
                args = event.arguments
                if args and skill_name in str(args):
                    return True
        return False

    def are_tool_calls_successful(self, tool_name: str | None = None) -> bool:
        """Check if tool calls were successful."""
        start_events = [
            e for e in self.events
            if e.type == "tool.execution_start"
            and (tool_name is None or e.tool_name == tool_name)
        ]

        if not start_events:
            return True  # No calls = vacuously true

        complete_events = [e for e in self.events if e.type == "tool.execution_complete"]

        for start in start_events:
            tool_call_id = start.tool_call_id
            completed = any(
                c.tool_call_id == tool_call_id and c.success
                for c in complete_events
            )
            if not completed:
                return False

        return True

    def contains_keyword(self, keyword: str, case_sensitive: bool = False) -> bool:
        """Check if output or assistant messages contain a keyword."""
        text = self.output + " ".join(self.get_assistant_messages())

        if case_sensitive:
            return keyword in text
        return keyword.lower() in text.lower()


class BaseExecutor(ABC):
    """Abstract base class for skill executors."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", **kwargs: Any):
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def execute(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        skill_name: str | None = None,
    ) -> ExecutionResult:
        """Execute a prompt and return the result.

        Args:
            prompt: The user prompt to send
            context: Additional context (files, workspace, etc.)
            skill_name: Expected skill to be invoked (for validation)

        Returns:
            ExecutionResult with output, events, and metadata
        """
        pass

    @abstractmethod
    async def setup(self) -> None:
        """Initialize the executor (create clients, etc.)."""
        pass

    @abstractmethod
    async def teardown(self) -> None:
        """Clean up resources."""
        pass

    async def __aenter__(self) -> BaseExecutor:
        await self.setup()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.teardown()
