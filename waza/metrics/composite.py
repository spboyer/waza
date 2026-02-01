"""Composite metric for weighted scoring."""

from __future__ import annotations

from waza.schemas.results import MetricResult


class CompositeMetric:
    """Combines multiple metrics into a weighted composite score."""

    name = "composite"

    def __init__(self, threshold: float = 0.7):
        """Initialize composite metric.

        Args:
            threshold: Pass/fail threshold for composite score
        """
        self.threshold = threshold

    def calculate(self, metrics: dict[str, MetricResult]) -> MetricResult:
        """Calculate weighted composite score from individual metrics.

        Args:
            metrics: Dictionary of metric name -> MetricResult

        Returns:
            MetricResult with composite score
        """
        if not metrics:
            return MetricResult(
                name=self.name,
                score=0.0,
                threshold=self.threshold,
                passed=False,
                weight=1.0,
                details={"error": "No metrics to combine"},
            )

        # Calculate weighted sum
        total_weight = sum(m.weight for m in metrics.values())
        if total_weight == 0:
            total_weight = 1.0  # Avoid division by zero

        weighted_sum = sum(m.score * m.weight for m in metrics.values())
        composite_score = weighted_sum / total_weight

        # Determine pass/fail
        all_passed = all(m.passed for m in metrics.values())
        composite_passed = composite_score >= self.threshold

        return MetricResult(
            name=self.name,
            score=composite_score,
            threshold=self.threshold,
            passed=composite_passed and all_passed,
            weight=1.0,
            details={
                "total_weight": total_weight,
                "weighted_sum": weighted_sum,
                "individual_metrics": {
                    name: {
                        "score": m.score,
                        "weight": m.weight,
                        "passed": m.passed,
                        "contribution": (m.score * m.weight) / total_weight,
                    }
                    for name, m in metrics.items()
                },
                "all_individual_passed": all_passed,
            },
        )

    def calculate_with_gates(
        self,
        metrics: dict[str, MetricResult],
        gate_metrics: list[str] | None = None,
    ) -> MetricResult:
        """Calculate composite with hard gates.

        Gate metrics must pass for the overall eval to pass,
        regardless of composite score.

        Args:
            metrics: Dictionary of metric name -> MetricResult
            gate_metrics: List of metric names that act as hard gates

        Returns:
            MetricResult with composite score
        """
        result = self.calculate(metrics)

        if gate_metrics:
            gates_passed = all(
                metrics.get(name, MetricResult(name=name, score=0, threshold=0, passed=False, weight=0)).passed
                for name in gate_metrics
            )

            result.details["gate_metrics"] = gate_metrics
            result.details["gates_passed"] = gates_passed

            if not gates_passed:
                result.passed = False
                result.details["failure_reason"] = "Gate metric(s) failed"

        return result
