"""Skills scanning and generation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from waza.api.auth import require_auth
from waza.api.storage import get_storage

router = APIRouter(prefix="/api/skills", tags=["skills"])


class ScanRequest(BaseModel):
    """Request model for scanning a repo."""
    repo: str  # e.g., "microsoft/GitHub-Copilot-for-Azure"


class GenerateRequest(BaseModel):
    """Request model for generating an eval from a SKILL.md."""
    skill_url: str
    name: str | None = None
    assist: bool = False


@router.post("/scan")
async def scan_repo(data: ScanRequest, request: Request) -> list[dict[str, Any]]:
    """Scan a GitHub repo for skills (requires auth)."""
    user = require_auth(request)
    access_token = user.get("access_token")

    try:
        from waza.scanner import SkillScanner

        scanner = SkillScanner(github_token=access_token)
        skills = scanner.scan_github_repo(data.repo)

        return [
            {
                "name": s.name,
                "path": s.path,
                "url": s.url,
                "description": s.description[:200] if s.description else "",
            }
            for s in skills
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/generate")
async def generate_eval(data: GenerateRequest, request: Request) -> dict[str, Any]:
    """Generate an eval from a SKILL.md URL.

    Creates the eval YAML and tasks files in storage.
    """
    # Auth required for LLM-assisted generation
    if data.assist:
        require_auth(request)

    try:
        from waza.generator import EvalGenerator, SkillParser

        parser = SkillParser()
        skill = parser.parse_url(data.skill_url)

        generator = EvalGenerator(skill)

        # Determine name
        name = data.name or skill.name or "generated-eval"
        eval_id = name.lower().replace(" ", "-")
        eval_id = "".join(c if c.isalnum() or c == "-" else "" for c in eval_id)

        # Generate eval content
        eval_yaml = generator.generate_eval_yaml()
        trigger_tests = generator.generate_trigger_tests()

        # Generate tasks
        tasks = generator.generate_tasks()

        # Save to storage
        storage = get_storage()

        # Create eval
        eval_data = storage.create_eval(name, eval_yaml)
        actual_eval_id = eval_data["id"]

        # Create tasks directory and save tasks
        tasks_created = []
        for task in tasks:
            import yaml
            task_name = task.get("name", f"task-{len(tasks_created)}")
            task_id = task_name.lower().replace(" ", "-")
            task_id = "".join(c if c.isalnum() or c == "-" else "" for c in task_id)
            task_yaml = yaml.dump(task, default_flow_style=False, sort_keys=False)
            storage.create_task(actual_eval_id, task_id, task_yaml)
            tasks_created.append(task_id)

        # Save trigger tests as a separate task file
        if trigger_tests:
            storage.create_task(actual_eval_id, "trigger-tests", trigger_tests)

        return {
            "eval_id": actual_eval_id,
            "skill_name": skill.name,
            "triggers_count": len(skill.triggers),
            "tasks_created": tasks_created,
            "message": f"Created eval '{actual_eval_id}' with {len(tasks_created)} tasks",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/generate-preview")
async def generate_preview(data: GenerateRequest) -> dict[str, Any]:
    """Preview eval generation without saving (no auth required)."""
    try:
        from waza.generator import EvalGenerator, SkillParser

        parser = SkillParser()
        skill = parser.parse_url(data.skill_url)

        generator = EvalGenerator(skill)

        # Generate preview content
        eval_yaml = generator.generate_eval_yaml()
        example_tasks = generator.generate_example_tasks()  # Returns list of (name, yaml_content) tuples

        return {
            "skill_name": skill.name,
            "description": skill.description[:500] if skill.description else "",
            "triggers": skill.triggers[:10],  # First 10 triggers
            "triggers_count": len(skill.triggers),
            "eval_yaml_preview": eval_yaml[:2000],
            "tasks_count": len(example_tasks),
            "tasks_preview": [
                {
                    "name": name,
                    "content": content[:200],
                }
                for name, content in example_tasks[:5]
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
