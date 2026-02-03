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
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate")
async def generate_eval(data: GenerateRequest, request: Request) -> dict[str, Any]:
    """Generate an eval from a SKILL.md URL."""
    # Auth required for LLM-assisted generation
    if data.assist:
        require_auth(request)
    
    try:
        from waza.generator import EvalGenerator, SkillParser
        
        parser = SkillParser()
        skill = parser.parse_url(data.skill_url)
        
        generator = EvalGenerator(skill)
        
        # Generate eval content
        eval_yaml = generator.generate_eval_yaml()
        trigger_tests = generator.generate_trigger_tests()
        
        # Determine name
        name = data.name or skill.name or "generated-eval"
        
        # Save to storage
        storage = get_storage()
        eval_data = storage.create_eval(name, eval_yaml)
        
        return {
            "eval_id": eval_data["id"],
            "skill_name": skill.name,
            "triggers_count": len(skill.triggers),
            "eval_yaml": eval_yaml,
            "trigger_tests": trigger_tests,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
