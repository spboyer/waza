"""GitHub OAuth authentication for waza Web UI."""

from __future__ import annotations

import os
import secrets
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

# OAuth configuration from environment
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/callback")

# In-memory session store (use Redis/DB in production)
sessions: dict[str, dict[str, Any]] = {}


def is_oauth_configured() -> bool:
    """Check if GitHub OAuth is configured."""
    return bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)


@router.get("/status")
async def auth_status(request: Request) -> dict[str, Any]:
    """Get current authentication status."""
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
            "oauth_configured": is_oauth_configured(),
        }

    return {
        "authenticated": False,
        "user": None,
        "oauth_configured": is_oauth_configured(),
    }


@router.get("/login")
async def login() -> RedirectResponse:
    """Initiate GitHub OAuth login."""
    if not is_oauth_configured():
        raise HTTPException(status_code=400, detail="GitHub OAuth not configured")

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
    session_id = request.cookies.get("waza_session")

    if session_id and session_id in sessions:
        del sessions[session_id]

    response.delete_cookie("waza_session")
    return {"status": "logged_out"}


def get_current_user(request: Request) -> dict[str, Any] | None:
    """Get the current user from session (helper for other routes)."""
    session_id = request.cookies.get("waza_session")
    if session_id and session_id in sessions:
        return sessions[session_id]
    return None


def require_auth(request: Request) -> dict[str, Any]:
    """Require authentication (raises HTTPException if not authenticated)."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
