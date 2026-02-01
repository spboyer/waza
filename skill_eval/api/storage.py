"""Storage layer for skill-eval API using JSON files."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class StorageManager:
    """Manages JSON file storage in ~/.skill-eval/."""

    def __init__(self, base_path: Path | None = None):
        """Initialize storage manager.
        
        Args:
            base_path: Base directory for storage (defaults to ~/.skill-eval/)
        """
        self.base_path = base_path or Path.home() / ".skill-eval"
        self.evals_dir = self.base_path / "evals"
        self.runs_dir = self.base_path / "runs"
        self.cache_dir = self.base_path / "cache"
        self.config_file = self.base_path / "config.json"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        for directory in [self.evals_dir, self.runs_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    # Eval operations
    def list_evals(self) -> list[dict[str, Any]]:
        """List all eval suite definitions."""
        evals = []
        for eval_file in self.evals_dir.glob("*.yaml"):
            try:
                import yaml
                with open(eval_file, "r") as f:
                    data = yaml.safe_load(f)
                    data["id"] = eval_file.stem
                    data["path"] = str(eval_file)
                    evals.append(data)
            except Exception:
                continue
        return evals
    
    def get_eval(self, eval_id: str) -> dict[str, Any] | None:
        """Get a specific eval by ID."""
        eval_file = self.evals_dir / f"{eval_id}.yaml"
        if not eval_file.exists():
            return None
        
        try:
            import yaml
            with open(eval_file, "r") as f:
                data = yaml.safe_load(f)
                data["id"] = eval_id
                data["path"] = str(eval_file)
                return data
        except Exception:
            return None
    
    def create_eval(self, eval_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new eval suite."""
        eval_file = self.evals_dir / f"{eval_id}.yaml"
        
        import yaml
        with open(eval_file, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        
        return {"id": eval_id, "path": str(eval_file), **data}
    
    def update_eval(self, eval_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update an existing eval suite."""
        eval_file = self.evals_dir / f"{eval_id}.yaml"
        if not eval_file.exists():
            return None
        
        import yaml
        with open(eval_file, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        
        return {"id": eval_id, "path": str(eval_file), **data}
    
    def delete_eval(self, eval_id: str) -> bool:
        """Delete an eval suite."""
        eval_file = self.evals_dir / f"{eval_id}.yaml"
        if not eval_file.exists():
            return False
        
        eval_file.unlink()
        return True
    
    # Run operations
    def list_runs(self) -> list[dict[str, Any]]:
        """List all eval runs."""
        runs = []
        for run_dir in sorted(self.runs_dir.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue
            
            results_file = run_dir / "results.json"
            if not results_file.exists():
                continue
            
            try:
                with open(results_file, "r") as f:
                    data = json.load(f)
                    data["run_id"] = run_dir.name
                    runs.append(data)
            except Exception:
                continue
        
        return runs
    
    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Get a specific run by ID."""
        run_dir = self.runs_dir / run_id
        if not run_dir.exists():
            return None
        
        results_file = run_dir / "results.json"
        if not results_file.exists():
            return None
        
        try:
            with open(results_file, "r") as f:
                data = json.load(f)
                data["run_id"] = run_id
                
                # Include transcript if available
                transcript_file = run_dir / "transcript.json"
                if transcript_file.exists():
                    with open(transcript_file, "r") as tf:
                        data["transcript"] = json.load(tf)
                
                # Include suggestions if available
                suggestions_file = run_dir / "suggestions.md"
                if suggestions_file.exists():
                    with open(suggestions_file, "r") as sf:
                        data["suggestions"] = sf.read()
                
                return data
        except Exception:
            return None
    
    def create_run(self, eval_id: str) -> str:
        """Create a new run directory and return run_id."""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        run_id = f"{timestamp}-{eval_id}"
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_id
    
    def save_run_results(self, run_id: str, results: dict[str, Any]) -> None:
        """Save run results to JSON file."""
        run_dir = self.runs_dir / run_id
        results_file = run_dir / "results.json"
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
    
    def save_run_transcript(self, run_id: str, transcript: list[dict[str, Any]]) -> None:
        """Save run transcript to JSON file."""
        run_dir = self.runs_dir / run_id
        transcript_file = run_dir / "transcript.json"
        
        with open(transcript_file, "w") as f:
            json.dump(transcript, f, indent=2)
    
    def save_run_suggestions(self, run_id: str, suggestions: str) -> None:
        """Save run suggestions to markdown file."""
        run_dir = self.runs_dir / run_id
        suggestions_file = run_dir / "suggestions.md"
        
        with open(suggestions_file, "w") as f:
            f.write(suggestions)
    
    # Config operations
    def get_config(self) -> dict[str, Any]:
        """Get user configuration."""
        if not self.config_file.exists():
            return self._default_config()
        
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception:
            return self._default_config()
    
    def update_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Update user configuration."""
        current = self.get_config()
        current.update(config)
        
        with open(self.config_file, "w") as f:
            json.dump(current, f, indent=2)
        
        return current
    
    def _default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            "model": "claude-sonnet-4-20250514",
            "executor": "mock",
            "theme": "dark",
            "github_token": None,
        }
