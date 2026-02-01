"""Code-based (deterministic) graders."""

from __future__ import annotations

import re
import time
from typing import Any

from skill_eval.graders.base import Grader, GraderContext, GraderType, GraderRegistry
from skill_eval.schemas.results import GraderResult


@GraderRegistry.register("code")
class CodeGrader(Grader):
    """Grader that uses code-based assertions."""

    @property
    def grader_type(self) -> GraderType:
        return GraderType.CODE

    def grade(self, context: GraderContext) -> GraderResult:
        """Grade using configured assertions."""
        start_time = time.time()
        
        assertions = self.config.get("assertions", [])
        if not assertions:
            return GraderResult(
                name=self.name,
                type=self.grader_type.value,
                score=1.0,
                passed=True,
                message="No assertions configured",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        passed_count = 0
        failed_assertions = []
        
        # Build evaluation context
        # Note: transcript entries use 'role' not 'type', and tool calls have role='tool' with 'name'
        eval_context = {
            "output": context.output,
            "outcome": context.outcome,
            "transcript": context.transcript,
            "tool_calls": [t for t in context.transcript if t.get("role") == "tool" or t.get("type") == "tool_call"],
            "errors": [t for t in context.transcript if t.get("type") == "error" or "error" in str(t.get("content", "")).lower()],
            "duration_ms": context.duration_ms,
            "len": len,
            "any": any,
            "all": all,
            "re": re,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "True": True,
            "False": False,
        }

        for assertion in assertions:
            try:
                result = eval(assertion, {"__builtins__": {}}, eval_context)
                if result:
                    passed_count += 1
                else:
                    failed_assertions.append(f"Failed: {assertion}")
            except Exception as e:
                failed_assertions.append(f"Error in '{assertion}': {e}")

        score = passed_count / len(assertions) if assertions else 1.0
        passed = len(failed_assertions) == 0

        return GraderResult(
            name=self.name,
            type=self.grader_type.value,
            score=score,
            passed=passed,
            message="All assertions passed" if passed else "; ".join(failed_assertions),
            details={
                "total_assertions": len(assertions),
                "passed_assertions": passed_count,
                "failed_assertions": failed_assertions,
            },
            duration_ms=int((time.time() - start_time) * 1000),
        )


@GraderRegistry.register("regex")
class RegexGrader(Grader):
    """Grader that matches output against regex patterns."""

    @property
    def grader_type(self) -> GraderType:
        return GraderType.CODE

    def grade(self, context: GraderContext) -> GraderResult:
        """Grade using regex pattern matching."""
        start_time = time.time()
        
        must_match = self.config.get("must_match", [])
        must_not_match = self.config.get("must_not_match", [])
        
        failures = []
        output = context.output

        for pattern in must_match:
            if not re.search(pattern, output, re.IGNORECASE):
                failures.append(f"Missing expected pattern: {pattern}")

        for pattern in must_not_match:
            if re.search(pattern, output, re.IGNORECASE):
                failures.append(f"Found forbidden pattern: {pattern}")

        total_checks = len(must_match) + len(must_not_match)
        passed_checks = total_checks - len(failures)
        score = passed_checks / total_checks if total_checks > 0 else 1.0

        return GraderResult(
            name=self.name,
            type=self.grader_type.value,
            score=score,
            passed=len(failures) == 0,
            message="All patterns matched" if not failures else "; ".join(failures),
            details={
                "must_match": must_match,
                "must_not_match": must_not_match,
                "failures": failures,
            },
            duration_ms=int((time.time() - start_time) * 1000),
        )


@GraderRegistry.register("tool_calls")
class ToolCallGrader(Grader):
    """Grader that validates tool call patterns."""

    @property
    def grader_type(self) -> GraderType:
        return GraderType.CODE

    def grade(self, context: GraderContext) -> GraderResult:
        """Grade based on tool call requirements."""
        start_time = time.time()
        
        required = self.config.get("required", [])
        forbidden = self.config.get("forbidden", [])
        max_calls = self.config.get("max_calls")
        
        # Extract tool calls from transcript
        tool_calls = []
        for entry in context.transcript:
            if entry.get("type") == "tool_call":
                tool_calls.append(entry.get("tool", "") + " " + str(entry.get("args", "")))
        
        tool_call_str = "\n".join(tool_calls)
        failures = []

        # Check required patterns
        for pattern in required:
            if isinstance(pattern, dict):
                pattern = pattern.get("pattern", "")
            if not re.search(pattern, tool_call_str, re.IGNORECASE):
                failures.append(f"Missing required tool call pattern: {pattern}")

        # Check forbidden patterns
        for pattern in forbidden:
            if isinstance(pattern, dict):
                pattern = pattern.get("pattern", "")
            if re.search(pattern, tool_call_str, re.IGNORECASE):
                failures.append(f"Found forbidden tool call pattern: {pattern}")

        # Check max calls
        if max_calls is not None and len(tool_calls) > max_calls:
            failures.append(f"Too many tool calls: {len(tool_calls)} > {max_calls}")

        total_checks = len(required) + len(forbidden) + (1 if max_calls else 0)
        passed_checks = total_checks - len(failures)
        score = passed_checks / total_checks if total_checks > 0 else 1.0

        return GraderResult(
            name=self.name,
            type=self.grader_type.value,
            score=score,
            passed=len(failures) == 0,
            message="Tool calls valid" if not failures else "; ".join(failures),
            details={
                "total_tool_calls": len(tool_calls),
                "required_patterns": required,
                "forbidden_patterns": forbidden,
                "failures": failures,
            },
            duration_ms=int((time.time() - start_time) * 1000),
        )


@GraderRegistry.register("script")
class ScriptGrader(Grader):
    """Grader that runs an external Python script."""

    @property
    def grader_type(self) -> GraderType:
        return GraderType.CODE

    def grade(self, context: GraderContext) -> GraderResult:
        """Grade by running an external script."""
        import subprocess
        import json
        
        start_time = time.time()
        script_path = self.config.get("script")
        
        if not script_path:
            return GraderResult(
                name=self.name,
                type=self.grader_type.value,
                score=0.0,
                passed=False,
                message="No script path configured",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        try:
            # Pass context as JSON to stdin
            context_json = context.model_dump_json()
            result = subprocess.run(
                ["python", script_path],
                input=context_json,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return GraderResult(
                    name=self.name,
                    type=self.grader_type.value,
                    score=0.0,
                    passed=False,
                    message=f"Script failed: {result.stderr}",
                    duration_ms=int((time.time() - start_time) * 1000),
                )

            # Parse script output as JSON
            output = json.loads(result.stdout)
            return GraderResult(
                name=self.name,
                type=self.grader_type.value,
                score=output.get("score", 0.0),
                passed=output.get("passed", False),
                message=output.get("message", ""),
                details=output.get("details", {}),
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except subprocess.TimeoutExpired:
            return GraderResult(
                name=self.name,
                type=self.grader_type.value,
                score=0.0,
                passed=False,
                message="Script timed out",
                duration_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return GraderResult(
                name=self.name,
                type=self.grader_type.value,
                score=0.0,
                passed=False,
                message=f"Script error: {e}",
                duration_ms=int((time.time() - start_time) * 1000),
            )
