"""GitHub authentication for waza Web UI.

Supports two modes:
1. Azure Easy Auth - When deployed to Azure App Service with GitHub provider
2. Local gh CLI - When running via `waza serve`, reuses `gh auth token`
"""

from __future__ import annotations

import os
import secrets
import subprocess
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

# OAuth configuration from environment (optional, for custom OAuth apps)
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8080/api/auth/callback")

# In-memory session store (use Redis/DB in production)
sessions: dict[str, dict[str, Any]] = {}

# Cached gh CLI token
_gh_cli_token: str | None = None
_gh_cli_user: dict[str, Any] | None = None


def is_azure_easy_auth(request: Request) -> bool:
    """Check if request is coming through Azure Easy Auth."""
    return "X-MS-CLIENT-PRINCIPAL" in request.headers


def get_azure_easy_auth_user(request: Request) -> dict[str, Any] | None:
    """Extract user info from Azure Easy Auth headers."""
    if not is_azure_easy_auth(request):
        return None

    # Azure Easy Auth provides these headers when GitHub is configured as provider
    return {
        "login": request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME", ""),
        "name": request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME", ""),
        "id": request.headers.get("X-MS-CLIENT-PRINCIPAL-ID", ""),
        "access_token": request.headers.get("X-MS-TOKEN-GITHUB-ACCESS-TOKEN", ""),
        "auth_type": "azure_easy_auth",
    }


def get_gh_cli_token() -> str | None:
    """Get GitHub token from gh CLI (cached)."""
    global _gh_cli_token
    if _gh_cli_token:
        return _gh_cli_token

    # Check environment variable first
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        _gh_cli_token = token
        return token

    # Try gh CLI
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            _gh_cli_token = result.stdout.strip()
            return _gh_cli_token
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


async def get_gh_cli_user() -> dict[str, Any] | None:
    """Get user info using gh CLI token."""
    global _gh_cli_user
    if _gh_cli_user:
        return _gh_cli_user

    token = get_gh_cli_token()
    if not token:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=10,
            )
            if response.status_code == 200:
                user_data = response.json()
                _gh_cli_user = {
                    "login": user_data.get("login"),
                    "name": user_data.get("name"),
                    "avatar_url": user_data.get("avatar_url"),
                    "access_token": token,
                    "auth_type": "gh_cli",
                }
                return _gh_cli_user
    except Exception:
        pass

    return None


def is_oauth_configured() -> bool:
    """Check if GitHub OAuth is configured."""
    return bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)


def is_gh_cli_available() -> bool:
    """Check if gh CLI auth is available."""
    return get_gh_cli_token() is not None


