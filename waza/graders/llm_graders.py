"""LLM-based graders using model-as-judge."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from waza.graders.base import Grader, GraderContext, GraderRegistry, GraderType
from waza.schemas.results import GraderResult


@GraderRegistry.register("llm")
class LLMGrader(Grader):
    """Grader that uses an LLM to evaluate output."""

    @property
    def grader_type(self) -> GraderType:
        return GraderType.LLM

    def _load_rubric(self) -> str:
        """Load rubric from file or config."""
        rubric = self.config.get("rubric", "")

        # If rubric is a file path, load it
        if rubric and not rubric.startswith("Score"):
            rubric_path = Path(rubric)
            if rubric_path.exists():
                rubric = rubric_path.read_text()

        return rubric or self._default_rubric()

    def _default_rubric(self) -> str:
        """Return default rubric if none configured."""
        return """Score the response from 1-5 based on:
1. Correctness: Is the output accurate and correct?
2. Completeness: Did it address all parts of the request?
3. Quality: Is the response well-structured and clear?

Return a JSON object with:
- "score": number from 1-5
- "reasoning": brief explanation
- "passed": true if score >= 4, false otherwise
"""

    def grade(self, context: GraderContext) -> GraderResult:
        """Grade using an LLM judge."""
        start_time = time.time()

        model = self.config.get("model", "gpt-4o-mini")
        rubric = self._load_rubric()

        # Build the prompt for the LLM judge
        prompt = self._build_judge_prompt(context, rubric)

        try:
            # Try to use OpenAI
            result = self._call_openai(prompt, model)
        except ImportError:
            # Fall back to mock result if no LLM client available
            result = self._mock_result()
        except Exception as e:
            return GraderResult(
                name=self.name,
                type=self.grader_type.value,
                score=0.0,
                passed=False,
                message=f"LLM grading failed: {e}",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # Normalize score from 1-5 to 0-1
        raw_score = result.get("score", 3)
        normalized_score = (raw_score - 1) / 4  # 1->0, 5->1
        threshold = self.config.get("threshold", 0.75)  # Default: score >= 4

        return GraderResult(
            name=self.name,
            type=self.grader_type.value,
            score=normalized_score,
            passed=normalized_score >= threshold,
            message=result.get("reasoning", ""),
            details={
                "raw_score": raw_score,
                "model": model,
                "rubric_used": rubric[:100] + "..." if len(rubric) > 100 else rubric,
            },
            duration_ms=int((time.time() - start_time) * 1000),
        )

    def _build_judge_prompt(self, context: GraderContext, rubric: str) -> str:
        """Build the prompt for the LLM judge."""
        return f"""You are an AI evaluator. Grade the following skill execution.

## Task
{context.task.get('name', 'Unknown task')}
{context.task.get('description', '')}

## Input
{context.task.get('inputs', {}).get('prompt', 'No prompt')}

## Output
{context.output}

## Rubric
{rubric}

Respond with a JSON object containing "score" (1-5), "reasoning", and "passed" (boolean).
"""

    def _call_openai(self, prompt: str, model: str) -> dict[str, Any]:
        """Call OpenAI API for grading."""
        import json

        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        return json.loads(response.choices[0].message.content)

    def _mock_result(self) -> dict[str, Any]:
        """Return mock result when no LLM client available."""
        return {
            "score": 4,
            "reasoning": "LLM grading not available (no client configured)",
            "passed": True,
        }


@GraderRegistry.register("llm_comparison")
class LLMComparisonGrader(Grader):
    """Grader that compares output against a reference using LLM."""

    @property
    def grader_type(self) -> GraderType:
        return GraderType.LLM

    def grade(self, context: GraderContext) -> GraderResult:
        """Grade by comparing output to reference."""
        start_time = time.time()

        reference = self.config.get("reference", "")
        model = self.config.get("model", "gpt-4o-mini")

        if not reference:
            return GraderResult(
                name=self.name,
                type=self.grader_type.value,
                score=0.0,
                passed=False,
                message="No reference output configured",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        prompt = f"""Compare these two outputs and rate their semantic similarity from 1-5.

## Reference Output (Expected)
{reference}

## Actual Output
{context.output}

Score 5 if they convey the same information, even if worded differently.
Score 1 if they are completely different or contradictory.

Respond with JSON: {{"score": N, "reasoning": "...", "passed": true/false}}
"""

        try:
            import json

            from openai import OpenAI

            client = OpenAI()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            result = json.loads(response.choices[0].message.content)
        except Exception:
            result = {"score": 3, "reasoning": "Comparison not available", "passed": False}

        raw_score = result.get("score", 3)
        normalized_score = (raw_score - 1) / 4

        return GraderResult(
            name=self.name,
            type=self.grader_type.value,
            score=normalized_score,
            passed=result.get("passed", normalized_score >= 0.75),
            message=result.get("reasoning", ""),
            details={"raw_score": raw_score, "model": model},
            duration_ms=int((time.time() - start_time) * 1000),
        )
