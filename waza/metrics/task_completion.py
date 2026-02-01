"""Task completion metric."""

from __future__ import annotations

from waza.schemas.results import MetricResult, TaskResult


class TaskCompletionMetric:
    """Measures whether tasks were completed successfully."""

    name = "task_completion"

    def __init__(self, threshold: float = 0.8, weight: float = 1.0):
        """Initialize metric.

        Args:
            threshold: Pass/fail threshold (0-1)
            weight: Weight in composite score
        """
        self.threshold = threshold
        self.weight = weight

    def calculate(self, task_results: list[TaskResult]) -> MetricResult:
        """Calculate task completion score.

        Args:
            task_results: Results from all tasks

        Returns:
            MetricResult with completion score
        """
        if not task_results:
            return MetricResult(
                name=self.name,
                score=0.0,
                threshold=self.threshold,
                passed=False,
                weight=self.weight,
                details={"error": "No task results"},
            )

        # Count tasks that completed (passed or partial)
        completed = sum(
            1 for t in task_results
            if t.status in ("passed", "partial")
        )

        # Full pass count
        fully_passed = sum(1 for t in task_results if t.status == "passed")

        # Calculate score (weight partial completions at 0.5)
        partial_count = completed - fully_passed
        weighted_score = (fully_passed + 0.5 * partial_count) / len(task_results)

        return MetricResult(
            name=self.name,
            score=weighted_score,
            threshold=self.threshold,
            passed=weighted_score >= self.threshold,
            weight=self.weight,
            details={
                "total_tasks": len(task_results),
                "fully_passed": fully_passed,
                "partial": partial_count,
                "failed": len(task_results) - completed,
            },
        )