@router.get("/status")
async def auth_status(request: Request, response: Response) -> dict[str, Any]:
    """Get current authentication status.

    Checks in order:
    1. Azure Easy Auth headers (when deployed to Azure)
    2. Session cookie (OAuth flow)
    3. gh CLI token (local development)
    """
    # Check Azure Easy Auth first
    if is_azure_easy_auth(request):
        user = get_azure_easy_auth_user(request)
        if user and user.get("login"):
            return {
                "authenticated": True,
                "user": {
                    "login": user.get("login"),
                    "name": user.get("name"),
                    "avatar_url": None,
                },
                "auth_type": "azure_easy_auth",
                "oauth_configured": True,
            }

    # Check session cookie
    session_id = request.cookies.get("waza_session")
    if session_id and session_id in sessions:
        user = sessions[session_id]
        return {
            "authenticated": True,
            "user": {
                "login": user.get("login"),
                "name": user.get("name"),
                "avatar_url": user.get("avatar_url"),
            },
            "auth_type": user.get("auth_type", "oauth"),
            "oauth_configured": is_oauth_configured(),
        }

    # Check gh CLI token (auto-auth for local development)
    gh_user = await get_gh_cli_user()
    if gh_user:
        # Auto-create session for gh CLI user and set cookie
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = gh_user

        # Set the session cookie so subsequent requests are authenticated
        response.set_cookie(
            key="waza_session",
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,  # 1 week
        )

        return {
            "authenticated": True,
            "user": {
                "login": gh_user.get("login"),
                "name": gh_user.get("name"),
                "avatar_url": gh_user.get("avatar_url"),
            },
            "auth_type": "gh_cli",
            "oauth_configured": is_oauth_configured(),
            "auto_authenticated": True,
        }

    return {
        "authenticated": False,
        "user": None,
        "auth_type": None,
        "oauth_configured": is_oauth_configured(),
        "gh_cli_available": is_gh_cli_available(),
    }


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """Initiate authentication.

    - If gh CLI is available, auto-authenticate and redirect
    - Otherwise, use GitHub OAuth flow
    """
    # Try gh CLI first for local development
    gh_user = await get_gh_cli_user()
    if gh_user:
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = gh_user

        redirect = RedirectResponse(url="/", status_code=302)
        redirect.set_cookie(
            key="waza_session",
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,  # 1 week
        )
        return redirect

    # Fall back to OAuth
    if not is_oauth_configured():
        raise HTTPException(
            status_code=400,
            detail="Authentication not available. Run 'gh auth login' to authenticate via GitHub CLI.",
        )

    state = secrets.token_urlsafe(32)
    # Store state for verification (in production, use Redis with TTL)
    sessions[f"state:{state}"] = {"valid": True}

    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&scope=repo,read:user,copilot"
        f"&state={state}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def oauth_callback(code: str, state: str, response: Response) -> RedirectResponse:
    """Handle GitHub OAuth callback."""
    # Verify state
    state_key = f"state:{state}"
    if state_key not in sessions:
        raise HTTPException(status_code=400, detail="Invalid state")
    del sessions[state_key]

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")

        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        user_data = user_response.json()

    # Create session
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "login": user_data.get("login"),
        "name": user_data.get("name"),
        "avatar_url": user_data.get("avatar_url"),
        "access_token": access_token,
        "auth_type": "oauth",
    }

    # Redirect to frontend with session cookie
    redirect = RedirectResponse(url="/", status_code=302)
    redirect.set_cookie(
        key="waza_session",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 1 week
    )

    return redirect


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict[str, str]:
    """Log out the current user."""
    global _gh_cli_user

    session_id = request.cookies.get("waza_session")

    if session_id and session_id in sessions:
        del sessions[session_id]

    # Clear cached gh CLI user so it re-fetches on next request
    _gh_cli_user = None

    response.delete_cookie("waza_session")
    return {"status": "logged_out"}


def get_current_user(request: Request) -> dict[str, Any] | None:
    """Get the current user from session or auto-auth sources.

    Checks in order:
    1. Azure Easy Auth headers
    2. Session cookie
    3. gh CLI token (cached)
    """
    # Check Azure Easy Auth
    if is_azure_easy_auth(request):
        return get_azure_easy_auth_user(request)

    # Check session cookie
    session_id = request.cookies.get("waza_session")
    if session_id and session_id in sessions:
        return sessions[session_id]

    # Check cached gh CLI user (populated by get_gh_cli_user or auth/status)
    if _gh_cli_user:
        return _gh_cli_user

    # Last resort: try to get gh CLI token synchronously
    token = get_gh_cli_token()
    if token:
        # Return a minimal user dict with the token
        return {
            "login": "gh-cli-user",
            "access_token": token,
            "auth_type": "gh_cli",
        }

    return None


def require_auth(request: Request) -> dict[str, Any]:
    """Require authentication (raises HTTPException if not authenticated)."""
    user = get_current_user(request)
    if not user:
        # Provide helpful error message
        if is_gh_cli_available():
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Visit /api/auth/login to authenticate.",
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Run 'gh auth login' first, then restart the server.",
            )
    return user
