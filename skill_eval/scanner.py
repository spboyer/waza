"""Scanner for discovering skills in GitHub and local repositories.

Provides functionality to:
- Scan GitHub repositories for SKILL.md files
- Scan local git repositories for skills
- Extract skill metadata from SKILL.md files
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from skill_eval.generator import SkillParser


@dataclass
class SkillInfo:
    """Information about a discovered skill."""

    name: str
    description: str
    path: str  # Local path or GitHub path (e.g., "skills/my-skill")
    url: str | None = None  # GitHub URL if from remote repo
    repo: str | None = None  # GitHub repo (e.g., "owner/repo")

    def __str__(self) -> str:
        """String representation for display."""
        if self.description:
            return f"{self.name}: {self.description[:60]}{'...' if len(self.description) > 60 else ''}"
        return self.name


class SkillScanner:
    """Scanner for discovering skills in repositories."""

    def __init__(self) -> None:
        """Initialize the scanner."""
        self.parser = SkillParser()

    def scan_github_repo(self, repo: str, branch: str = "main") -> list[SkillInfo]:
        """Scan a GitHub repository for SKILL.md files.

        Args:
            repo: Repository in format "owner/repo"
            branch: Branch to scan (default: main)

        Returns:
            List of discovered skills

        Raises:
            RuntimeError: If gh CLI is not available or API call fails
        """
        # Check if gh CLI is available
        if not self._check_gh_cli():
            raise RuntimeError(
                "GitHub CLI (gh) is required for scanning GitHub repos. "
                "Install from https://cli.github.com/"
            )

        # Use GitHub API to search for SKILL.md files
        try:
            result = subprocess.run(
                [
                    "gh",
                    "api",
                    f"/repos/{repo}/git/trees/{branch}?recursive=1",
                    "--jq",
                    '.tree[] | select(.path | endswith("SKILL.md")) | .path',
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            skill_paths = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to scan repository {repo}: {e.stderr}"
            ) from e

        if not skill_paths:
            return []

        # Fetch content and parse each SKILL.md
        skills = []
        for path in skill_paths:
            try:
                skill_info = self._fetch_github_skill(repo, path, branch)
                if skill_info:
                    skills.append(skill_info)
            except Exception as e:
                # Log error but continue with other skills
                print(f"Warning: Failed to parse {path}: {e}")
                continue

        return skills

    def scan_local_repo(self, path: str | Path = ".") -> list[SkillInfo]:
        """Scan a local repository for SKILL.md files.

        Args:
            path: Path to the repository (default: current directory)

        Returns:
            List of discovered skills
        """
        repo_path = Path(path).resolve()
        if not repo_path.exists():
            raise ValueError(f"Path does not exist: {repo_path}")

        # Find all SKILL.md files
        skill_files = list(repo_path.rglob("SKILL.md"))

        skills = []
        for skill_file in skill_files:
            try:
                parsed = self.parser.parse_file(skill_file)
                rel_path = skill_file.parent.relative_to(repo_path)

                skill_info = SkillInfo(
                    name=parsed.name or skill_file.parent.name,
                    description=parsed.description,
                    path=str(rel_path),
                    url=None,
                    repo=None,
                )
                skills.append(skill_info)
            except Exception as e:
                # Log error but continue with other skills
                print(f"Warning: Failed to parse {skill_file}: {e}")
                continue

        return skills

    def _check_gh_cli(self) -> bool:
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

    def _fetch_github_skill(
        self, repo: str, path: str, branch: str
    ) -> SkillInfo | None:
        """Fetch and parse a SKILL.md from GitHub.

        Args:
            repo: Repository in format "owner/repo"
            path: Path to SKILL.md in repo
            branch: Branch name

        Returns:
            SkillInfo if successful, None otherwise
        """
        try:
            # Fetch file content using gh CLI
            result = subprocess.run(
                [
                    "gh",
                    "api",
                    f"/repos/{repo}/contents/{path}",
                    "--jq=.content",
                    "-H",
                    "Accept: application/vnd.github.raw",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            content = result.stdout

            # Parse the skill
            parsed = self.parser.parse(content)

            # Extract skill directory path
            skill_dir = str(Path(path).parent)

            # Construct GitHub URL
            url = f"https://github.com/{repo}/blob/{branch}/{path}"

            return SkillInfo(
                name=parsed.name or Path(path).parent.name,
                description=parsed.description,
                path=skill_dir,
                url=url,
                repo=repo,
            )
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to fetch {path}: {e.stderr}")
            return None


def parse_repo_arg(repo_arg: str) -> str:
    """Parse repository argument into owner/repo format.

    Accepts:
    - owner/repo
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git

    Args:
        repo_arg: Repository argument from user

    Returns:
        Repository in "owner/repo" format

    Raises:
        ValueError: If format is invalid
    """
    repo_arg = repo_arg.strip()

    # Handle GitHub URLs
    if repo_arg.startswith(("http://", "https://")):
        # Extract owner/repo from URL
        parts = repo_arg.rstrip("/").split("/")
        if len(parts) >= 2:
            owner = parts[-2]
            repo = parts[-1].replace(".git", "")
            return f"{owner}/{repo}"
        raise ValueError(f"Invalid GitHub URL: {repo_arg}")

    # Handle owner/repo format
    if "/" in repo_arg:
        parts = repo_arg.split("/")
        if len(parts) == 2:
            return repo_arg
        raise ValueError(f"Invalid repository format: {repo_arg}")

    raise ValueError(
        f"Invalid repository: {repo_arg}. "
        "Use format 'owner/repo' or GitHub URL"
    )
