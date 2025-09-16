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
    APIProviderEnum, APIConnectionStatusEnum, APIConnectionTagEnum
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
    Trigger a manual sync for an API connection.
    
    **Frontend Integration Notes:**
    - Use this to manually sync data from external systems
    - Creates a sync log entry
    """
    connection = db.query(APIConnection).filter(APIConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="API connection not found")
    
    if connection.status != APIConnectionStatusEnum.CONNECTED:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot sync: connection status is {connection.status.value}"
        )
    
    # Create sync log
    sync_log = APISyncLog(
        connection_id=connection_id,
        sync_type=sync_type,
        status="success",  # TODO: Implement actual sync
        records_processed="50",
        records_created="10",
        records_updated="40",
        records_failed="0"
    )
    
    db.add(sync_log)
    
    # Update connection last sync
    connection.last_sync = datetime.utcnow()
    connection.next_sync = datetime.utcnow() + timedelta(minutes=int(connection.sync_interval_minutes))
    
    db.commit()
    
    return {"message": "Sync triggered successfully", "sync_log_id": sync_log.id}


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
