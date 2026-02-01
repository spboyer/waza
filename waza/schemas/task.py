"""Data models for tasks (test cases)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FileContext(BaseModel):
    """File context for a task."""

    path: str = Field(..., description="Path to the file")
    content: str | None = Field(default=None, description="File content (if inline)")


class TaskInput(BaseModel):
    """Input specification for a task."""

    prompt: str = Field(..., description="The prompt/request to the skill")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    files: list[FileContext | str] = Field(default_factory=list, description="Files in context")
    environment: dict[str, str] = Field(default_factory=dict, description="Environment variables")


class ToolCallPattern(BaseModel):
    """Pattern for matching tool calls."""

    pattern: str = Field(..., description="Regex pattern to match tool calls")
    args_pattern: str | None = Field(default=None, description="Pattern for arguments")
    count: int | None = Field(default=None, description="Expected count (None = any)")


class OutcomeExpectation(BaseModel):
    """Expected outcome specification."""

    type: str = Field(..., description="Type of outcome")
    value: Any = Field(default=None, description="Expected value")
    condition: str | None = Field(default=None, description="Condition expression")


class BehaviorExpectation(BaseModel):
    """Behavioral expectations for a task."""

    max_tool_calls: int | None = Field(default=None, description="Max allowed tool calls")
    max_iterations: int | None = Field(default=None, description="Max conversation turns")
    max_tokens: int | None = Field(default=None, description="Max tokens used")
    required_tools: list[str] = Field(default_factory=list, description="Tools that must be used")
    forbidden_tools: list[str] = Field(default_factory=list, description="Tools that must not be used")


class TaskExpected(BaseModel):
    """Expected results for a task."""

    outcomes: list[OutcomeExpectation] = Field(
        default_factory=list, description="Expected outcomes"
    )
    tool_calls: dict[str, list[ToolCallPattern]] = Field(
        default_factory=dict, description="Expected tool call patterns (required/forbidden)"
    )
    behavior: BehaviorExpectation = Field(
        default_factory=BehaviorExpectation, description="Behavioral expectations"
    )
    output_contains: list[str] = Field(
        default_factory=list, description="Strings that must appear in output"
    )
    output_not_contains: list[str] = Field(
        default_factory=list, description="Strings that must not appear in output"
    )


class TaskGraderConfig(BaseModel):
    """Task-specific grader configuration."""

    name: str = Field(..., description="Grader name")
    type: str = Field(default="code", description="Grader type override")
    assertions: list[str] = Field(default_factory=list, description="Assertion expressions")
    rubric: str | None = Field(default=None, description="Inline rubric for LLM graders")
    weight: float = Field(default=1.0, description="Weight for this grader in task score")


class Task(BaseModel):
    """A single evaluation task (test case)."""

    id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Human-readable task name")
    description: str = Field(default="", description="Task description")
    inputs: TaskInput = Field(..., description="Task inputs")
    expected: TaskExpected = Field(default_factory=TaskExpected, description="Expected results")
    graders: list[TaskGraderConfig] = Field(
        default_factory=list, description="Task-specific graders"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")
    enabled: bool = Field(default=True, description="Whether this task is enabled")
    timeout_seconds: int | None = Field(default=None, description="Task-specific timeout override")
    context_dir: str | None = Field(default=None, description="Task-specific context directory (overrides global --context-dir)")

    @classmethod
    def from_yaml(cls, yaml_content: str) -> Task:
        """Parse task from YAML string."""
        import yaml

        data = yaml.safe_load(yaml_content)
        return cls.model_validate(data)

    @classmethod
    def from_file(cls, path: str) -> Task:
        """Load task from YAML file."""
        from pathlib import Path

        content = Path(path).read_text()
        return cls.from_yaml(content)


class TriggerTestCase(BaseModel):
    """Test case for trigger accuracy evaluation."""

    prompt: str = Field(..., description="The test prompt")
    should_trigger: bool = Field(..., description="Whether the skill should be triggered")
    reason: str = Field(default="", description="Explanation for expected behavior")


class TriggerTestSuite(BaseModel):
    """Collection of trigger test cases for a skill."""

    skill: str = Field(..., description="Skill being tested")
    should_trigger_prompts: list[TriggerTestCase] = Field(
        default_factory=list, description="Prompts that SHOULD trigger the skill"
    )
    should_not_trigger_prompts: list[TriggerTestCase] = Field(
        default_factory=list, description="Prompts that SHOULD NOT trigger the skill"
    )

    @classmethod
    def from_yaml(cls, yaml_content: str) -> TriggerTestSuite:
        """Parse trigger suite from YAML string."""
        import yaml

        data = yaml.safe_load(yaml_content)
        return cls.model_validate(data)
