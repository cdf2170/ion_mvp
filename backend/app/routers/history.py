from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from backend.app.db.session import get_db
from backend.app.db.models import (
    ConfigHistory, ActivityHistory, 
    ConfigChangeTypeEnum, ActivityTypeEnum
)
from backend.app.schemas import (
    ConfigHistorySchema,
    ConfigHistoryListResponse,
    ActivityHistorySchema,
    ActivityHistoryListResponse,
    ActivityCreateRequest
)
from backend.app.security.auth import verify_token

router = APIRouter(prefix="/history", tags=["history-audit"])


@router.get("/config", response_model=ConfigHistoryListResponse)
def get_config_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (user, device, policy, etc.)"),
    entity_id: Optional[UUID] = Query(None, description="Filter by specific entity ID"),
    change_type: Optional[ConfigChangeTypeEnum] = Query(None, description="Filter by change type"),
    changed_by: Optional[str] = Query(None, description="Filter by who made the change"),
    days_back: Optional[int] = Query(30, ge=1, le=365, description="Number of days back to search"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get configuration change history with filtering and pagination.
    
    **Frontend Integration Notes:**
    - Use this for audit trails and compliance reporting
    - Filter by entity_id to show changes for specific users/devices
    - Use days_back to limit scope for performance
    """
    # Build query
    query_filter = db.query(ConfigHistory)
    
    # Apply time filter
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    query_filter = query_filter.filter(ConfigHistory.changed_at >= cutoff_date)
    
    # Apply other filters
    if entity_type:
        query_filter = query_filter.filter(ConfigHistory.entity_type == entity_type)
    if entity_id:
        query_filter = query_filter.filter(ConfigHistory.entity_id == entity_id)
    if change_type:
        query_filter = query_filter.filter(ConfigHistory.change_type == change_type)
    if changed_by:
        query_filter = query_filter.filter(ConfigHistory.changed_by.ilike(f"%{changed_by}%"))
    
    # Order by most recent first
    query_filter = query_filter.order_by(desc(ConfigHistory.changed_at))
    
    # Get total count
    total = query_filter.count()
    
    # Apply pagination
    changes = query_filter.offset((page - 1) * page_size).limit(page_size).all()
    
    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size
    
    return ConfigHistoryListResponse(
        changes=changes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/activity", response_model=ActivityHistoryListResponse)
def get_activity_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    user_cid: Optional[UUID] = Query(None, description="Filter by user's canonical ID"),
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    activity_type: Optional[ActivityTypeEnum] = Query(None, description="Filter by activity type"),
    source_system: Optional[str] = Query(None, description="Filter by source system"),
    risk_score: Optional[str] = Query(None, description="Filter by risk score"),
    days_back: Optional[int] = Query(7, ge=1, le=90, description="Number of days back to search"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get user activity history with filtering and pagination.
    
    **Frontend Integration Notes:**
    - Use this for user behavior analysis and security monitoring
    - Filter by risk_score to focus on high-risk activities
    - Use shorter time windows for performance with large datasets
    """
    # Build query
    query_filter = db.query(ActivityHistory)
    
    # Apply time filter
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    query_filter = query_filter.filter(ActivityHistory.timestamp >= cutoff_date)
    
    # Apply other filters
    if user_cid:
        query_filter = query_filter.filter(ActivityHistory.user_cid == user_cid)
    if device_id:
        query_filter = query_filter.filter(ActivityHistory.device_id == device_id)
    if activity_type:
        query_filter = query_filter.filter(ActivityHistory.activity_type == activity_type)
    if source_system:
        query_filter = query_filter.filter(ActivityHistory.source_system.ilike(f"%{source_system}%"))
    if risk_score:
        query_filter = query_filter.filter(ActivityHistory.risk_score == risk_score)
    
    # Order by most recent first
    query_filter = query_filter.order_by(desc(ActivityHistory.timestamp))
    
    # Get total count
    total = query_filter.count()
    
    # Apply pagination
    activities = query_filter.offset((page - 1) * page_size).limit(page_size).all()
    
    # Convert IP addresses to strings for Pydantic serialization
    for activity in activities:
        if activity.source_ip:
            activity.source_ip = str(activity.source_ip)
    
    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size
    
    return ActivityHistoryListResponse(
        activities=activities,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/activity", response_model=ActivityHistorySchema)
def create_activity_record(
    request: ActivityCreateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Create a new activity history record.
    
    **Frontend Integration Notes:**
    - Use this to log custom activities from frontend actions
    - Include metadata as JSON for additional context
    """
    activity = ActivityHistory(
        user_cid=request.user_cid,
        device_id=request.device_id,
        activity_type=request.activity_type,
        source_system=request.source_system,
        source_ip=request.source_ip,
        user_agent=request.user_agent,
        description=request.description,
        activity_metadata=request.activity_metadata,
        risk_score=request.risk_score
    )
    
    db.add(activity)
    db.commit()
    db.refresh(activity)
    
    return activity


@router.get("/activity/summary/by-type")
def get_activity_summary_by_type(
    days_back: int = Query(7, ge=1, le=90, description="Number of days back to analyze"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get activity summary grouped by type for the specified time period.
    
    **Frontend Integration Notes:**
    - Use this for activity dashboard widgets
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    type_counts = (
        db.query(ActivityHistory.activity_type, func.count(ActivityHistory.id))
        .filter(ActivityHistory.timestamp >= cutoff_date)
        .group_by(ActivityHistory.activity_type)
        .all()
    )
    
    total_activities = (
        db.query(ActivityHistory)
        .filter(ActivityHistory.timestamp >= cutoff_date)
        .count()
    )
    
    return {
        "total_activities": total_activities,
        "period_days": days_back,
        "by_type": {activity_type.value: count for activity_type, count in type_counts}
    }


@router.get("/activity/summary/by-risk")
def get_activity_summary_by_risk(
    days_back: int = Query(7, ge=1, le=90, description="Number of days back to analyze"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get activity summary grouped by risk score for the specified time period.
    
    **Frontend Integration Notes:**
    - Use this for security dashboard widgets
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    risk_counts = (
        db.query(ActivityHistory.risk_score, func.count(ActivityHistory.id))
        .filter(
            and_(
                ActivityHistory.timestamp >= cutoff_date,
                ActivityHistory.risk_score.is_not(None)
            )
        )
        .group_by(ActivityHistory.risk_score)
        .all()
    )
    
    high_risk_activities = (
        db.query(ActivityHistory)
        .filter(
            and_(
                ActivityHistory.timestamp >= cutoff_date,
                or_(
                    ActivityHistory.risk_score == "High",
                    ActivityHistory.risk_score == "Critical"
                )
            )
        )
        .count()
    )
    
    return {
        "period_days": days_back,
        "by_risk": {risk_score: count for risk_score, count in risk_counts if risk_score},
        "high_risk_count": high_risk_activities
    }


@router.get("/config/summary/recent-changes")
def get_recent_config_changes(
    hours_back: int = Query(24, ge=1, le=168, description="Number of hours back to analyze"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get summary of recent configuration changes.
    
    **Frontend Integration Notes:**
    - Use this for change management dashboards
    """
    cutoff_date = datetime.utcnow() - timedelta(hours=hours_back)
    
    change_counts = (
        db.query(ConfigHistory.change_type, func.count(ConfigHistory.id))
        .filter(ConfigHistory.changed_at >= cutoff_date)
        .group_by(ConfigHistory.change_type)
        .all()
    )
    
    entity_counts = (
        db.query(ConfigHistory.entity_type, func.count(ConfigHistory.id))
        .filter(ConfigHistory.changed_at >= cutoff_date)
        .group_by(ConfigHistory.entity_type)
        .all()
    )
    
    total_changes = (
        db.query(ConfigHistory)
        .filter(ConfigHistory.changed_at >= cutoff_date)
        .count()
    )
    
    return {
        "period_hours": hours_back,
        "total_changes": total_changes,
        "by_change_type": {change_type.value: count for change_type, count in change_counts},
        "by_entity_type": {entity_type: count for entity_type, count in entity_counts}
    }


@router.get("/timeline")
def get_combined_timeline(
    entity_id: UUID = Query(..., description="Entity ID to get timeline for"),
    entity_type: str = Query(..., description="Entity type (user, device, etc.)"),
    days_back: int = Query(30, ge=1, le=90, description="Number of days back to include"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get combined timeline of configuration changes and activities for a specific entity.
    
    **Frontend Integration Notes:**
    - Use this to show complete history for a user or device
    - Combines config changes and activities in chronological order
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Get config changes for this entity
    config_changes = (
        db.query(ConfigHistory)
        .filter(
            and_(
                ConfigHistory.entity_id == entity_id,
                ConfigHistory.entity_type == entity_type,
                ConfigHistory.changed_at >= cutoff_date
            )
        )
        .all()
    )
    
    # Get activities for this entity (if it's a user or device)
    activities = []
    if entity_type == "user":
        activities = (
            db.query(ActivityHistory)
            .filter(
                and_(
                    ActivityHistory.user_cid == entity_id,
                    ActivityHistory.timestamp >= cutoff_date
                )
            )
            .all()
        )
    elif entity_type == "device":
        activities = (
            db.query(ActivityHistory)
            .filter(
                and_(
                    ActivityHistory.device_id == entity_id,
                    ActivityHistory.timestamp >= cutoff_date
                )
            )
            .all()
        )
    
    # Combine and sort chronologically
    timeline_events = []
    
    for change in config_changes:
        timeline_events.append({
            "type": "config_change",
            "timestamp": change.changed_at,
            "change_type": change.change_type.value,
            "field_name": change.field_name,
            "old_value": change.old_value,
            "new_value": change.new_value,
            "changed_by": change.changed_by,
            "description": change.description
        })
    
    for activity in activities:
        timeline_events.append({
            "type": "activity",
            "timestamp": activity.timestamp,
            "activity_type": activity.activity_type.value,
            "source_system": activity.source_system,
            "source_ip": activity.source_ip,
            "description": activity.description,
            "risk_score": activity.risk_score
        })
    
    # Sort by timestamp (most recent first)
    timeline_events.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "period_days": days_back,
        "total_events": len(timeline_events),
        "timeline": timeline_events
    }
