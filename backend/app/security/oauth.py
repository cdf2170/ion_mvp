"""
Mock OAuth 2.0 implementation for MVP demonstration
Provides realistic OAuth flow using existing user data
"""
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.db.models import CanonicalIdentity
from backend.app.config import settings
import json


# OAuth Configuration
OAUTH_CONFIG = {
    "issuer": "https://api.privion.tech",
    "authorization_endpoint": "/oauth/authorize", 
    "token_endpoint": "/oauth/token",
    "userinfo_endpoint": "/oauth/userinfo",
    "jwks_uri": "/oauth/jwks",
    "scopes_supported": ["openid", "email", "profile"],
    "response_types_supported": ["code"],
    "grant_types_supported": ["authorization_code"],
}

# Mock JWT secret (in production, use a proper secret)
JWT_SECRET = getattr(settings, 'jwt_secret', 'mock-oauth-secret-key-for-demo-only')
JWT_ALGORITHM = "HS256"


class MockOAuthService:
    """Mock OAuth service that creates realistic OAuth flow"""
    
    def __init__(self):
        self.authorization_codes: Dict[str, Dict] = {}  # In production, use Redis
        self.access_tokens: Dict[str, Dict] = {}        # In production, use Redis
    
    def create_authorization_code(self, user_email: str, client_id: str, redirect_uri: str, scope: str) -> str:
        """Create a temporary authorization code"""
        code = f"auth_code_{uuid.uuid4().hex[:16]}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        self.authorization_codes[code] = {
            "user_email": user_email,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "expires_at": expires_at,
            "used": False
        }
        
        return code
    
    def exchange_code_for_token(self, code: str, client_id: str, redirect_uri: str, db: Session) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        # Validate authorization code
        if code not in self.authorization_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization code"
            )
        
        auth_data = self.authorization_codes[code]
        
        # Check if code is expired or used
        if auth_data["used"] or datetime.now(timezone.utc) > auth_data["expires_at"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code expired or already used"
            )
        
        # Validate client and redirect URI
        if auth_data["client_id"] != client_id or auth_data["redirect_uri"] != redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client_id or redirect_uri"
            )
        
        # Mark code as used
        auth_data["used"] = True
        
        # Get user data
        user = db.query(CanonicalIdentity).filter(
            CanonicalIdentity.email == auth_data["user_email"]
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Create access token
        access_token = self.create_access_token(user)
        id_token = self.create_id_token(user, client_id)
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": auth_data["scope"],
            "id_token": id_token
        }
    
    def create_access_token(self, user: CanonicalIdentity) -> str:
        """Create JWT access token"""
        now = datetime.now(timezone.utc)
        payload = {
            "iss": OAUTH_CONFIG["issuer"],
            "sub": str(user.cid),
            "aud": "api.privion.tech",
            "exp": now + timedelta(hours=1),
            "iat": now,
            "email": user.email,
            "name": user.full_name,
            "role": user.role,
            "department": user.department,
            "scope": "openid email profile"
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Store token info
        self.access_tokens[token] = {
            "user_id": str(user.cid),
            "email": user.email,
            "expires_at": now + timedelta(hours=1)
        }
        
        return token
    
    def create_id_token(self, user: CanonicalIdentity, client_id: str) -> str:
        """Create JWT ID token (OpenID Connect)"""
        now = datetime.now(timezone.utc)
        payload = {
            "iss": OAUTH_CONFIG["issuer"],
            "sub": str(user.cid),
            "aud": client_id,
            "exp": now + timedelta(hours=1),
            "iat": now,
            "email": user.email,
            "email_verified": True,
            "name": user.full_name,
            "given_name": user.full_name.split()[0] if user.full_name else "",
            "family_name": " ".join(user.full_name.split()[1:]) if len(user.full_name.split()) > 1 else "",
            "role": user.role,
            "department": user.department,
        }
        
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode access token"""
        try:
            # Decode without audience validation for simplicity in demo
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_aud": False})
            
            # Check if token is in our store and not expired
            if token in self.access_tokens:
                token_info = self.access_tokens[token]
                if datetime.now(timezone.utc) > token_info["expires_at"]:
                    del self.access_tokens[token]
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token expired"
                    )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def get_user_info(self, token: str, db: Session) -> Dict[str, Any]:
        """Get user info from access token"""
        payload = self.verify_access_token(token)
        user_id = payload.get("sub")
        
        user = db.query(CanonicalIdentity).filter(
            CanonicalIdentity.cid == user_id
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "sub": str(user.cid),
            "email": user.email,
            "email_verified": True,
            "name": user.full_name,
            "given_name": user.full_name.split()[0] if user.full_name else "",
            "family_name": " ".join(user.full_name.split()[1:]) if len(user.full_name.split()) > 1 else "",
            "role": user.role,
            "department": user.department,
            "location": user.location,
            "manager": user.manager,
            "status": user.status.value,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None
        }


# Global OAuth service instance
oauth_service = MockOAuthService()
