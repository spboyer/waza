"""Mock executor for testing without real LLM calls."""

from __future__ import annotations

import asyncio
import random
from typing import Any

from waza.executors.base import BaseExecutor, ExecutionResult, SessionEvent


class MockExecutor(BaseExecutor):
    """Mock executor that generates synthetic responses.

    Useful for:
    - Unit testing eval framework
    - CI/CD pipelines without API keys
    - Rapid iteration on eval definitions
    """

    def __init__(
        self,
        model: str = "mock-model",
        latency_ms: int = 100,
        success_rate: float = 1.0,
        **kwargs: Any,
    ):
        super().__init__(model=model, **kwargs)
        self.latency_ms = latency_ms
        self.success_rate = success_rate
        self._responses: dict[str, str] = {}

    def set_response(self, prompt_pattern: str, response: str) -> None:
        """Set a canned response for prompts matching a pattern."""
        self._responses[prompt_pattern.lower()] = response

    async def setup(self) -> None:
        """No setup needed for mock executor."""
        pass

    async def teardown(self) -> None:
        """No teardown needed for mock executor."""
        pass

    async def execute(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        skill_name: str | None = None,
    ) -> ExecutionResult:
        """Generate a mock response."""
        # Simulate latency
        if self.latency_ms > 0:
            await asyncio.sleep(self.latency_ms / 1000)

        # Check for failure simulation
        if random.random() > self.success_rate:
            return ExecutionResult(
                output="",
                model=self.model,
                skill_name=skill_name,
                duration_ms=self.latency_ms,
                error="Simulated failure",
                success=False,
            )

        # Look for canned response
        output = self._find_response(prompt, context)

        # Generate events
        events = self._generate_events(prompt, output, skill_name)

        # Extract tool calls from events
        tool_calls = [
            {"name": e.tool_name, "arguments": e.arguments}
            for e in events
            if e.type == "tool.execution_start"
        ]

        return ExecutionResult(
            output=output,
            events=events,
            model=self.model,
            skill_name=skill_name,
            duration_ms=self.latency_ms,
            tool_calls=tool_calls,
            success=True,
        )

    def _find_response(self, prompt: str, context: dict[str, Any] | None) -> str:
        """Find a matching canned response or generate default."""
        prompt_lower = prompt.lower()

        # Check for exact or partial matches
        for pattern, response in self._responses.items():
            if pattern in prompt_lower:
                return response

        # Default mock response
        return f"Mock response for: {prompt[:50]}..."

    def _generate_events(
        self,
        prompt: str,
        output: str,
        skill_name: str | None,
    ) -> list[SessionEvent]:
        """Generate mock session events."""
        events: list[SessionEvent] = []

        # User message event
        events.append(SessionEvent(
            type="user.message",
            data={"content": prompt, "messageId": "msg_001"},
        ))

        # Skill invocation (if skill expected)
        if skill_name:
            events.append(SessionEvent(
                type="tool.execution_start",
                data={
                    "toolName": "skill",
                    "toolCallId": "call_001",
                    "arguments": {"skill": skill_name},
                },
            ))
            events.append(SessionEvent(
                type="tool.execution_complete",
                data={
                    "toolCallId": "call_001",
                    "success": True,
                },
            ))

        # Assistant response
        events.append(SessionEvent(
            type="assistant.message",
            data={"content": output, "messageId": "msg_002"},
        ))

        # Session complete
        events.append(SessionEvent(
            type="session.idle",
            data={},
        ))

        return events
