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
    model: str | None = None  # Model to use for LLM-assisted generation


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
    If assist=True, uses LLM to generate better tasks (requires auth).
    """
    # Auth required for LLM-assisted generation
    if data.assist:
        require_auth(request)

    try:
        from waza.generator import EvalGenerator, SkillParser

        parser = SkillParser()
        skill = parser.parse_url(data.skill_url)

        # Determine name
        name = data.name or skill.name or "generated-eval"
        eval_id = name.lower().replace(" ", "-")
        eval_id = "".join(c if c.isalnum() or c == "-" else "" for c in eval_id)

        if data.assist:
            # Use LLM-assisted generation for tasks, pattern-based for eval.yaml
            from waza.generator import AssistedGenerator, EvalGenerator

            # Generate eval.yaml using pattern-based generator
            basic_generator = EvalGenerator(skill)
            eval_yaml = basic_generator.generate_eval_yaml()

            # Generate tasks using LLM
            assisted = AssistedGenerator(skill, model=data.model or "claude-sonnet-4-20250514")
            try:
                await assisted.setup()
                result = await assisted.generate_all()
            finally:
                await assisted.teardown()

            tasks_data = result["tasks"]  # List of dicts with task data
            fixtures = result.get("fixtures", [])

            # Save to storage
            storage = get_storage()

            # Create eval
            eval_data = storage.create_eval(name, eval_yaml)
            actual_eval_id = eval_data["id"]

            # Save tasks
            import yaml
            tasks_created = []
            for i, task in enumerate(tasks_data):
                task_name = task.get("name", f"task-{i+1:03d}")
                task_id = task_name.lower().replace(" ", "-")
                task_id = "".join(c if c.isalnum() or c == "-" else "" for c in task_id)
                task_yaml = yaml.dump(task, default_flow_style=False, sort_keys=False)
                storage.create_task(actual_eval_id, task_id, task_yaml)
                tasks_created.append(task_id)

            return {
                "eval_id": actual_eval_id,
                "skill_name": skill.name,
                "triggers_count": len(skill.triggers),
                "tasks_created": tasks_created,
                "fixtures_created": len(fixtures),
                "message": f"Created eval '{actual_eval_id}' with {len(tasks_created)} LLM-generated tasks",
                "assist": True,
            }
        else:
            # Use pattern-based generation
            generator = EvalGenerator(skill)

            # Generate eval content
            eval_yaml = generator.generate_eval_yaml()
            trigger_tests = generator.generate_trigger_tests()

            # Generate tasks - returns list of (name, yaml_content) tuples
            example_tasks = generator.generate_example_tasks()

            # Save to storage
            storage = get_storage()

            # Create eval
            eval_data = storage.create_eval(name, eval_yaml)
            actual_eval_id = eval_data["id"]

            # Create tasks directory and save tasks
            tasks_created = []
            for task_name, task_yaml in example_tasks:
                task_id = task_name.replace(".yaml", "").lower().replace(" ", "-")
                task_id = "".join(c if c.isalnum() or c == "-" else "" for c in task_id)
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
                "assist": False,
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
