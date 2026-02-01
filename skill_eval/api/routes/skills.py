"""Skills endpoints for skill-eval API (requires authentication)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class SkillScan(BaseModel):
    """Model for scanning a repo for skills."""
    repo_url: str


class SkillGenerate(BaseModel):
    """Model for generating an eval from SKILL.md."""
    skill_url: str
    output_dir: str | None = None
    assist: bool = False


@router.post("/scan")
async def scan_repo(scan: SkillScan):
    """Scan a GitHub repo for skills (requires authentication)."""
    # TODO: Implement skill scanning
    # This will use GitHub API to find SKILL.md files
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/generate")
async def generate_eval(gen: SkillGenerate):
    """Generate an eval from a SKILL.md file (requires authentication)."""
    # TODO: Implement eval generation
    # This will use the existing generator logic
    raise HTTPException(status_code=501, detail="Not implemented yet")
