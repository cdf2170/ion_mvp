from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import List

from backend.app.db.session import get_db
from backend.app.db.models import (
    Device, CanonicalIdentity, DeviceTag, DeviceStatusEnum, 
    GroupMembership, Policy, ActivityHistory, APIConnection,
    ConfigHistory, ConfigChangeTypeEnum
)
from backend.app.schemas import DashboardSummaryResponse, DashboardSummaryCard
from backend.app.security.auth import verify_token

# Try to import cache, fallback if not available
try:
    from backend.app.cache import app_cache
except ImportError:
    # Fallback cache implementation
    class SimpleCache:
        def get(self, key): return None
        def set(self, key, value, ttl_seconds=300): pass
        def clear(self): pass
        def size(self): return 0
    app_cache = SimpleCache()


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get comprehensive dashboard summary with key metrics.
    
    **Frontend Integration Notes:**
    - Provides summary cards for main dashboard
    - Cached for 5 minutes for performance
    - Includes device counts, compliance, users, and system health
    - Perfect for dashboard overview widgets
    
    Returns:
        Dashboard summary with cards for key metrics
    """
    
    cache_key = "dashboard_summary"
    cached_result = app_cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        cards = []
        
        # Card 1: Total Devices
        total_devices = db.query(Device).count()
        connected_devices = db.query(Device).filter(
            Device.status == DeviceStatusEnum.CONNECTED
        ).count()
        device_connection_rate = (connected_devices / total_devices * 100) if total_devices > 0 else 0
        
        cards.append(DashboardSummaryCard(
            title="Total Devices",
            value=total_devices,
            subtitle=f"{connected_devices} connected ({device_connection_rate:.1f}%)",
            trend="neutral",
            change_percent=None
        ))
        
        # Card 2: Compliance Status
        compliant_devices = db.query(Device).filter(Device.compliant == True).count()
        compliance_rate = (compliant_devices / total_devices * 100) if total_devices > 0 else 0
        compliance_trend = "up" if compliance_rate >= 80 else "down" if compliance_rate < 60 else "neutral"
        
        cards.append(DashboardSummaryCard(
            title="Compliance Rate", 
            value=int(compliance_rate),
            subtitle=f"{compliant_devices}/{total_devices} devices compliant",
            trend=compliance_trend,
            change_percent=None
        ))
        
        # Card 3: Total Users
        total_users = db.query(CanonicalIdentity).count()
        # Get active users (users with devices)
        active_users = db.query(CanonicalIdentity).join(Device).distinct().count()
        
        cards.append(DashboardSummaryCard(
            title="Total Users",
            value=total_users,
            subtitle=f"{active_users} with devices",
            trend="neutral",
            change_percent=None
        ))
        
        # Card 4: Recent Activity
        # Count activity in last 24 hours
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_activity = db.query(ActivityHistory).filter(
            ActivityHistory.timestamp >= yesterday
        ).count()
        
        cards.append(DashboardSummaryCard(
            title="Recent Activity",
            value=recent_activity,
            subtitle="Events last 24h",
            trend="neutral",
            change_percent=None
        ))
        
        # Card 5: System Health
        # Simple health check based on various factors
        disconnected_devices = total_devices - connected_devices
        non_compliant_devices = total_devices - compliant_devices
        
        health_score = 100
        if disconnected_devices > total_devices * 0.3:  # >30% disconnected
            health_score -= 30
        if non_compliant_devices > total_devices * 0.2:  # >20% non-compliant
            health_score -= 20
        
        health_status = "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical"
        health_trend = "up" if health_score >= 80 else "down"
        
        cards.append(DashboardSummaryCard(
            title="System Health",
            value=health_score,
            subtitle=f"Status: {health_status}",
            trend=health_trend,
            change_percent=None
        ))
        
        # Card 6: Groups & Policies
        total_groups = db.query(GroupMembership.group_name).distinct().count()
        total_policies = db.query(Policy).count()
        
        cards.append(DashboardSummaryCard(
            title="Groups & Policies",
            value=total_groups,
            subtitle=f"{total_policies} policies configured",
            trend="neutral",
            change_percent=None
        ))
        
        result = DashboardSummaryResponse(
            cards=cards,
            last_updated=datetime.utcnow(),
            system_health=health_status
        )
        
        # Cache for 5 minutes
        app_cache.set(cache_key, result, ttl_seconds=300)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard summary: {str(e)}"
        )


@router.get("/quick-stats")
def get_quick_stats(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get quick statistics for dashboard header.
    
    **Frontend Integration Notes:**
    - Lightweight endpoint for header statistics
    - Faster than full summary, good for frequent updates
    - Returns just the most essential numbers
    
    Returns:
        Quick stats: devices, users, compliance, health
    """
    
    cache_key = "dashboard_quick_stats"
    cached_result = app_cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        total_devices = db.query(Device).count()
        connected_devices = db.query(Device).filter(
            Device.status == DeviceStatusEnum.CONNECTED
        ).count()
        compliant_devices = db.query(Device).filter(Device.compliant == True).count()
        total_users = db.query(CanonicalIdentity).count()
        
        compliance_rate = (compliant_devices / total_devices * 100) if total_devices > 0 else 0
        connection_rate = (connected_devices / total_devices * 100) if total_devices > 0 else 0
        
        result = {
            "devices": {
                "total": total_devices,
                "connected": connected_devices,
                "connection_rate": round(connection_rate, 1)
            },
            "compliance": {
                "compliant": compliant_devices,
                "rate": round(compliance_rate, 1)
            },
            "users": {
                "total": total_users
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Cache for 2 minutes (shorter than full summary)
        app_cache.set(cache_key, result, ttl_seconds=120)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quick stats: {str(e)}"
        )


@router.get("/config-changes")
def get_config_changes_summary(
    hours_back: int = Query(24, ge=1, le=168, description="Hours back to analyze"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get recent configuration changes summary for dashboard.
    
    **Frontend Integration Notes:**
    - Shows recent configuration activity for dashboard widgets
    - Includes change counts by type and entity
    - Perfect for audit overview components
    
    Returns:
        Configuration changes summary with recent activity breakdown
    """
    
    cache_key = f"config_changes_summary_{hours_back}h"
    cached_result = app_cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        # Time window
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Total changes in time window
        total_changes = db.query(ConfigHistory).filter(
            ConfigHistory.changed_at >= cutoff_time
        ).count()
        
        # Changes by type
        changes_by_type = db.query(
            ConfigHistory.change_type,
            func.count(ConfigHistory.id).label('count')
        ).filter(
            ConfigHistory.changed_at >= cutoff_time
        ).group_by(ConfigHistory.change_type).all()
        
        # Changes by entity type
        changes_by_entity = db.query(
            ConfigHistory.entity_type,
            func.count(ConfigHistory.id).label('count')
        ).filter(
            ConfigHistory.changed_at >= cutoff_time
        ).group_by(ConfigHistory.entity_type).order_by(
            func.count(ConfigHistory.id).desc()
        ).all()
        
        # Recent changes (last 10)
        recent_changes = db.query(ConfigHistory).filter(
            ConfigHistory.changed_at >= cutoff_time
        ).order_by(ConfigHistory.changed_at.desc()).limit(10).all()
        
        # Most active entities
        active_entities = db.query(
            ConfigHistory.entity_type,
            ConfigHistory.entity_id,
            func.count(ConfigHistory.id).label('change_count')
        ).filter(
            ConfigHistory.changed_at >= cutoff_time
        ).group_by(
            ConfigHistory.entity_type,
            ConfigHistory.entity_id
        ).order_by(func.count(ConfigHistory.id).desc()).limit(5).all()
        
        result = {
            "overview": {
                "total_changes": total_changes,
                "time_window_hours": hours_back,
                "changes_per_hour": round(total_changes / hours_back, 1) if hours_back > 0 else 0
            },
            "changes_by_type": [
                {"type": change_type.value, "count": count}
                for change_type, count in changes_by_type
            ],
            "changes_by_entity": [
                {"entity_type": entity_type, "count": count}
                for entity_type, count in changes_by_entity
            ],
            "recent_changes": [
                {
                    "id": str(change.id),
                    "entity_type": change.entity_type,
                    "entity_id": str(change.entity_id),
                    "change_type": change.change_type.value,
                    "field_name": change.field_name,
                    "changed_by": change.changed_by,
                    "changed_at": change.changed_at.isoformat()
                }
                for change in recent_changes
            ],
            "most_active_entities": [
                {
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "change_count": change_count
                }
                for entity_type, entity_id, change_count in active_entities
            ]
        }
        
        # Cache for 10 minutes
        app_cache.set(cache_key, result, ttl_seconds=600)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate config changes summary: {str(e)}"
        )
