"""GitHub issue creation for eval results.

Provides functionality to create GitHub issues with eval results,
including formatted summaries, task details, and links to transcripts.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from skill_eval.schemas.results import EvalResult


def create_eval_issue(
    result: EvalResult,
    repo: str,
    transcript_path: str | None = None,
    suggestions_path: str | None = None,
    failed_only: bool = True,
) -> str | None:
    """Create a GitHub issue with eval results.

    Args:
        result: Evaluation result
        repo: Target repository in format "owner/repo"
        transcript_path: Optional path to transcript JSON file
        suggestions_path: Optional path to suggestions markdown file
        failed_only: If True, only include failed tasks in detail

    Returns:
        Issue URL if successful, None otherwise

    Raises:
        RuntimeError: If gh CLI is not available or issue creation fails
    """
    # Check if gh CLI is available
    if not _check_gh_cli():
        raise RuntimeError(
            "GitHub CLI (gh) is required for creating issues. "
            "Install from https://cli.github.com/"
        )

    # Generate issue title and body
    title = _format_issue_title(result)
    body = _format_issue_body(
        result,
        transcript_path=transcript_path,
        suggestions_path=suggestions_path,
        failed_only=failed_only,
    )

    # Create issue using gh CLI
    try:
        cmd = [
            "gh",
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body",
            body,
            "--label",
            "eval",
            "--label",
            "skill-eval",
            "--label",
            result.skill,
        ]

        result_proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        # Extract issue URL from output
        issue_url = result_proc.stdout.strip()
        return issue_url

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create issue: {e.stderr}") from e


def _format_issue_title(result: EvalResult) -> str:
    """Format issue title.

    Args:
        result: Evaluation result

    Returns:
        Formatted title
    """
    # Count failed tasks
    failed_count = sum(1 for task in result.tasks if task.status != "passed")
    total_count = len(result.tasks)

    if failed_count == 0:
        return f"[Eval] {result.skill}: All {total_count} tasks passed"
    elif failed_count == total_count:
        return f"[Eval] {result.skill}: All {total_count} tasks failed"
    else:
        return f"[Eval] {result.skill}: {failed_count}/{total_count} tasks failed"


def _format_issue_body(
    result: EvalResult,
    transcript_path: str | None = None,
    suggestions_path: str | None = None,
    failed_only: bool = True,
) -> str:
    """Format issue body with eval results.

    Args:
        result: Evaluation result
        transcript_path: Optional path to transcript JSON
        suggestions_path: Optional path to suggestions markdown
        failed_only: If True, only include failed tasks in detail

    Returns:
        Formatted markdown body
    """
    lines = []

    # Header
    lines.append(f"## Eval Results: {result.eval_name}")
    lines.append("")
    lines.append(f"**Skill:** {result.skill}")
    lines.append(f"**Timestamp:** {result.timestamp.isoformat()}")
    lines.append(f"**Model:** {result.config.model or 'default'}")
    executor_str = str(result.config.executor)
    lines.append(f"**Executor:** {executor_str}")
    lines.append("")

    # Summary metrics
    total = len(result.tasks)
    passed = sum(1 for t in result.tasks if t.status == "passed")
    failed = sum(1 for t in result.tasks if t.status == "failed")
    pass_rate = (passed / total * 100) if total > 0 else 0

    lines.append("### Summary")
    lines.append("")
    lines.append(f"- **Pass Rate:** {pass_rate:.1f}% ({passed}/{total})")
    lines.append(f"- **Passed:** {passed}")
    lines.append(f"- **Failed:** {failed}")
    lines.append("")

    # Task results table
    lines.append("### Task Results")
    lines.append("")
    lines.append("| Task | Status | Score | Duration |")
    lines.append("|------|--------|-------|----------|")

    for task in result.tasks:
        status_icon = "✅" if task.status == "passed" else "❌"
        score = task.aggregate.mean_score if task.aggregate else 0.0
        duration_ms = task.aggregate.mean_duration_ms if task.aggregate else 0
        duration_str = (
            f"{duration_ms / 1000:.1f}s"
            if duration_ms >= 1000
            else f"{duration_ms}ms"
        )
        lines.append(
            f"| {task.name} | {status_icon} {task.status} | "
            f"{score:.2f} | {duration_str} |"
        )

    lines.append("")

    # Task details (failed only by default)
    tasks_to_detail = [
        t for t in result.tasks if not failed_only or t.status != "passed"
    ]

    if tasks_to_detail:
        lines.append("### Task Details")
        lines.append("")

        for task in tasks_to_detail:
            lines.append(f"#### {task.name}")
            lines.append("")
            lines.append(f"**Status:** {task.status}")
            score = task.aggregate.mean_score if task.aggregate else 0.0
            lines.append(f"**Score:** {score:.2f}")
            lines.append(f"**Trials:** {len(task.trials)}")
            lines.append("")

            # Show grader results from trials
            if task.trials:
                lines.append("**Grader Results:**")
                lines.append("")

                # Collect unique grader messages
                messages: set[str] = set()
                for trial in task.trials:
                    for grader_result in trial.grader_results.values():
                        if not grader_result.passed and grader_result.message:
                            messages.add(f"- {grader_result.message}")

                for msg in sorted(messages):
                    lines.append(msg)
                lines.append("")

    # Suggestions (if provided)
    if suggestions_path:
        suggestions_file = Path(suggestions_path)
        if suggestions_file.exists():
            lines.append("### Improvement Suggestions")
            lines.append("")
            suggestions_content = suggestions_file.read_text()
            lines.append(suggestions_content)
            lines.append("")

    # Collapsible sections for full details
    lines.append("<details>")
    lines.append("<summary>Full JSON Results</summary>")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(result.model_dump(), indent=2, default=str))
    lines.append("```")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    # Transcript (if provided)
    if transcript_path:
        transcript_file = Path(transcript_path)
        if transcript_file.exists():
            lines.append("<details>")
            lines.append("<summary>Conversation Transcript</summary>")
            lines.append("")
            lines.append("```json")
            transcript_content = transcript_file.read_text()
            lines.append(transcript_content)
            lines.append("```")
            lines.append("")
            lines.append("</details>")
            lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Generated by [skill-eval](https://github.com/spboyer/evals-for-skills)*")

    return "\n".join(lines)


def _check_gh_cli() -> bool:
    """Check if GitHub CLI is installed."""
    try:
        subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
