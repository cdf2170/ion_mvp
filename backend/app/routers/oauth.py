"""
OAuth 2.0 / OpenID Connect endpoints for mock authentication
Provides realistic OAuth flow for frontend integration
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import urllib.parse
from backend.app.db.session import get_db
from backend.app.db.models import CanonicalIdentity
from backend.app.security.oauth import oauth_service, OAUTH_CONFIG

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.get("/.well-known/openid-configuration")
def openid_configuration():
    """OpenID Connect Discovery endpoint"""
    base_url = "https://api.privion.tech"  # In production, get from request
    return {
        **OAUTH_CONFIG,
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "userinfo_endpoint": f"{base_url}/oauth/userinfo",
        "jwks_uri": f"{base_url}/oauth/jwks",
    }


@router.get("/authorize")
def authorize(
    response_type: str = Query(..., description="Must be 'code'"),
    client_id: str = Query(..., description="Client ID"),
    redirect_uri: str = Query(..., description="Redirect URI"),
    scope: str = Query("openid email profile", description="OAuth scopes"),
    state: Optional[str] = Query(None, description="State parameter"),
    nonce: Optional[str] = Query(None, description="Nonce for ID token"),
):
    """
    OAuth 2.0 Authorization endpoint
    
    In a real OAuth flow, this would redirect to a login page.
    For our mock implementation, we'll return a simple HTML page.
    """
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported response_type. Only 'code' is supported."
        )
    
    # For demo purposes, return a simple login page
    # In production, this would redirect to your identity provider
    login_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mock OAuth Login</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }}
            .login-form {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
            input, select, button {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }}
            button {{ background: #007bff; color: white; border: none; cursor: pointer; }}
            button:hover {{ background: #0056b3; }}
            .info {{ background: #e7f3ff; padding: 10px; border-radius: 4px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="login-form">
            <h2>🔐 Mock OAuth Login</h2>
            <div class="info">
                <strong>Demo OAuth Flow</strong><br>
                Client: {client_id}<br>
                Scopes: {scope}
            </div>
            
            <form action="/oauth/callback" method="post">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="scope" value="{scope}">
                <input type="hidden" name="state" value="{state or ''}">
                
                <label>Select User (Mock Login):</label>
                <select name="user_email" required>
                    <option value="">-- Select a user --</option>
                    <option value="admin@company.com">Admin User</option>
                    <option value="elizabeth37@example.com">Elizabeth (Sample User)</option>
                    <option value="john.doe@company.com">John Doe</option>
                    <option value="jane.smith@company.com">Jane Smith</option>
                </select>
                
                <button type="submit">Authorize & Continue</button>
            </form>
            
            <div class="info">
                <small>
                    This is a mock OAuth implementation for demo purposes.<br>
                    In production, this would be your real identity provider (Auth0, Google, etc.)
                </small>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=login_html)


@router.post("/callback")
def oauth_callback(
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form(...),
    state: Optional[str] = Form(None),
    user_email: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle the mock login and generate authorization code"""
    
    # Verify user exists
    user = db.query(CanonicalIdentity).filter(
        CanonicalIdentity.email == user_email
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {user_email} not found. Please select a valid user."
        )
    
    # Create authorization code
    auth_code = oauth_service.create_authorization_code(
        user_email=user_email,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope
    )
    
    # Redirect back to client with authorization code
    params = {
        "code": auth_code,
        "state": state
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    redirect_url = f"{redirect_uri}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=redirect_url, status_code=302)


@router.post("/token")
def token_endpoint(
    grant_type: str = Form(...),
    code: str = Form(...),
    redirect_uri: str = Form(...),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    OAuth 2.0 Token endpoint
    Exchange authorization code for access token
    """
    if grant_type != "authorization_code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant_type. Only 'authorization_code' is supported."
        )
    
    # Exchange code for token
    token_response = oauth_service.exchange_code_for_token(
        code=code,
        client_id=client_id,
        redirect_uri=redirect_uri,
        db=db
    )
    
    return token_response


@router.get("/userinfo")
def userinfo_endpoint(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    OAuth 2.0 UserInfo endpoint
    Get user information using access token
    """
    # Extract access token from Authorization header
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = authorization.split(" ")[1]
    
    # Get user info
    user_info = oauth_service.get_user_info(access_token, db)
    return user_info


@router.get("/jwks")
def jwks_endpoint():
    """
    JSON Web Key Set endpoint
    For token verification (simplified for demo)
    """
    return {
        "keys": [
            {
                "kty": "oct",
                "use": "sig",
                "kid": "mock-key-1",
                "alg": "HS256",
                "k": "mock-jwk-key-for-demo-purposes-only"
            }
        ]
    }


@router.get("/logout")
def logout_endpoint(
    id_token_hint: Optional[str] = Query(None),
    post_logout_redirect_uri: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
):
    """
    OAuth 2.0 Logout endpoint
    """
    # In a real implementation, you'd invalidate tokens here
    
    if post_logout_redirect_uri:
        params = {"state": state} if state else {}
        redirect_url = f"{post_logout_redirect_uri}?{urllib.parse.urlencode(params)}"
        return RedirectResponse(url=redirect_url)
    
    return {"message": "Logged out successfully"}


# Additional helper endpoint for testing
@router.get("/test-users")
def get_test_users(db: Session = Depends(get_db)):
    """Get list of available test users for OAuth demo"""
    users = db.query(CanonicalIdentity).limit(10).all()
    return {
        "available_users": [
            {
                "email": user.email,
                "name": user.full_name,
                "role": user.role,
                "department": user.department
            }
            for user in users
        ],
        "note": "These users can be used in the OAuth login flow"
    }
