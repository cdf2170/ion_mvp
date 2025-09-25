"""
Microsoft E5 Tenant Integration Router
Secure endpoints for managing Microsoft Graph API connections.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel
import logging
import requests
import asyncio

from backend.app.db.session import get_db
from backend.app.db.models import APIConnection, APIProviderEnum, APIConnectionStatusEnum
from backend.app.security.auth import verify_token
from backend.app.services.connectors.microsoft_connector import MicrosoftGraphConnector
from backend.app.services.connectors.encryption import encrypt_credentials, decrypt_credentials
from backend.app.schemas import APIConnectionCreateRequest, APIConnectionSchema
from backend.app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/microsoft", tags=["Microsoft E5 Integration"])


async def test_microsoft_connection(credentials: Dict[str, str]) -> Dict[str, Any]:
    """Test Microsoft Graph API connection with provided credentials."""
    try:
        # Test OAuth2 token acquisition
        token_url = f"https://login.microsoftonline.com/{credentials['tenant_id']}/oauth2/v2.0/token"
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': credentials['client_id'],
            'client_secret': credentials['client_secret'],
            'scope': 'https://graph.microsoft.com/.default'
        }

        response = requests.post(token_url, data=token_data, timeout=30)
        response.raise_for_status()

        token_info = response.json()
        access_token = token_info['access_token']

        # Test basic Graph API call
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Try to get organization info (might fail if no admin consent)
        try:
            org_response = requests.get(
                "https://graph.microsoft.com/v1.0/organization",
                headers=headers,
                timeout=30
            )

            if org_response.status_code == 200:
                org_data = org_response.json()
                org_info = org_data.get('value', [{}])[0]
                tenant_info = {
                    'display_name': org_info.get('displayName', 'Unknown Organization'),
                    'tenant_id': credentials['tenant_id']
                }
            else:
                # Fallback if organization endpoint fails
                tenant_info = {
                    'display_name': 'Microsoft 365 Tenant',
                    'tenant_id': credentials['tenant_id']
                }
        except:
            tenant_info = {
                'display_name': 'Microsoft 365 Tenant',
                'tenant_id': credentials['tenant_id']
            }

        return {
            "status": "success",
            "message": "Microsoft Graph API connection successful",
            "tenant_info": tenant_info
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Connection failed: {str(e)}",
            "tenant_info": {}
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "tenant_info": {}
        }


class MicrosoftSetupRequest(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str

@router.post("/setup", response_model=Dict[str, Any])
async def setup_microsoft_tenant(
    request: MicrosoftSetupRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Set up Microsoft E5 tenant connection with secure credential storage.
    
    **Security Features:**
    - Credentials are encrypted before database storage
    - Connection is tested before saving
    - Audit trail is maintained
    
    **Required Permissions in Azure AD:**
    - User.Read.All
    - Group.Read.All
    - Device.Read.All
    - Directory.Read.All
    - AuditLog.Read.All (optional)
    
    Args:
        tenant_id: Azure AD tenant ID (GUID)
        client_id: Application (client) ID from Azure AD
        client_secret: Client secret from Azure AD
    
    Returns:
        Connection status and configuration details
    """
    try:
        # Validate inputs
        if not all([request.tenant_id, request.client_id, request.client_secret]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tenant_id, client_id, and client_secret are required"
            )

        # Prepare credentials for encryption
        credentials = {
            "tenant_id": request.tenant_id,
            "client_id": request.client_id,
            "client_secret": request.client_secret
        }
        
        # Test connection before saving by making direct API calls
        test_result = await test_microsoft_connection(credentials)
        
        if test_result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection test failed: {test_result['message']}"
            )
        
        # Encrypt credentials for secure storage
        encrypted_credentials = encrypt_credentials(credentials)
        
        # Check if connection already exists
        existing_connection = db.query(APIConnection).filter(
            APIConnection.provider == APIProviderEnum.MICROSOFT_365
        ).first()
        
        if existing_connection:
            # Update existing connection
            existing_connection.credentials = encrypted_credentials
            existing_connection.status = APIConnectionStatusEnum.CONNECTED
            existing_connection.health_check_message = "Connection updated successfully"
            connection = existing_connection
        else:
            # Create new connection
            connection = APIConnection(
                name=f"Microsoft E5 Tenant ({request.tenant_id[:8]}...)",
                provider=APIProviderEnum.MICROSOFT_365,
                description=f"Microsoft 365 E5 tenant integration for {test_result.get('tenant_info', {}).get('display_name', 'Unknown')}",
                base_url="https://graph.microsoft.com/v1.0",
                api_version="v1.0",
                authentication_type="oauth2_client_credentials",
                credentials=encrypted_credentials,
                sync_enabled=True,
                sync_interval_minutes=60,
                status=APIConnectionStatusEnum.CONNECTED,
                health_check_message="Connection established successfully",
                created_by="API Setup",
                supports_users=True,
                supports_devices=True,
                supports_groups=True,
                supports_realtime=False
            )
            db.add(connection)
        
        db.commit()
        db.refresh(connection)
        
        logger.info(f"Microsoft E5 tenant connection established: {request.tenant_id}")
        
        return {
            "status": "success",
            "message": "Microsoft E5 tenant connected successfully",
            "connection_id": str(connection.id),
            "tenant_info": test_result["tenant_info"],
            "capabilities": {
                "users": True,
                "groups": True,
                "devices": True,
                "audit_logs": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to setup Microsoft tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Setup failed: {str(e)}"
        )


@router.get("/status", response_model=Dict[str, Any])
async def get_microsoft_status(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """Get Microsoft E5 tenant connection status."""
    try:
        connection = db.query(APIConnection).filter(
            APIConnection.provider == APIProviderEnum.MICROSOFT_365
        ).first()
        
        if not connection:
            return {
                "status": "not_configured",
                "message": "Microsoft E5 tenant not configured"
            }
        
        # Test current connection
        try:
            decrypted_creds = decrypt_credentials(connection.credentials)
            test_result = await test_microsoft_connection(decrypted_creds)
            
            return {
                "status": "connected" if test_result["status"] == "success" else "error",
                "connection_id": str(connection.id),
                "tenant_info": test_result.get("tenant_info", {}),
                "last_sync": connection.last_sync,
                "sync_enabled": connection.sync_enabled,
                "message": test_result["message"]
            }
            
        except Exception as e:
            logger.error(f"Microsoft connection test failed: {e}")
            return {
                "status": "error",
                "connection_id": str(connection.id),
                "message": f"Connection test failed: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get Microsoft status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )


@router.post("/sync", response_model=Dict[str, Any])
def sync_microsoft_data(
    sync_type: str = "incremental",
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Trigger manual sync of Microsoft E5 tenant data.
    
    Args:
        sync_type: Type of sync (incremental, full, users_only, devices_only, groups_only)
    
    Returns:
        Sync results and statistics
    """
    try:
        connection = db.query(APIConnection).filter(
            APIConnection.provider == APIProviderEnum.MICROSOFT_365
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Microsoft E5 tenant not configured"
            )
        
        # Decrypt credentials
        decrypted_creds = decrypt_credentials(connection.credentials)
        
        # Create connector
        connector_config = {
            "base_url": connection.base_url,
            "credentials": decrypted_creds
        }
        
        connector = MicrosoftGraphConnector(connector_config)
        
        # Perform sync based on type
        sync_results = {
            "sync_type": sync_type,
            "started_at": connector._get_current_time(),
            "users_processed": 0,
            "groups_processed": 0,
            "devices_processed": 0,
            "errors": []
        }
        
        try:
            if sync_type in ["full", "incremental", "users_only"]:
                users = connector.get_users()
                sync_results["users_processed"] = len(users)
                logger.info(f"Synced {len(users)} users from Microsoft Graph")
            
            if sync_type in ["full", "incremental", "groups_only"]:
                groups = connector.get_groups()
                sync_results["groups_processed"] = len(groups)
                logger.info(f"Synced {len(groups)} groups from Microsoft Graph")
            
            if sync_type in ["full", "incremental", "devices_only"]:
                devices = connector.get_devices()
                sync_results["devices_processed"] = len(devices)
                logger.info(f"Synced {len(devices)} devices from Microsoft Graph")
            
            sync_results["status"] = "success"
            sync_results["completed_at"] = connector._get_current_time()
            
        except Exception as sync_error:
            sync_results["status"] = "partial_failure"
            sync_results["errors"].append(str(sync_error))
            logger.error(f"Microsoft sync error: {sync_error}")
        
        return sync_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Microsoft sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.delete("/disconnect", response_model=Dict[str, Any])
def disconnect_microsoft_tenant(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """Disconnect Microsoft E5 tenant (removes credentials but keeps historical data)."""
    try:
        connection = db.query(APIConnection).filter(
            APIConnection.provider == APIProviderEnum.MICROSOFT_365
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Microsoft E5 tenant not configured"
            )
        
        # Update connection status (don't delete to preserve audit trail)
        connection.status = APIConnectionStatusEnum.DISCONNECTED
        connection.credentials = ""  # Clear credentials
        connection.health_check_message = "Manually disconnected"
        connection.sync_enabled = False
        
        db.commit()
        
        logger.info("Microsoft E5 tenant disconnected")
        
        return {
            "status": "success",
            "message": "Microsoft E5 tenant disconnected successfully",
            "note": "Historical data preserved for audit purposes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect Microsoft tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Disconnect failed: {str(e)}"
        )
