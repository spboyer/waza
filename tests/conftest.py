"""Pytest configuration for skill-eval tests."""

import pytest


@pytest.fixture
def sample_eval_spec():
    """Provide a sample eval spec for testing."""
    from skill_eval.schemas.eval_spec import EvalSpec, GraderConfig, GraderType, MetricConfig

    return EvalSpec(
        name="sample-eval",
        description="Sample evaluation for testing",
        skill="sample-skill",
        metrics=[
            MetricConfig(name="task_completion", weight=0.5, threshold=0.8),
            MetricConfig(name="trigger_accuracy", weight=0.3, threshold=0.9),
            MetricConfig(name="behavior_quality", weight=0.2, threshold=0.7),
        ],
        graders=[
            GraderConfig(
                type=GraderType.CODE,
                name="basic_check",
                config={"assertions": ["len(output) > 0"]},
            ),
        ],
        tasks=["tasks/*.yaml"],
    )


@pytest.fixture
def sample_task():
    """Provide a sample task for testing."""
    from skill_eval.schemas.task import Task, TaskExpected, TaskInput

    return Task(
        id="sample-001",
        name="Sample Task",
        description="A sample task for testing",
        inputs=TaskInput(
            prompt="Do something useful",
            context={"key": "value"},
        ),
        expected=TaskExpected(
            output_contains=["success"],
        ),
    )


@pytest.fixture
def sample_grader_context():
    """Provide a sample grader context for testing."""
    from skill_eval.graders.base import GraderContext

    return GraderContext(
        task={"id": "sample-001", "name": "Sample Task"},
        transcript=[
            {"type": "tool_call", "tool": "bash", "args": {"cmd": "echo hello"}},
            {"type": "response", "content": "hello"},
        ],
        output="Task completed successfully",
        outcome={"status": "completed"},
        duration_ms=1500,
    )
