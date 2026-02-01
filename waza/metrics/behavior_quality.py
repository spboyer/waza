"""Behavior quality metric."""

from __future__ import annotations

from waza.schemas.results import MetricResult, TaskResult, TrialResult


class BehaviorQualityMetric:
    """Measures the quality of skill behavior (efficiency, tool usage, etc.)."""

    name = "behavior_quality"

    def __init__(
        self,
        threshold: float = 0.7,
        weight: float = 1.0,
        max_tool_calls: int | None = None,
        max_iterations: int | None = None,
        required_tools: list[str] | None = None,
    ):
        """Initialize metric.

        Args:
            threshold: Pass/fail threshold (0-1)
            weight: Weight in composite score
            max_tool_calls: Maximum expected tool calls
            max_iterations: Maximum expected conversation turns
            required_tools: Tools that should be used
        """
        self.threshold = threshold
        self.weight = weight
        self.max_tool_calls = max_tool_calls
        self.max_iterations = max_iterations
        self.required_tools = required_tools or []

    def calculate(self, task_results: list[TaskResult]) -> MetricResult:
        """Calculate behavior quality score.

        Args:
            task_results: Results from all tasks

        Returns:
            MetricResult with quality score
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

        # Collect all trials
        all_trials: list[TrialResult] = []
        for task in task_results:
            all_trials.extend(task.trials)

        if not all_trials:
            return MetricResult(
                name=self.name,
                score=0.0,
                threshold=self.threshold,
                passed=False,
                weight=self.weight,
                details={"error": "No trials"},
            )

        # Calculate component scores
        efficiency_score = self._calc_efficiency(all_trials)
        tool_usage_score = self._calc_tool_usage(all_trials)
        error_rate_score = self._calc_error_rate(all_trials)
        grader_score = self._calc_grader_average(all_trials)

        # Weighted average of component scores
        component_weights = {
            "efficiency": 0.25,
            "tool_usage": 0.25,
            "error_rate": 0.25,
            "grader_avg": 0.25,
        }

        overall_score = (
            efficiency_score * component_weights["efficiency"]
            + tool_usage_score * component_weights["tool_usage"]
            + error_rate_score * component_weights["error_rate"]
            + grader_score * component_weights["grader_avg"]
        )

        return MetricResult(
            name=self.name,
            score=overall_score,
            threshold=self.threshold,
            passed=overall_score >= self.threshold,
            weight=self.weight,
            details={
                "total_trials": len(all_trials),
                "efficiency_score": efficiency_score,
                "tool_usage_score": tool_usage_score,
                "error_rate_score": error_rate_score,
                "grader_average_score": grader_score,
                "component_weights": component_weights,
            },
        )

    def _calc_efficiency(self, trials: list[TrialResult]) -> float:
        """Calculate efficiency score based on tool calls and iterations."""
        if not trials:
            return 0.0

        scores = []
        for trial in trials:
            summary = trial.transcript_summary

            # Score based on tool calls (if max configured)
            if self.max_tool_calls:
                tool_ratio = min(1.0, summary.tool_calls / self.max_tool_calls)
                # Lower is better, invert the score
                tool_score = max(0.0, 1.0 - (tool_ratio - 0.5) * 2) if tool_ratio > 0.5 else 1.0
            else:
                tool_score = 1.0

            # Score based on turns (if max configured)
            if self.max_iterations:
                turn_ratio = min(1.0, summary.total_turns / self.max_iterations)
                turn_score = max(0.0, 1.0 - (turn_ratio - 0.5) * 2) if turn_ratio > 0.5 else 1.0
            else:
                turn_score = 1.0

            scores.append((tool_score + turn_score) / 2)

        return sum(scores) / len(scores)

    def _calc_tool_usage(self, trials: list[TrialResult]) -> float:
        """Calculate score based on correct tool usage."""
        if not self.required_tools:
            return 1.0  # No requirements = full score

        scores = []
        for trial in trials:
            tools_used = set(trial.transcript_summary.tools_used)
            required = set(self.required_tools)

            if not required:
                scores.append(1.0)
                continue

            # Score based on coverage of required tools
            covered = len(tools_used & required)
            score = covered / len(required)
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def _calc_error_rate(self, trials: list[TrialResult]) -> float:
        """Calculate score based on error rate."""
        if not trials:
            return 0.0

        error_count = sum(
            1 for t in trials
            if t.status == "error" or t.transcript_summary.errors
        )

        error_rate = error_count / len(trials)
        # Invert: 0 errors = 1.0 score, 100% errors = 0.0 score
        return 1.0 - error_rate

    def _calc_grader_average(self, trials: list[TrialResult]) -> float:
        """Calculate average score from graders."""
        scores = []
        for trial in trials:
            if trial.grader_results:
                trial_avg = sum(g.score for g in trial.grader_results.values()) / len(trial.grader_results)
                scores.append(trial_avg)

        return sum(scores) / len(scores) if scores else 0.5  # Default to middle score
