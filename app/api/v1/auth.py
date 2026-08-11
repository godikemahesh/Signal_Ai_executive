"""
Signal — Auth API Endpoints
Google OAuth flow login and callback.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import UserProfile
from app.schemas.auth import TokenResponse, UserProfileResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/google/login")
async def google_login():
    """Get Google OAuth consent screen URL."""
    auth_url = AuthService.get_google_auth_url()
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Exchange Google OAuth code for JWT token and user profile."""
    try:
        res = await AuthService.process_google_callback(code, db)
        token = res["access_token"]

        from app.config import get_settings
        settings = get_settings()
        target_frontend = settings.frontend_url or (settings.cors_origins_list[0] if settings.cors_origins_list else "http://localhost:5173")
        target_frontend = target_frontend.rstrip('/')

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authenticating...</title>
            <style>
                body {{ font-family: system-ui, sans-serif; background: #0f172a; color: white; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; text-align: center; }}
                .card {{ background: #1e293b; padding: 2rem; border-radius: 1rem; border: 1px solid #334155; max-width: 400px; }}
                a {{ color: #60a5fa; text-decoration: none; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>Authentication Successful!</h2>
                <p>Redirecting to Signal Executive Assistant...</p>
                <script>
                    localStorage.setItem('signal_token', '{token}');
                    var defaultFrontend = '{target_frontend}';
                    var referrer = document.referrer;
                    var targetUrl = defaultFrontend;

                    if (referrer && (referrer.includes('vercel.app') || referrer.includes('localhost') || referrer.includes('5173') || referrer.includes('3000'))) {{
                        try {{
                            targetUrl = new URL(referrer).origin;
                        }} catch (e) {{}}
                    }}

                    window.location.href = targetUrl + '/?token={token}';
                </script>
                <p style="margin-top: 1rem; font-size: 0.85rem; color: #94a3b8;">
                    If you are not redirected automatically, <a href="{target_frontend}/?token={token}">Click here to open Signal Frontend</a>
                </p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {str(e)}",
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_me(user: UserProfile = Depends(get_current_user)):
    """Get currently authenticated user profile."""
    return UserProfileResponse.model_validate(user)

