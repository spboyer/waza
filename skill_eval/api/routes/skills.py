"""Skills endpoints for skill-eval API (requires authentication)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from skill_eval.api import auth

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
async def scan_repo(scan: SkillScan, request: Request):
    """Scan a GitHub repo for skills (requires authentication)."""
    # Require authentication
    user = auth.require_auth(request)
    access_token = auth.get_access_token(request)
    
    if not access_token:
        raise HTTPException(status_code=401, detail="GitHub access token required")
    
    # Parse repo URL to get owner/repo
    import re
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)", scan.repo_url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub repo URL")
    
    owner, repo = match.groups()
    repo = repo.replace(".git", "")
    
    # Search for SKILL.md files using GitHub API
    import httpx
    
    async with httpx.AsyncClient() as client:
        # Search for SKILL.md files in the repo
        search_response = await client.get(
            f"https://api.github.com/search/code",
            params={
                "q": f"filename:SKILL.md repo:{owner}/{repo}",
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json"
            }
        )
        
        if search_response.status_code != 200:
            raise HTTPException(
                status_code=search_response.status_code,
                detail=f"GitHub API error: {search_response.text}"
            )
        
        search_data = search_response.json()
        skills = []
        
        for item in search_data.get("items", []):
            skills.append({
                "name": item.get("name"),
                "path": item.get("path"),
                "url": item.get("html_url"),
                "repo": f"{owner}/{repo}",
            })
        
        return {
            "repo": f"{owner}/{repo}",
            "skills": skills,
            "count": len(skills)
        }


@router.post("/generate")
async def generate_eval(gen: SkillGenerate, request: Request):
    """Generate an eval from a SKILL.md file (requires authentication)."""
    # Require authentication
    user = auth.require_auth(request)
    
    # Use the existing generator logic
    from skill_eval.generator import AssistedGenerator, EvalGenerator
    from pathlib import Path
    import tempfile
    
    try:
        # Download SKILL.md content
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(gen.skill_url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch SKILL.md: {response.text}"
                )
            
            skill_content = response.text
        
        # Create temporary directory for generation
        temp_dir = tempfile.mkdtemp(prefix="skill-eval-gen-")
        output_path = Path(temp_dir)
        
        # Generate eval using AssistedGenerator if requested
        if gen.assist:
            generator = AssistedGenerator()
        else:
            generator = EvalGenerator()
        
        # Save SKILL.md to temp file
        skill_file = output_path / "SKILL.md"
        skill_file.write_text(skill_content)
        
        # Generate eval spec
        eval_spec = generator.generate_from_skill(str(skill_file))
        
        # Return the generated spec
        return {
            "success": True,
            "eval_spec": eval_spec,
            "output_dir": str(output_path)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
