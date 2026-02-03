"""Storage layer for waza Web UI - JSON file-based storage in ~/.waza/"""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


class StorageManager:
    """Manage JSON file storage in ~/.waza/ directory."""

    def __init__(self, base_dir: Path | str | None = None):
        if base_dir is None:
            base_dir = Path.home() / ".waza"
        self.base_dir = Path(base_dir)
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Create required directories."""
        (self.base_dir / "evals").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "runs").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "cache").mkdir(parents=True, exist_ok=True)

    # Config management
    def get_config(self) -> dict[str, Any]:
        """Get user configuration."""
        config_path = self.base_dir / "config.json"
        if config_path.exists():
            return json.loads(config_path.read_text())
        return {
            "model": "claude-sonnet-4-20250514",
            "executor": "mock",
            "theme": "dark",
        }

    def save_config(self, config: dict[str, Any]) -> None:
        """Save user configuration."""
        config_path = self.base_dir / "config.json"
        config_path.write_text(json.dumps(config, indent=2))

    # Evals management
    def list_evals(self) -> list[dict[str, Any]]:
        """List all eval suites."""
        evals_dir = self.base_dir / "evals"
        evals = []
        for f in evals_dir.glob("*.yaml"):
            try:
                import yaml
                content = yaml.safe_load(f.read_text())
                evals.append({
                    "id": f.stem,
                    "name": content.get("name", f.stem),
                    "skill": content.get("skill", ""),
                    "version": content.get("version", "1.0"),
                    "path": str(f),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
            except Exception:
                continue
        return sorted(evals, key=lambda x: x["modified"], reverse=True)

    def get_eval(self, eval_id: str) -> dict[str, Any] | None:
        """Get eval by ID."""
        eval_path = self.base_dir / "evals" / f"{eval_id}.yaml"
        if not eval_path.exists():
            return None
        import yaml
        content = yaml.safe_load(eval_path.read_text())
        return {
            "id": eval_id,
            "path": str(eval_path),
            "content": content,
            "raw": eval_path.read_text(),
        }

    def save_eval(self, eval_id: str, content: str) -> dict[str, Any]:
        """Save eval content."""
        eval_path = self.base_dir / "evals" / f"{eval_id}.yaml"
        eval_path.write_text(content)
        return self.get_eval(eval_id)  # type: ignore

    def delete_eval(self, eval_id: str) -> bool:
        """Delete an eval and its tasks directory."""
        eval_path = self.base_dir / "evals" / f"{eval_id}.yaml"
        tasks_dir = self.base_dir / "evals" / eval_id
        if eval_path.exists():
            eval_path.unlink()
            if tasks_dir.exists():
                shutil.rmtree(tasks_dir)
            return True
        return False

    def create_eval(self, name: str, content: str) -> dict[str, Any]:
        """Create a new eval."""
        eval_id = name.lower().replace(" ", "-")
        eval_id = "".join(c if c.isalnum() or c == "-" else "" for c in eval_id)
        return self.save_eval(eval_id, content)

    # Task management
    def list_tasks(self, eval_id: str) -> list[dict[str, Any]]:
        """List all tasks in an eval."""
        import yaml
        tasks_dir = self.base_dir / "evals" / eval_id / "tasks"
        if not tasks_dir.exists():
            # Check if eval references external tasks
            eval_data = self.get_eval(eval_id)
            if eval_data and eval_data.get("content"):
                # Return inline tasks if any
                inline_tasks = eval_data["content"].get("tasks", [])
                if isinstance(inline_tasks, list) and inline_tasks:
                    # Check if they're file patterns or inline task dicts
                    tasks = []
                    for i, t in enumerate(inline_tasks):
                        if isinstance(t, dict):
                            tasks.append({
                                "id": t.get("id", f"task-{i}"),
                                "name": t.get("name", f"Task {i+1}"),
                                "prompt": t.get("prompt", "")[:100],
                                "graders": list(t.get("graders", {}).keys()) if isinstance(t.get("graders"), dict) else [],
                            })
                    return tasks
            return []

        tasks = []
        for f in tasks_dir.glob("*.yaml"):
            try:
                content = yaml.safe_load(f.read_text())
                tasks.append({
                    "id": f.stem,
                    "name": content.get("name", f.stem),
                    "prompt": content.get("prompt", "")[:100],
                    "graders": list(content.get("graders", {}).keys()) if isinstance(content.get("graders"), dict) else [],
                    "path": str(f),
                })
            except Exception:
                continue
        return sorted(tasks, key=lambda x: x["name"])

    def get_task(self, eval_id: str, task_id: str) -> dict[str, Any] | None:
        """Get a single task by ID."""
        import yaml
        task_path = self.base_dir / "evals" / eval_id / "tasks" / f"{task_id}.yaml"
        if not task_path.exists():
            return None
        content = yaml.safe_load(task_path.read_text())
        return {
            "id": task_id,
            "path": str(task_path),
            "content": content,
            "raw": task_path.read_text(),
        }

    def save_task(self, eval_id: str, task_id: str, content: str) -> dict[str, Any]:
        """Save task content."""
        tasks_dir = self.base_dir / "evals" / eval_id / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        task_path = tasks_dir / f"{task_id}.yaml"
        task_path.write_text(content)
        return self.get_task(eval_id, task_id)  # type: ignore

    def create_task(self, eval_id: str, name: str, content: str) -> dict[str, Any]:
        """Create a new task."""
        task_id = name.lower().replace(" ", "-")
        task_id = "".join(c if c.isalnum() or c == "-" else "" for c in task_id)
        # Ensure unique ID
        tasks_dir = self.base_dir / "evals" / eval_id / "tasks"
        if tasks_dir.exists() and (tasks_dir / f"{task_id}.yaml").exists():
            task_id = f"{task_id}-{uuid.uuid4().hex[:6]}"
        return self.save_task(eval_id, task_id, content)

    def duplicate_task(self, eval_id: str, task_id: str) -> dict[str, Any] | None:
        """Duplicate a task with a new ID."""
        original = self.get_task(eval_id, task_id)
        if not original:
            return None
        new_id = f"{task_id}-copy-{uuid.uuid4().hex[:6]}"
        return self.save_task(eval_id, new_id, original["raw"])

    def delete_task(self, eval_id: str, task_id: str) -> bool:
        """Delete a task."""
        task_path = self.base_dir / "evals" / eval_id / "tasks" / f"{task_id}.yaml"
        if task_path.exists():
            task_path.unlink()
            return True
        return False

    # Runs management
    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent runs."""
        runs_dir = self.base_dir / "runs"
        runs = []
        for d in runs_dir.iterdir():
            if d.is_dir():
                results_file = d / "results.json"
                if results_file.exists():
                    try:
                        results = json.loads(results_file.read_text())
                        runs.append({
                            "id": d.name,
                            "eval_name": results.get("eval_name", ""),
                            "status": results.get("status", "completed"),
                            "pass_rate": results.get("summary", {}).get("pass_rate", 0),
                            "score": results.get("summary", {}).get("composite_score", 0),
                            "timestamp": results.get("timestamp", d.name[:19]),
                            "duration_ms": results.get("duration_ms", 0),
                        })
                    except Exception:
                        continue
        return sorted(runs, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Get run details."""
        run_dir = self.base_dir / "runs" / run_id
        if not run_dir.exists():
            return None

        result: dict[str, Any] = {"id": run_id}

        results_file = run_dir / "results.json"
        if results_file.exists():
            result["results"] = json.loads(results_file.read_text())

        transcript_file = run_dir / "transcript.json"
        if transcript_file.exists():
            result["transcript"] = json.loads(transcript_file.read_text())

        suggestions_file = run_dir / "suggestions.md"
        if suggestions_file.exists():
            result["suggestions"] = suggestions_file.read_text()

        return result

    def create_run(self, eval_id: str) -> str:
        """Create a new run directory."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_id = f"{timestamp}-{eval_id}-{uuid.uuid4().hex[:8]}"
        run_dir = self.base_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Write initial status
        (run_dir / "results.json").write_text(json.dumps({
            "eval_name": eval_id,
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
        }))

        return run_id

    def update_run(self, run_id: str, results: dict[str, Any]) -> None:
        """Update run results."""
        run_dir = self.base_dir / "runs" / run_id
        if run_dir.exists():
            (run_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))

    def save_run_transcript(self, run_id: str, transcript: list[dict[str, Any]]) -> None:
        """Save run transcript."""
        run_dir = self.base_dir / "runs" / run_id
        if run_dir.exists():
            (run_dir / "transcript.json").write_text(json.dumps(transcript, indent=2))

    def save_run_suggestions(self, run_id: str, suggestions: str) -> None:
        """Save run suggestions."""
        run_dir = self.base_dir / "runs" / run_id
        if run_dir.exists():
            (run_dir / "suggestions.md").write_text(suggestions)

    def delete_run(self, run_id: str) -> bool:
        """Delete a run."""
        run_dir = self.base_dir / "runs" / run_id
        if run_dir.exists():
            shutil.rmtree(run_dir)
            return True
        return False


# Global storage instance
_storage: StorageManager | None = None


def get_storage() -> StorageManager:
    """Get the global storage instance."""
    global _storage
    if _storage is None:
        _storage = StorageManager()
    return _storage
