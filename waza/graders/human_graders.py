"""Human review graders for manual evaluation."""

from __future__ import annotations

import time

from waza.graders.base import Grader, GraderContext, GraderRegistry, GraderType
from waza.schemas.results import GraderResult


@GraderRegistry.register("human")
class HumanGrader(Grader):
    """Grader that requires human review."""

    @property
    def grader_type(self) -> GraderType:
        return GraderType.HUMAN

    def grade(self, context: GraderContext) -> GraderResult:
        """Mark for human review - returns pending status."""
        start_time = time.time()

        instructions = self.config.get("instructions", "Review the output for correctness.")
        criteria = self.config.get("criteria", [])

        return GraderResult(
            name=self.name,
            type=self.grader_type.value,
            score=0.0,  # Pending
            passed=False,  # Will be updated after review
            message="Pending human review",
            details={
                "status": "pending",
                "instructions": instructions,
                "criteria": criteria,
                "task_id": context.task.get("id"),
                "output_preview": context.output[:500] if context.output else "",
            },
            duration_ms=int((time.time() - start_time) * 1000),
        )

    def submit_review(
        self,
        grader_result: GraderResult,
        score: float,
        passed: bool,
        reviewer: str,
        comments: str = "",
    ) -> GraderResult:
        """Submit human review results."""
        return GraderResult(
            name=self.name,
            type=self.grader_type.value,
            score=score,
            passed=passed,
            message=comments or "Human review completed",
            details={
                **grader_result.details,
                "status": "reviewed",
                "reviewer": reviewer,
                "review_comments": comments,
            },
            duration_ms=grader_result.duration_ms,
        )


@GraderRegistry.register("human_calibration")
class HumanCalibrationGrader(Grader):
    """Grader for calibrating LLM graders against human judgment."""

    @property
    def grader_type(self) -> GraderType:
        return GraderType.HUMAN

    def grade(self, context: GraderContext) -> GraderResult:
        """Generate calibration request."""
        start_time = time.time()

        # This grader is used alongside LLM graders to collect
        # human labels for calibration purposes
        llm_grader_name = self.config.get("calibrate_grader")

        return GraderResult(
            name=self.name,
            type=self.grader_type.value,
            score=0.0,
            passed=False,
            message="Awaiting human calibration",
            details={
                "status": "calibration_pending",
                "calibrate_grader": llm_grader_name,
                "task_id": context.task.get("id"),
                "instructions": "Provide your own score for comparison with LLM grader",
            },
            duration_ms=int((time.time() - start_time) * 1000),
        )
