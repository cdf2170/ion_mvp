from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.config import settings
from typing import Dict, Any, Optional


security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify the Bearer token - supports both demo token and OAuth tokens.
    
    Args:
        credentials: HTTP authorization credentials containing the bearer token
        
    Returns:
        str: The verified token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # First, check if it's the demo token (backward compatibility)
    if token == settings.demo_api_token:
        return token
    
    # Try to verify as OAuth token
    try:
        from backend.app.security.oauth import oauth_service
        payload = oauth_service.verify_access_token(token)
        return token
    except HTTPException:
        # If OAuth token verification fails, try demo token one more time
        if token != settings.demo_api_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token


def verify_oauth_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """
    Verify OAuth token and return user information.
    
    Args:
        credentials: HTTP authorization credentials containing the bearer token
        
    Returns:
        Dict: User information from the OAuth token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # For demo token, return mock user info
    if token == settings.demo_api_token:
        return {
            "sub": "demo-user-id",
            "email": "demo@company.com",
            "name": "Demo User",
            "role": "Administrator",
            "department": "IT"
        }
    
    # Verify OAuth token and get user info
    try:
        from backend.app.security.oauth import oauth_service
        payload = oauth_service.verify_access_token(token)
        return payload
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
