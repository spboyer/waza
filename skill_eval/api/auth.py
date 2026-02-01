"""GitHub OAuth authentication for skill-eval API."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

router = APIRouter()

# OAuth configuration (can be set via environment variables)
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/callback")

# In-memory session store (TODO: use proper session management)
sessions: dict[str, dict[str, Any]] = {}


class AuthStatus(BaseModel):
    """Authentication status response."""
    authenticated: bool
    user: dict[str, Any] | None = None
    scopes: list[str] | None = None


@router.get("/status")
async def get_auth_status(request: Request) -> AuthStatus:
    """Check if user is authenticated."""
    session_id = request.cookies.get("session_id")
    
    if session_id and session_id in sessions:
        session = sessions[session_id]
        return AuthStatus(
            authenticated=True,
            user=session.get("user"),
            scopes=session.get("scopes", [])
        )
    
    return AuthStatus(authenticated=False)


@router.get("/login")
async def initiate_oauth():
    """Initiate GitHub OAuth flow."""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID environment variable."
        )
    
    # GitHub OAuth authorization URL
    scopes = "repo read:user copilot"
    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&scope={scopes}"
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def oauth_callback(code: str, response: Response):
    """Handle GitHub OAuth callback."""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth not configured"
        )
    
    # Exchange code for access token
    import httpx
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"}
        )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        
        user_data = user_response.json()
        
        # Create session
        import secrets
        session_id = secrets.token_urlsafe(32)
        
        sessions[session_id] = {
            "access_token": access_token,
            "user": {
                "login": user_data.get("login"),
                "name": user_data.get("name"),
                "avatar_url": user_data.get("avatar_url"),
                "email": user_data.get("email"),
            },
            "scopes": token_data.get("scope", "").split(","),
        }
        
        # Set cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=86400 * 30,  # 30 days
            samesite="lax"
        )
        
        # Redirect to dashboard
        return RedirectResponse(url="/")


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session."""
    session_id = request.cookies.get("session_id")
    
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    response.delete_cookie("session_id")
    
    return {"success": True}


def get_current_user(request: Request) -> dict[str, Any] | None:
    """Get current authenticated user from request."""
    session_id = request.cookies.get("session_id")
    
    if session_id and session_id in sessions:
        return sessions[session_id].get("user")
    
    return None


def get_access_token(request: Request) -> str | None:
    """Get GitHub access token for current user."""
    session_id = request.cookies.get("session_id")
    
    if session_id and session_id in sessions:
        return sessions[session_id].get("access_token")
    
    return None


def require_auth(request: Request) -> dict[str, Any]:
    """Require authentication, raise exception if not authenticated."""
    user = get_current_user(request)
    
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return user
