"""Tests for GitHub issues module."""

from datetime import datetime
from pathlib import Path

from skill_eval.issues import _format_issue_body, _format_issue_title
from skill_eval.schemas.eval_spec import EvalConfig, ExecutorType
from skill_eval.schemas.results import (
    EvalResult,
    EvalSummary,
    GraderResult,
    TaskAggregate,
    TaskResult,
    TrialResult,
)


class TestFormatIssueTitle:
    """Tests for _format_issue_title function."""

    def test_all_tasks_passed(self):
        """Test title when all tasks pass."""
        result = EvalResult(
            eval_id="test-001",
            eval_name="test-eval",
            skill="test-skill",
            timestamp=datetime.now(),
            tasks=[
                TaskResult(
                    id="task1",
                    name="Task 1",
                    status="passed",
                    trials=[],
                    aggregate=TaskAggregate(
                        pass_rate=1.0,
                        mean_score=1.0,
                        min_score=1.0,
                        max_score=1.0,
                        mean_duration_ms=100,
                    ),
                )
            ],
            summary=EvalSummary(
                total_tasks=1,
                passed=1,
                failed=0,
                pass_rate=1.0,
                composite_score=1.0,
            ),
        )

        title = _format_issue_title(result)
        assert "[Eval] test-skill: All 1 tasks passed" in title

    def test_all_tasks_failed(self):
        """Test title when all tasks fail."""
        result = EvalResult(
            eval_id="test-001",
            eval_name="test-eval",
            skill="test-skill",
            timestamp=datetime.now(),
            tasks=[
                TaskResult(
                    id="task1",
                    name="Task 1",
                    status="failed",
                    trials=[],
                    aggregate=TaskAggregate(
                        pass_rate=0.0,
                        mean_score=0.0,
                        min_score=0.0,
                        max_score=0.0,
                        mean_duration_ms=100,
                    ),
                )
            ],
            summary=EvalSummary(
                total_tasks=1,
                passed=0,
                failed=1,
                pass_rate=0.0,
                composite_score=0.0,
            ),
        )

        title = _format_issue_title(result)
        assert "[Eval] test-skill: All 1 tasks failed" in title

    def test_some_tasks_failed(self):
        """Test title when some tasks fail."""
        result = EvalResult(
            eval_id="test-001",
            eval_name="test-eval",
            skill="test-skill",
            timestamp=datetime.now(),
            tasks=[
                TaskResult(
                    id="task1",
                    name="Task 1",
                    status="passed",
                    trials=[],
                    aggregate=TaskAggregate(
                        pass_rate=1.0,
                        mean_score=1.0,
                        min_score=1.0,
                        max_score=1.0,
                        mean_duration_ms=100,
                    ),
                ),
                TaskResult(
                    id="task2",
                    name="Task 2",
                    status="failed",
                    trials=[],
                    aggregate=TaskAggregate(
                        pass_rate=0.0,
                        mean_score=0.0,
                        min_score=0.0,
                        max_score=0.0,
                        mean_duration_ms=100,
                    ),
                ),
            ],
            summary=EvalSummary(
                total_tasks=2,
                passed=1,
                failed=1,
                pass_rate=0.5,
                composite_score=0.5,
            ),
        )

        title = _format_issue_title(result)
        assert "[Eval] test-skill: 1/2 tasks failed" in title


class TestFormatIssueBody:
    """Tests for _format_issue_body function."""

    def test_basic_issue_body_structure(self):
        """Test that issue body contains expected sections."""
        result = EvalResult(
            eval_id="test-001",
            eval_name="test-eval",
            skill="test-skill",
            timestamp=datetime.now(),
            tasks=[
                TaskResult(
                    id="task1",
                    name="Task 1",
                    status="failed",
                    trials=[
                        TrialResult(
                            trial_id=1,
                            status="failed",
                            output="test output",
                            grader_results={
                                "test_grader": GraderResult(
                                    name="test_grader",
                                    type="mock",
                                    passed=False,
                                    score=0.0,
                                    message="Test failure",
                                )
                            },
                        )
                    ],
                    aggregate=TaskAggregate(
                        pass_rate=0.0,
                        mean_score=0.0,
                        min_score=0.0,
                        max_score=0.0,
                        mean_duration_ms=100,
                    ),
                )
            ],
            summary=EvalSummary(
                total_tasks=1,
                passed=0,
                failed=1,
                pass_rate=0.0,
                composite_score=0.0,
            ),
        )

        body = _format_issue_body(result)

        # Check for key sections
        assert "## Eval Results:" in body
        assert "test-eval" in body
        assert "**Skill:** test-skill" in body
        assert "### Summary" in body
        assert "Pass Rate" in body
        assert "### Task Results" in body
        assert "| Task | Status | Score | Duration |" in body
        assert "### Task Details" in body
        assert "Task 1" in body
        assert "Test failure" in body
        assert "<details>" in body  # Collapsible sections
        assert "Full JSON Results" in body

    def test_failed_only_filtering(self):
        """Test that failed_only parameter filters tasks correctly."""
        result = EvalResult(
            eval_id="test-001",
            eval_name="test-eval",
            skill="test-skill",
            timestamp=datetime.now(),
            tasks=[
                TaskResult(
                    id="task1",
                    name="Passed Task",
                    status="passed",
                    trials=[],
                    aggregate=TaskAggregate(
                        pass_rate=1.0,
                        mean_score=1.0,
                        min_score=1.0,
                        max_score=1.0,
                        mean_duration_ms=100,
                    ),
                ),
                TaskResult(
                    id="task2",
                    name="Failed Task",
                    status="failed",
                    trials=[],
                    aggregate=TaskAggregate(
                        pass_rate=0.0,
                        mean_score=0.0,
                        min_score=0.0,
                        max_score=0.0,
                        mean_duration_ms=100,
                    ),
                ),
            ],
            summary=EvalSummary(
                total_tasks=2,
                passed=1,
                failed=1,
                pass_rate=0.5,
                composite_score=0.5,
            ),
        )

        # With failed_only=True
        body_failed_only = _format_issue_body(result, failed_only=True)
        assert "Failed Task" in body_failed_only
        assert "#### Failed Task" in body_failed_only
        # Passed task should not be in details section
        assert "#### Passed Task" not in body_failed_only

        # With failed_only=False
        body_all = _format_issue_body(result, failed_only=False)
        assert "Failed Task" in body_all
        assert "Passed Task" in body_all

    def test_suggestions_included(self):
        """Test that suggestions are included when provided."""
        import tempfile

        result = EvalResult(
            eval_id="test-001",
            eval_name="test-eval",
            skill="test-skill",
            timestamp=datetime.now(),
            tasks=[],
            summary=EvalSummary(
                total_tasks=0,
                passed=0,
                failed=0,
                pass_rate=0.0,
                composite_score=0.0,
            ),
        )

        # Create a temp suggestions file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("## Suggestions\n\n- Improve error handling\n")
            suggestions_path = f.name

        try:
            body = _format_issue_body(result, suggestions_path=suggestions_path)
            assert "### Improvement Suggestions" in body
            assert "Improve error handling" in body
        finally:
            Path(suggestions_path).unlink()
