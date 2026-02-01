"""Trigger accuracy metric."""

from __future__ import annotations

from waza.schemas.results import MetricResult
from waza.schemas.task import TriggerTestCase, TriggerTestSuite


class TriggerAccuracyMetric:
    """Measures whether a skill triggers on the correct prompts."""

    name = "trigger_accuracy"

    def __init__(self, threshold: float = 0.9, weight: float = 1.0):
        """Initialize metric.

        Args:
            threshold: Pass/fail threshold (0-1)
            weight: Weight in composite score
        """
        self.threshold = threshold
        self.weight = weight

    def calculate(
        self,
        test_suite: TriggerTestSuite,
        trigger_results: list[tuple[TriggerTestCase, bool]],
    ) -> MetricResult:
        """Calculate trigger accuracy score.

        Args:
            test_suite: The trigger test suite
            trigger_results: List of (test_case, actual_triggered) tuples

        Returns:
            MetricResult with accuracy score
        """
        if not trigger_results:
            return MetricResult(
                name=self.name,
                score=0.0,
                threshold=self.threshold,
                passed=False,
                weight=self.weight,
                details={"error": "No trigger results"},
            )

        # Calculate metrics
        true_positives = 0  # Should trigger and did
        true_negatives = 0  # Should not trigger and didn't
        false_positives = 0  # Should not trigger but did
        false_negatives = 0  # Should trigger but didn't

        for test_case, actual_triggered in trigger_results:
            if test_case.should_trigger:
                if actual_triggered:
                    true_positives += 1
                else:
                    false_negatives += 1
            else:
                if actual_triggered:
                    false_positives += 1
                else:
                    true_negatives += 1

        total = len(trigger_results)
        correct = true_positives + true_negatives
        accuracy = correct / total if total > 0 else 0.0

        # Calculate precision and recall for additional insight
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return MetricResult(
            name=self.name,
            score=accuracy,
            threshold=self.threshold,
            passed=accuracy >= self.threshold,
            weight=self.weight,
            details={
                "total_tests": total,
                "correct": correct,
                "true_positives": true_positives,
                "true_negatives": true_negatives,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
            },
        )

    def calculate_from_lists(
        self,
        should_trigger_results: list[bool],
        should_not_trigger_results: list[bool],
    ) -> MetricResult:
        """Calculate from simple boolean lists.

        Args:
            should_trigger_results: Results for prompts that should trigger (True = triggered)
            should_not_trigger_results: Results for prompts that should not trigger (True = triggered)

        Returns:
            MetricResult with accuracy score
        """
        # Build test cases and results
        trigger_results = []

        for triggered in should_trigger_results:
            test_case = TriggerTestCase(
                prompt="",  # Placeholder
                should_trigger=True,
            )
            trigger_results.append((test_case, triggered))

        for triggered in should_not_trigger_results:
            test_case = TriggerTestCase(
                prompt="",
                should_trigger=False,
            )
            trigger_results.append((test_case, triggered))

        # Create minimal test suite
        test_suite = TriggerTestSuite(skill="unknown")

        return self.calculate(test_suite, trigger_results)
