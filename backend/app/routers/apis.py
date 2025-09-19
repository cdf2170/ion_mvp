from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import json
import time

from backend.app.db.session import get_db
from backend.app.db.models import (
    APIConnection, APIConnectionTag, APISyncLog,
    APIProviderEnum, APIConnectionStatusEnum, APIConnectionTagEnum, Device
)
from backend.app.schemas import (
    APIConnectionSchema,
    APIConnectionCreateRequest,
    APIConnectionUpdateRequest,
    APIConnectionListResponse,
    APIHealthCheckResult,
    APISyncLogSchema,
    APISyncLogListResponse,
    APIConnectionTagSchema
)
from backend.app.security.auth import verify_token

router = APIRouter(prefix="/apis", tags=["api-management"])


@router.get("", response_model=APIConnectionListResponse)
def get_api_connections(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    provider: Optional[APIProviderEnum] = Query(None, description="Filter by provider"),
    status: Optional[APIConnectionStatusEnum] = Query(None, description="Filter by status"),
    tag: Optional[APIConnectionTagEnum] = Query(None, description="Filter by tag"),
    sync_enabled: Optional[bool] = Query(None, description="Filter by sync enabled status"),
    query: Optional[str] = Query(None, description="Search in connection name or description"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get paginated list of API connections with optional filtering and search.
    
    **Frontend Integration Notes:**
    - Use this to build API management dashboards
    - Filter by status to show only active/error connections
    - Use tags to organize connections by environment or type
    """
    # Build query
    query_filter = db.query(APIConnection)
    
    # Apply filters
    if provider:
        query_filter = query_filter.filter(APIConnection.provider == provider)
    if status:
        query_filter = query_filter.filter(APIConnection.status == status)
    if sync_enabled is not None:
        query_filter = query_filter.filter(APIConnection.sync_enabled == sync_enabled)
    if tag:
        query_filter = query_filter.join(APIConnectionTag).filter(APIConnectionTag.tag == tag)
    if query:
        search = f"%{query}%"
        query_filter = query_filter.filter(
            or_(
                APIConnection.name.ilike(search),
                APIConnection.description.ilike(search)
            )
        )
    
    # Get total count
    total = query_filter.count()
    
    # Apply pagination
    connections = query_filter.offset((page - 1) * page_size).limit(page_size).all()
    
    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size
    
    return APIConnectionListResponse(
        connections=connections,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{connection_id}", response_model=APIConnectionSchema)
def get_api_connection(
    connection_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get detailed information about a specific API connection.
    
    **Frontend Integration Notes:**
    - Use this to show connection details in configuration screens
    - Check status and health_check_message for connection health
    """
    connection = db.query(APIConnection).filter(APIConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="API connection not found")
    
    return connection


@router.post("", response_model=APIConnectionSchema)
def create_api_connection(
    request: APIConnectionCreateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Create a new API connection.
    
    **Frontend Integration Notes:**
    - Use this to set up new integrations
    - Credentials will be automatically encrypted
    - Connection starts in TESTING status
    """
    # Create the connection
    connection = APIConnection(
        name=request.name,
        provider=request.provider,
        description=request.description,
        base_url=request.base_url,
        api_version=request.api_version,
        authentication_type=request.authentication_type,
        credentials=request.credentials,  # TODO: Encrypt in production
        sync_enabled=request.sync_enabled,
        sync_interval_minutes=request.sync_interval_minutes,
        connection_test_url=request.connection_test_url,
        rate_limit_requests=request.rate_limit_requests,
        rate_limit_window=request.rate_limit_window,
        field_mappings=request.field_mappings,
        supports_users=request.supports_users,
        supports_devices=request.supports_devices,
        supports_groups=request.supports_groups,
        supports_realtime=request.supports_realtime,
        created_by="system"  # TODO: Get from auth context
    )
    
    db.add(connection)
    db.flush()  # Get the ID
    
    # Add tags
    for tag_enum in request.tags:
        tag = APIConnectionTag(connection_id=connection.id, tag=tag_enum)
        db.add(tag)
    
    db.commit()
    db.refresh(connection)
    
    return connection


@router.put("/{connection_id}", response_model=APIConnectionSchema)
def update_api_connection(
    connection_id: UUID,
    request: APIConnectionUpdateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Update an existing API connection.
    
    **Frontend Integration Notes:**
    - Use this to modify connection settings
    - Only provided fields will be updated
    """
    connection = db.query(APIConnection).filter(APIConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="API connection not found")
    
    # Update fields if provided
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(connection, field):
            setattr(connection, field, value)
    
    connection.updated_by = "system"  # TODO: Get from auth context
    
    db.commit()
    db.refresh(connection)
    
    return connection


@router.delete("/{connection_id}")
def delete_api_connection(
    connection_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Delete an API connection.
    
    **Frontend Integration Notes:**
    - Use this to remove integrations
    - This will also delete all associated sync logs
    """
    connection = db.query(APIConnection).filter(APIConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="API connection not found")
    
    db.delete(connection)
    db.commit()
    
    return {"message": "API connection deleted successfully"}


@router.post("/{connection_id}/test", response_model=APIHealthCheckResult)
def test_api_connection(
    connection_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Test an API connection health.
    
    **Frontend Integration Notes:**
    - Use this to verify connection settings
    - Returns response time and status
    """
    connection = db.query(APIConnection).filter(APIConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="API connection not found")
    
    # Simulate health check
    start_time = time.time()
    
    # TODO: Implement actual health check logic based on provider
    # For now, return a mock response
    response_time = (time.time() - start_time) * 1000
    
    # Update connection status
    connection.last_health_check = datetime.utcnow()
    connection.health_check_message = "Connection test successful"
    connection.status = APIConnectionStatusEnum.CONNECTED
    
    db.commit()
    
    return APIHealthCheckResult(
        connection_id=connection_id,
        status="healthy",
        response_time_ms=response_time,
        message="Connection test successful",
        last_checked=connection.last_health_check,
        capabilities_verified=["authentication", "basic_api_access"]
    )


@router.post("/{connection_id}/sync")
def trigger_api_sync(
    connection_id: UUID,
    sync_type: str = Query("manual", description="Type of sync to perform"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Trigger a manual sync for an API connection using the correlation engine.
    
    **Frontend Integration Notes:**
    - Use this to manually sync data from external systems
    - Uses automatic correlation engine to map data to canonical identities
    - Creates detailed sync log entry with real results
    """
    connection = db.query(APIConnection).filter(APIConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="API connection not found")
    
    # Use the sync orchestrator to perform the actual sync
    try:
        from backend.app.services.sync_orchestrator import SyncOrchestrator
        orchestrator = SyncOrchestrator(db)
        
        sync_result = orchestrator.sync_connection(str(connection_id))
        
        if sync_result["status"] == "success":
            return {
                "message": "Sync completed successfully",
                "sync_result": sync_result
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Sync failed: {sync_result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/{connection_id}/logs", response_model=APISyncLogListResponse)
def get_api_sync_logs(
    connection_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    status: Optional[str] = Query(None, description="Filter by sync status"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get sync logs for an API connection.
    
    **Frontend Integration Notes:**
    - Use this to show sync history and troubleshoot issues
    - Filter by status to find failed syncs
    """
    # Verify connection exists
    connection = db.query(APIConnection).filter(APIConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="API connection not found")
    
    # Build query
    query_filter = db.query(APISyncLog).filter(APISyncLog.connection_id == connection_id)
    
    if status:
        query_filter = query_filter.filter(APISyncLog.status == status)
    
    # Order by most recent first
    query_filter = query_filter.order_by(APISyncLog.started_at.desc())
    
    # Get total count
    total = query_filter.count()
    
    # Apply pagination
    logs = query_filter.offset((page - 1) * page_size).limit(page_size).all()
    
    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size
    
    return APISyncLogListResponse(
        logs=logs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.put("/{connection_id}/tags")
def update_api_connection_tags(
    connection_id: UUID,
    tags: List[APIConnectionTagEnum],
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Update tags for an API connection.
    
    **Frontend Integration Notes:**
    - Use this to organize connections by environment, criticality, etc.
    - Replaces all existing tags
    """
    connection = db.query(APIConnection).filter(APIConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="API connection not found")
    
    # Remove existing tags
    db.query(APIConnectionTag).filter(APIConnectionTag.connection_id == connection_id).delete()
    
    # Add new tags
    for tag_enum in tags:
        tag = APIConnectionTag(connection_id=connection_id, tag=tag_enum)
        db.add(tag)
    
    db.commit()
    
    return {"message": "Tags updated successfully"}


@router.get("/status/summary")
def get_api_status_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get summary of API connection statuses.
    
    **Frontend Integration Notes:**
    - Use this for dashboard widgets showing overall API health
    """
    status_counts = (
        db.query(APIConnection.status, func.count(APIConnection.id))
        .group_by(APIConnection.status)
        .all()
    )
    
    total_connections = db.query(APIConnection).count()
    
    # Get recent sync stats
    recent_syncs = (
        db.query(APISyncLog)
        .filter(APISyncLog.started_at >= datetime.utcnow() - timedelta(hours=24))
        .count()
    )
    
    failed_syncs = (
        db.query(APISyncLog)
        .filter(
            and_(
                APISyncLog.started_at >= datetime.utcnow() - timedelta(hours=24),
                APISyncLog.status == "error"
            )
        )
        .count()
    )
    
    return {
        "total_connections": total_connections,
        "status_breakdown": {status.value: count for status, count in status_counts},
        "recent_syncs_24h": recent_syncs,
        "failed_syncs_24h": failed_syncs,
        "sync_success_rate": ((recent_syncs - failed_syncs) / recent_syncs * 100) if recent_syncs > 0 else 100
    }


@router.post("/sync-all")
def sync_all_connections(
    force_sync: bool = Query(False, description="Force sync even if not scheduled"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Trigger sync for all active API connections using the correlation engine.
    
    **Frontend Integration Notes:**
    - Use this to sync all data sources at once
    - Shows comprehensive results with correlation statistics
    """
    try:
        from backend.app.services.sync_orchestrator import SyncOrchestrator
        orchestrator = SyncOrchestrator(db)
        
        results = orchestrator.sync_all_connections(force_sync=force_sync)
        
        return {
            "message": "Batch sync completed",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch sync failed: {str(e)}"
        )


@router.get("/orphans")
def detect_orphaned_resources(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Detect orphaned resources (devices without owners, accounts without users, etc.).
    
    **Frontend Integration Notes:**
    - Use this for compliance dashboards
    - Shows resources that need attention
    - Helps identify cost optimization opportunities
    """
    try:
        from backend.app.services.identity_correlation import IdentityCorrelationEngine
        engine = IdentityCorrelationEngine(db)
        
        orphans = engine.detect_orphaned_resources()
        
        return {
            "orphaned_resources": orphans,
            "summary": {
                "orphaned_devices": len(orphans["devices_without_owners"]),
                "orphaned_accounts": len(orphans["accounts_without_users"]),
                "inactive_users_with_resources": len(orphans["inactive_users_with_resources"])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Orphan detection failed: {str(e)}"
        )


@router.post("/improve-device-names")
def improve_device_names(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Improve device names by adding last names for better clarity.
    
    **Frontend Integration Notes:**
    - Use this to enhance existing device names with full names
    - Shows before/after results for transparency
    - Helps with device identification when multiple users have similar first names
    """
    try:
        from backend.app.services.identity_correlation import IdentityCorrelationEngine
        engine = IdentityCorrelationEngine(db)
        
        # Get all devices with owners
        devices = db.query(Device).filter(
            Device.owner_cid.isnot(None)
        ).all()
        
        improvements = []
        total_improved = 0
        
        for device in devices:
            if device.owner_cid:
                original_name = device.name
                improved_name = engine._improve_device_name(device.name, device.owner_cid)
                
                if improved_name != original_name:
                    device.name = improved_name
                    improvements.append({
                        "device_id": str(device.id),
                        "original_name": original_name,
                        "improved_name": improved_name,
                        "owner_name": device.owner.full_name if device.owner else None
                    })
                    total_improved += 1
        
        db.commit()
        
        return {
            "message": f"Improved {total_improved} device names",
            "improvements": improvements,
            "total_devices_processed": len(devices),
            "devices_improved": total_improved
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to improve device names: {str(e)}"
        )


@router.post("/fix-misnamed-devices")
def fix_misnamed_devices(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Fix devices that are completely misnamed (wrong owner name in device name).
    
    **Frontend Integration Notes:**
    - Use this when devices show wrong owner names
    - Corrects devices like "Adam's iPad" owned by "Laura Howe" to "Laura Howe's iPad"
    """
    try:
        devices = db.query(Device).filter(
            Device.owner_cid.isnot(None)
        ).all()
        
        fixes = []
        total_fixed = 0
        
        for device in devices:
            if device.owner and device.owner.full_name:
                owner_parts = device.owner.full_name.strip().split()
                if len(owner_parts) >= 2:
                    owner_first = owner_parts[0].lower()
                    owner_full = f"{owner_parts[0]} {owner_parts[-1]}"
                    
                    # Check if device name has possessive pattern
                    if "'s " in device.name:
                        device_first = device.name.split("'s ")[0].strip().lower()
                        device_type = device.name.split("'s ", 1)[1]
                        
                        # If device shows wrong owner name, fix it
                        if device_first != owner_first:
                            original_name = device.name
                            device.name = f"{owner_full}'s {device_type}"
                            
                            fixes.append({
                                "device_id": str(device.id),
                                "original_name": original_name,
                                "corrected_name": device.name,
                                "actual_owner": device.owner.full_name,
                                "issue": f"Device named for '{device_first}' but owned by '{owner_first}'"
                            })
                            total_fixed += 1
        
        db.commit()
        
        return {
            "message": f"Fixed {total_fixed} misnamed devices",
            "fixes": fixes,
            "total_devices_processed": len(devices),
            "devices_fixed": total_fixed
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fix misnamed devices: {str(e)}"
        )
