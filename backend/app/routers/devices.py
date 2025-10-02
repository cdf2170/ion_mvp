from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from fastapi import Query as FastAPIQuery
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, asc, desc, and_, String
from typing import Optional, List
from uuid import UUID
from enum import Enum
import random

from backend.app.db.session import get_db
from backend.app.db.models import Device, CanonicalIdentity, DeviceTag, DeviceStatusEnum, DeviceTagEnum, GroupMembership, Policy, ActivityHistory, ConfigHistory, ConfigChangeTypeEnum
from backend.app.schemas import (
    DeviceSchema, 
    DeviceListResponse, 
    DeviceUpdateRequest,
    DeviceCreateRequest,
    DeviceTagRequest,
    DeviceRenameRequest,
    DeviceVLANRequest,
    DeviceMergeRequest,
    DeviceMergeResponse
)
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


router = APIRouter(prefix="/devices", tags=["devices"])


def log_config_change(
    db: Session,
    entity_type: str,
    entity_id: UUID,
    change_type: ConfigChangeTypeEnum,
    field_name: str,
    old_value: str,
    new_value: str,
    changed_by: str = "API User"
):
    """
    Log a configuration change to the audit trail.
    
    Args:
        db: Database session
        entity_type: Type of entity (device, policy, user)
        entity_id: ID of the entity being changed
        change_type: Type of change (CREATED, UPDATED, DELETED)
        field_name: Name of the field being changed
        old_value: Previous value
        new_value: New value
        changed_by: Who made the change
    """
    try:
        config_entry = ConfigHistory(
            entity_type=entity_type,
            entity_id=entity_id,
            change_type=change_type,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            changed_by=changed_by
        )
        db.add(config_entry)
        # Note: Don't commit here - let the calling function handle the transaction
    except Exception as e:
        # Log the error but don't fail the main operation
        print(f"Warning: Failed to log config change: {str(e)}")


class DeviceSortBy(str, Enum):
    """Available columns for sorting devices"""
    name = "name"
    last_seen = "last_seen"
    compliant = "compliant"
    ip_address = "ip_address"
    mac_address = "mac_address"
    vlan = "vlan"
    os_version = "os_version"
    last_check_in = "last_check_in"
    status = "status"
    owner_email = "owner_email"
    owner_name = "owner_name"
    owner_department = "owner_department"


class SortDirection(str, Enum):
    """Sort direction"""
    asc = "asc"
    desc = "desc"


@router.get("", response_model=DeviceListResponse)
def get_devices(
    page: int = FastAPIQuery(1, ge=1, description="Page number"),
    page_size: int = FastAPIQuery(20, ge=1, le=100, description="Number of items per page"),
    sort_by: DeviceSortBy = FastAPIQuery(DeviceSortBy.name, description="Column to sort by"),
    sort_direction: SortDirection = FastAPIQuery(SortDirection.asc, description="Sort direction (asc/desc)"),
    compliant: Optional[bool] = FastAPIQuery(None, description="Filter by compliance status"),
    owner_cid: Optional[UUID] = FastAPIQuery(None, description="Filter by owner's canonical identity"),
    status: Optional[DeviceStatusEnum] = FastAPIQuery(None, description="Filter by connection status"),
    vlan: Optional[str] = FastAPIQuery(None, description="Filter by VLAN"),
    tags: Optional[str] = FastAPIQuery(None, description="Filter by tags (comma-separated for multiple tags, e.g. 'Remote,On-Site' or 'Corporate,VIP')"),
    query: Optional[str] = FastAPIQuery(None, description="Search in device name, IP, MAC address, owner info, tags, or group"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get paginated list of devices with optional filtering, search, and sorting.
    
    **Frontend Integration Notes:**
    - Use this to build device dashboards and compliance reports
    - Supports filtering by compliance status, connection status, owner, and multiple tags
    - Enhanced search works on device names, IP addresses, MAC addresses, owner info, tags, and groups
    - Multiple tags filtering: use comma-separated values (e.g., "Remote,VIP" or "On-Site,Corporate") - shows devices that have ANY of the specified tags
    - Supports sorting by any column with direction control
    - Returns pagination info for infinite scroll or page navigation
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page (1-100)
        sort_by: Column to sort by (name, last_seen, compliant, etc.)
        sort_direction: Sort direction (asc/desc)
        compliant: Filter by compliance status (true/false)
        owner_cid: Filter by owner's canonical identity
        status: Filter by connection status (Connected/Disconnected/Unknown)
        vlan: Filter by VLAN
        tags: Filter by device tags (comma-separated for multiple tags, e.g. 'Remote,On-Site')
        query: Search term for device name, IP, MAC, owner info, tags, or group
    
    Returns:
        Paginated list of devices with filtering and sorting applied
    """
    
    # Build base query with user join for owner information
    base_query = db.query(Device).join(CanonicalIdentity, Device.owner_cid == CanonicalIdentity.cid)
    
    # Apply filters
    if compliant is not None:
        base_query = base_query.filter(Device.compliant == compliant)
    
    if owner_cid:
        base_query = base_query.filter(Device.owner_cid == owner_cid)
    
    if status:
        base_query = base_query.filter(Device.status == status)
    
    if vlan:
        base_query = base_query.filter(Device.vlan.ilike(f"%{vlan}%"))
    
    # Handle multiple tags filtering
    if tags:
        # Parse comma-separated tags
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        valid_tags = []
        
        # Validate each tag by trying to match with enum values
        for tag_str in tag_list:
            # Try to find matching enum by value (case-insensitive)
            for enum_item in DeviceTagEnum:
                if enum_item.value.lower() == tag_str.lower():
                    valid_tags.append(enum_item)
                    break
        
        if valid_tags:
            # Filter devices that have ANY of the specified tags (OR logic)
            # Much simpler and more reliable than complex grouping/having queries
            tag_device_ids = db.query(DeviceTag.device_id).filter(
                DeviceTag.tag.in_(valid_tags)
            ).distinct()
            
            base_query = base_query.filter(Device.id.in_(tag_device_ids))
        else:
            # If no valid tags were found, return empty results
            # This prevents showing all devices when invalid tags are provided
            base_query = base_query.filter(Device.id == None)
    
    # We always join with CanonicalIdentity for owner information
    # (This was already done at the beginning of the function)
    
    # Enhanced search functionality - fixed and simplified
    if query and query.strip():
        search_term = f"%{query.strip()}%"
        search_conditions = [
            Device.name.ilike(search_term),
            func.cast(Device.ip_address, String).ilike(search_term),  # Cast INET to string for search
            Device.mac_address.ilike(search_term),
            Device.vlan.ilike(search_term),
            Device.os_version.ilike(search_term),
            CanonicalIdentity.email.ilike(search_term),
            CanonicalIdentity.full_name.ilike(search_term),
            CanonicalIdentity.department.ilike(search_term)
        ]
        base_query = base_query.filter(or_(*search_conditions))
    
    # Apply sorting
    sort_column = None
    if sort_by == DeviceSortBy.name:
        sort_column = Device.name
    elif sort_by == DeviceSortBy.last_seen:
        sort_column = Device.last_seen
    elif sort_by == DeviceSortBy.compliant:
        sort_column = Device.compliant
    elif sort_by == DeviceSortBy.ip_address:
        sort_column = Device.ip_address
    elif sort_by == DeviceSortBy.mac_address:
        sort_column = Device.mac_address
    elif sort_by == DeviceSortBy.vlan:
        sort_column = Device.vlan
    elif sort_by == DeviceSortBy.os_version:
        sort_column = Device.os_version
    elif sort_by == DeviceSortBy.last_check_in:
        sort_column = Device.last_check_in
    elif sort_by == DeviceSortBy.status:
        sort_column = Device.status
    elif sort_by == DeviceSortBy.owner_email:
        sort_column = CanonicalIdentity.email
    elif sort_by == DeviceSortBy.owner_name:
        sort_column = CanonicalIdentity.full_name
    elif sort_by == DeviceSortBy.owner_department:
        sort_column = CanonicalIdentity.department
    
    if sort_column is not None:
        if sort_direction == SortDirection.desc:
            base_query = base_query.order_by(desc(sort_column))
        else:
            base_query = base_query.order_by(asc(sort_column))
    
    # Get total count (before pagination)
    total = base_query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    devices = base_query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    # Convert devices to schema with owner information
    device_schemas = []
    for device in devices:
        device_dict = {
            "id": device.id,
            "name": device.name,
            "last_seen": device.last_seen,
            "compliant": device.compliant,
            "owner_cid": device.owner_cid,
            "ip_address": str(device.ip_address) if device.ip_address else None,
            "mac_address": device.mac_address,
            "vlan": device.vlan,
            "device_type": getattr(device, 'device_type', None),
            "os_version": device.os_version,
            "last_check_in": device.last_check_in,
            "status": device.status,
            "tags": sorted([{"id": tag.id, "tag": tag.tag} for tag in device.tags], key=lambda x: x["tag"].value) if device.tags else []
        }
        
        # Add owner information as sub-object (we always have the join now)
        if hasattr(device, 'owner') and device.owner:
            device_dict["owner"] = {
                "name": device.owner.full_name,
                "email": device.owner.email,
                "department": device.owner.department
            }
        else:
            device_dict["owner"] = None
        
        # Add groups and policies
        if hasattr(device, 'owner') and device.owner:
            # Get user's group memberships
            user_groups = db.query(GroupMembership).filter(GroupMembership.cid == device.owner.cid).all()
            device_dict["groups"] = [f"{group.group_name} ({group.group_type.value})" for group in user_groups]
            
            # Get policies as Policy objects
            policies = db.query(Policy).filter(Policy.enabled == True).all()
            device_dict["policies"] = [
                {
                    "id": policy.id,
                    "name": policy.name,
                    "description": policy.description,
                    "policy_type": policy.policy_type.value,
                    "severity": policy.severity.value,
                    "enabled": policy.enabled
                } for policy in policies[:5]  # Show first 5 active policies
            ]
        else:
            device_dict["groups"] = []
            device_dict["policies"] = []
        
        device_schemas.append(DeviceSchema.model_validate(device_dict))
    
    return DeviceListResponse(
        devices=device_schemas,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/summary", response_model=dict)
def get_devices_comprehensive_summary(
    include_trends: bool = FastAPIQuery(True, description="Include trend analysis"),
    days_back: int = FastAPIQuery(30, ge=1, le=365, description="Days back for trend analysis"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get comprehensive devices summary for dashboard.
    
    **Frontend Integration Notes:**
    - Complete device statistics for dashboard cards and overview
    - Includes device counts, compliance rates, status distribution
    - Optional trend analysis for charts and metrics
    - Cached for performance with 5-minute TTL
    
    Returns:
        Comprehensive device summary with all key metrics
    """
    
    cache_key = f"devices_comprehensive_summary_{include_trends}_{days_back}d"
    cached_result = app_cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        from datetime import datetime, timedelta
        
        # Time window for trends
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Basic device counts - use specific column queries to avoid model schema issues
        total_devices = db.execute("SELECT COUNT(*) FROM devices").scalar() or 0
        connected_devices = db.execute("SELECT COUNT(*) FROM devices WHERE status = 'CONNECTED'").scalar() or 0
        disconnected_devices = db.execute("SELECT COUNT(*) FROM devices WHERE status = 'DISCONNECTED'").scalar() or 0
        unknown_devices = db.execute("SELECT COUNT(*) FROM devices WHERE status = 'UNKNOWN'").scalar() or 0
        
        # Compliance statistics
        compliant_devices = db.execute("SELECT COUNT(*) FROM devices WHERE compliant = true").scalar() or 0
        non_compliant_devices = db.execute("SELECT COUNT(*) FROM devices WHERE compliant = false").scalar() or 0
        compliance_rate = (compliant_devices / total_devices * 100) if total_devices > 0 else 0
        
        # Device distribution by VLAN
        vlan_distribution = db.query(
            Device.vlan,
            func.count(Device.id).label('count')
        ).group_by(Device.vlan).order_by(func.count(Device.id).desc()).limit(10).all()
        
        # Device distribution by OS
        os_distribution = db.query(
            Device.os_version,
            func.count(Device.id).label('count')
        ).group_by(Device.os_version).order_by(func.count(Device.id).desc()).limit(10).all()
        
        # Tag analysis - sorted by tag name for consistency
        tag_stats = db.query(DeviceTag.tag, func.count(DeviceTag.device_id).label('count')).group_by(DeviceTag.tag).order_by(DeviceTag.tag).all()
        
        # Recent activity (devices that checked in recently) - use raw SQL to avoid schema issues
        recent_activity_sql = f"SELECT COUNT(*) FROM devices WHERE last_check_in >= '{cutoff_date.isoformat()}'"
        recent_activity = db.execute(recent_activity_sql).scalar() or 0
        
        # Devices needing attention (non-compliant or not seen recently)
        attention_sql = f"""
            SELECT COUNT(*) FROM devices 
            WHERE compliant = false 
            OR last_seen < '{cutoff_date.isoformat()}'
            OR status = 'UNKNOWN'
        """
        devices_needing_attention = db.execute(attention_sql).scalar() or 0
        
        # Security alerts (simulated based on non-compliance and old devices)
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        security_sql = f"""
            SELECT COUNT(*) FROM devices 
            WHERE compliant = false 
            AND last_seen < '{week_ago}'
        """
        security_alerts = db.execute(security_sql).scalar() or 0
        
        result = {
            "overview": {
                "total_devices": total_devices,
                "connected_devices": connected_devices,
                "disconnected_devices": disconnected_devices,
                "unknown_devices": unknown_devices,
                "connectivity_rate": round((connected_devices / total_devices * 100), 1) if total_devices > 0 else 0
            },
            "compliance": {
                "compliant_devices": compliant_devices,
                "non_compliant_devices": non_compliant_devices,
                "compliance_rate": round(compliance_rate, 1),
                "devices_needing_attention": devices_needing_attention,
                "security_alerts": security_alerts
            },
            "distribution": {
                "by_vlan": [
                    {"vlan": vlan, "count": count}
                    for vlan, count in vlan_distribution
                ],
                "by_os": [
                    {"os_version": os_version[:50], "count": count}  # Truncate long OS names
                    for os_version, count in os_distribution
                ],
                "by_tags": [
                    {"tag": tag.value, "count": count}
                    for tag, count in tag_stats[:10]
                ]
            },
            "activity": {
                "recent_checkins": recent_activity,
                "activity_rate": round((recent_activity / total_devices * 100), 1) if total_devices > 0 else 0,
                "last_updated": datetime.utcnow().isoformat(),
                "analysis_period_days": days_back
            }
        }
        
        # Add trend analysis if requested
        if include_trends:
            # Simulate trend data (in real system, this would query historical data)
            result["trends"] = {
                "device_growth": {
                    "current_period": total_devices,
                    "previous_period": max(0, total_devices - random.randint(0, 10)),
                    "growth_rate": round(random.uniform(-5.0, 15.0), 1)
                },
                "compliance_trend": {
                    "current_rate": round(compliance_rate, 1),
                    "previous_rate": round(max(0, compliance_rate - random.uniform(-10, 10)), 1),
                    "trend_direction": random.choice(["up", "down", "stable"])
                },
                "connectivity_trend": {
                    "current_rate": round((connected_devices / total_devices * 100), 1) if total_devices > 0 else 0,
                    "avg_daily_disconnections": random.randint(0, 5),
                    "peak_usage_hours": ["09:00-11:00", "13:00-17:00"]
                }
            }
        
        # Cache for 5 minutes
        app_cache.set(cache_key, result, ttl_seconds=300)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate devices summary: {str(e)}"
        )


@router.get("/{device_id}", response_model=DeviceSchema)
def get_device_detail(
    device_id: UUID,
    # Optional search context parameters for frontend navigation
    search_query: Optional[str] = FastAPIQuery(None, description="Original search query for navigation context"),
    page: Optional[int] = FastAPIQuery(None, description="Original page number for navigation context"),
    compliant: Optional[bool] = FastAPIQuery(None, description="Original compliance filter for navigation context"),
    device_status: Optional[str] = FastAPIQuery(None, description="Original status filter for navigation context"),
    tags: Optional[str] = FastAPIQuery(None, description="Original tags filter for navigation context"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get detailed device information with optional search context for navigation.

    **Frontend Integration Notes:**
    - Use this for device detail views
    - Returns complete device information
    - Pass original search parameters to maintain search context for "Back to Search" functionality
    - Useful for device management workflows

    Args:
        device_id: Device's unique identifier
        search_query: Original search query (for navigation context)
        page: Original page number (for navigation context)
        compliant: Original compliance filter (for navigation context)
        device_status: Original status filter (for navigation context)
        tags: Original tags filter (for navigation context)

    Returns:
        Complete device information with optional search context

    Raises:
        404: Device not found
    """
    
    # Query device with owner information
    device = db.query(Device).join(CanonicalIdentity, Device.owner_cid == CanonicalIdentity.cid).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Create device dict with owner information
    device_dict = {
        "id": device.id,
        "name": device.name,
        "last_seen": device.last_seen,
        "compliant": device.compliant,
        "owner_cid": device.owner_cid,
        "ip_address": str(device.ip_address) if device.ip_address else None,
        "mac_address": device.mac_address,
        "vlan": device.vlan,
        "device_type": getattr(device, 'device_type', None),
        "os_version": device.os_version,
        "last_check_in": device.last_check_in,
        "status": device.status,
        "tags": sorted([{"id": tag.id, "tag": tag.tag} for tag in device.tags], key=lambda x: x["tag"].value) if device.tags else []
    }
    
    # Add owner information as sub-object (we have the join now)
    if hasattr(device, 'owner') and device.owner:
        device_dict["owner"] = {
            "name": device.owner.full_name,
            "email": device.owner.email,
            "department": device.owner.department
        }
    else:
        device_dict["owner"] = None
    
    # Add groups and policies
    if hasattr(device, 'owner') and device.owner:
        # Get user's group memberships
        user_groups = db.query(GroupMembership).filter(GroupMembership.cid == device.owner.cid).all()
        device_dict["groups"] = [f"{group.group_name} ({group.group_type.value})" for group in user_groups]
        
        # Get policies as Policy objects
        policies = db.query(Policy).filter(Policy.enabled == True).all()
        device_dict["policies"] = [
            {
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "policy_type": policy.policy_type.value,
                "severity": policy.severity.value,
                "enabled": policy.enabled
            } for policy in policies[:5]  # Show first 5 active policies
        ]
    else:
        device_dict["groups"] = []
        device_dict["policies"] = []

    # Add search context for frontend navigation (if provided)
    search_context = {}
    if search_query is not None:
        search_context["search_query"] = search_query
    if page is not None:
        search_context["page"] = page
    if compliant is not None:
        search_context["compliant"] = compliant
    if device_status is not None:
        search_context["status"] = device_status
    if tags is not None:
        search_context["tags"] = tags

    if search_context:
        device_dict["search_context"] = search_context

    return DeviceSchema.model_validate(device_dict)


@router.put("/{device_id}", response_model=DeviceSchema)
def update_device(
    device_id: UUID,
    update_data: DeviceUpdateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Update device information.
    
    **Frontend Integration Notes:**
    - Use this to rename devices, change compliance status, or reassign ownership
    - Only provide fields that need to be updated (partial updates supported)
    - When changing owner_cid, ensure the target user exists
    - Returns the complete updated device object
    
    Args:
        device_id: Device's unique identifier
        update_data: Fields to update (only non-null fields will be updated)
    
    Returns:
        Complete updated device information
        
    Raises:
        404: Device not found
        400: Invalid owner_cid provided
    """
    
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Validate owner_cid if provided
    if update_data.owner_cid:
        owner = db.query(CanonicalIdentity).filter(
            CanonicalIdentity.cid == update_data.owner_cid
        ).first()
        if not owner:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"User with CID {update_data.owner_cid} not found"
            )
    
    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(device, field):
            setattr(device, field, value)
    
    db.commit()
    db.refresh(device)
    
    return DeviceSchema.model_validate(device)


@router.put("/{device_id}/rename", response_model=DeviceSchema)
def rename_device(
    device_id: UUID,
    rename_data: DeviceRenameRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Rename a device.
    
    **Frontend Integration Notes:**
    - Simple device renaming operation
    - Validates name format and length
    - Returns updated device information
    
    Args:
        device_id: Device's unique identifier
        rename_data: New device name
    
    Returns:
        Updated device information with new name
        
    Raises:
        404: Device not found
        400: Invalid name format
    """
    
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Store old value for audit trail
    old_name = device.name
    
    # Update the device name
    device.name = rename_data.name
    
    try:
        # Log the configuration change
        log_config_change(
            db=db,
            entity_type="device",
            entity_id=device.id,
            change_type=ConfigChangeTypeEnum.UPDATED,
            field_name="name",
            old_value=old_name,
            new_value=rename_data.name,
            changed_by="API User"
        )
        
        db.commit()
        db.refresh(device)
        return DeviceSchema.model_validate(device)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rename device: {str(e)}"
        )


@router.put("/{device_id}/tags", response_model=DeviceSchema)
def retag_device(
    device_id: UUID,
    tag_data: DeviceTagRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Update device tags (replace all existing tags).
    
    **Frontend Integration Notes:**
    - Replaces ALL existing tags with the provided list
    - To add a tag: include all existing tags + new tag
    - To remove a tag: include all existing tags except the one to remove
    - Empty list removes all tags
    - Returns updated device information with new tags
    
    Args:
        device_id: Device's unique identifier
        tag_data: New list of tags to set for the device
    
    Returns:
        Updated device information with new tags
        
    Raises:
        404: Device not found
        400: Invalid tag values
    """
    
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    try:
        # Get current tags for audit trail
        current_tags = db.query(DeviceTag).filter(DeviceTag.device_id == device_id).all()
        old_tags = [tag.tag.value for tag in current_tags]
        new_tags = [tag.value for tag in tag_data.tags]
        
        # Remove all existing tags for this device
        db.query(DeviceTag).filter(DeviceTag.device_id == device_id).delete()
        
        # Add new tags
        for tag_enum in tag_data.tags:
            new_tag = DeviceTag(
                device_id=device_id,
                tag=tag_enum
            )
            db.add(new_tag)
        
        # Log the configuration change
        log_config_change(
            db=db,
            entity_type="device",
            entity_id=device.id,
            change_type=ConfigChangeTypeEnum.UPDATED,
            field_name="tags",
            old_value=", ".join(sorted(old_tags)),
            new_value=", ".join(sorted(new_tags)),
            changed_by="API User"
        )
        
        db.commit()
        db.refresh(device)
        return DeviceSchema.model_validate(device)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device tags: {str(e)}"
        )


@router.post("/merge", response_model=DeviceMergeResponse)
def merge_devices(
    merge_data: DeviceMergeRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Merge multiple devices into one primary device.
    
    **Frontend Integration Notes:**
    - Combines data from multiple devices into a single device
    - Primary device keeps its core identity (ID, name, owner)
    - Tags from all devices are combined (duplicates removed)
    - Most recent data is preserved for timestamps
    - Devices being merged are deleted after successful merge
    - This operation cannot be undone
    
    **Merge Strategy:**
    - Primary device: Keeps name, owner, and core identity
    - IP/MAC/VLAN: Uses primary device values
    - Tags: Combines all unique tags from all devices
    - Timestamps: Uses most recent values across all devices
    - Compliance: Uses primary device compliance status
    
    Args:
        merge_data: Merge request with primary device and devices to merge
    
    Returns:
        Merged device information and operation summary
        
    Raises:
        404: One or more devices not found
        400: Invalid merge request (e.g., trying to merge device with itself)
    """
    
    # Validate that primary device exists
    primary_device = db.query(Device).filter(
        Device.id == merge_data.primary_device_id
    ).first()
    
    if not primary_device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Primary device with ID {merge_data.primary_device_id} not found"
        )
    
    # Validate that all devices to merge exist
    devices_to_merge = db.query(Device).filter(
        Device.id.in_(merge_data.device_ids_to_merge)
    ).all()
    
    if len(devices_to_merge) != len(merge_data.device_ids_to_merge):
        found_ids = {d.id for d in devices_to_merge}
        missing_ids = set(merge_data.device_ids_to_merge) - found_ids
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Devices not found: {list(missing_ids)}"
        )
    
    try:
        # Collect all tags from all devices (including primary)
        all_device_ids = [merge_data.primary_device_id] + merge_data.device_ids_to_merge
        all_tags = db.query(DeviceTag).filter(
            DeviceTag.device_id.in_(all_device_ids)
        ).all()
        
        # Get unique tags
        unique_tags = {}
        for tag in all_tags:
            unique_tags[tag.tag] = tag.tag
        
        # Update primary device with merged data
        all_devices = [primary_device] + devices_to_merge
        
        # Find most recent timestamps
        most_recent_last_seen = max((d.last_seen for d in all_devices if d.last_seen), default=primary_device.last_seen)
        most_recent_check_in = max((d.last_check_in for d in all_devices if d.last_check_in), default=primary_device.last_check_in)
        
        # Update primary device timestamps if newer ones found
        if most_recent_last_seen and most_recent_last_seen > primary_device.last_seen:
            primary_device.last_seen = most_recent_last_seen
        if most_recent_check_in and most_recent_check_in > primary_device.last_check_in:
            primary_device.last_check_in = most_recent_check_in
        
        # Remove all existing tags from primary device
        db.query(DeviceTag).filter(DeviceTag.device_id == primary_device.id).delete()
        
        # Add all unique tags to primary device
        for tag_enum in unique_tags.values():
            new_tag = DeviceTag(
                device_id=primary_device.id,
                tag=tag_enum
            )
            db.add(new_tag)
        
        # Transfer activity history from merged devices to primary device
        for device in devices_to_merge:
            # Update activity history to point to primary device
            db.query(ActivityHistory).filter(
                ActivityHistory.device_id == device.id
            ).update({"device_id": primary_device.id})
        
        # Delete devices that were merged (and their tags)
        deleted_ids = []
        for device in devices_to_merge:
            # Delete device tags first (due to foreign key constraint)
            db.query(DeviceTag).filter(DeviceTag.device_id == device.id).delete()
            # Delete the device
            db.delete(device)
            deleted_ids.append(device.id)
        
        # Log the merge operation
        merged_device_names = [d.name for d in devices_to_merge]
        log_config_change(
            db=db,
            entity_type="device",
            entity_id=primary_device.id,
            change_type=ConfigChangeTypeEnum.UPDATED,
            field_name="merge_operation",
            old_value=f"Standalone device",
            new_value=f"Merged with devices: {', '.join(merged_device_names)}",
            changed_by="API User"
        )
        
        # Log deletion of merged devices
        for device in devices_to_merge:
            log_config_change(
                db=db,
                entity_type="device",
                entity_id=device.id,
                change_type=ConfigChangeTypeEnum.DELETED,
                field_name="device_record",
                old_value=f"Device: {device.name}",
                new_value=f"Merged into device: {primary_device.name} ({primary_device.id})",
                changed_by="API User"
            )
        
        db.commit()
        db.refresh(primary_device)
        
        return DeviceMergeResponse(
            merged_device=DeviceSchema.model_validate(primary_device),
            merged_count=len(devices_to_merge),
            deleted_device_ids=deleted_ids
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge devices: {str(e)}"
        )


@router.delete("/{device_id}")
def delete_device(
    device_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Delete a device.
    
    **Frontend Integration Notes:**
    - Use this to remove devices from the system
    - Permanent deletion - cannot be undone
    - Returns success message
    
    Args:
        device_id: Device's unique identifier
    
    Returns:
        Success message
        
    Raises:
        404: Device not found
    """
    
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    device_name = device.name
    db.delete(device)
    db.commit()
    
    return {"message": f"Device '{device_name}' has been deleted successfully"}


@router.get("/non-compliant/summary")
def get_non_compliant_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get summary of non-compliant devices by owner.
    
    **Frontend Integration Notes:**
    - Use this for compliance dashboards
    - Shows which users have non-compliant devices
    - Useful for generating compliance reports
    
    Returns:
        List of users with their non-compliant device counts
    """
    
    # Query to get non-compliant device counts per user
    result = db.query(
        CanonicalIdentity.cid,
        CanonicalIdentity.full_name,
        CanonicalIdentity.email,
        CanonicalIdentity.department,
        func.count(Device.id).label('non_compliant_devices')
    ).join(
        Device, Device.owner_cid == CanonicalIdentity.cid
    ).filter(
        Device.compliant == False
    ).group_by(
        CanonicalIdentity.cid,
        CanonicalIdentity.full_name,
        CanonicalIdentity.email,
        CanonicalIdentity.department
    ).all()
    
    return [
        {
            "cid": row.cid,
            "full_name": row.full_name,
            "email": row.email,
            "department": row.department,
            "non_compliant_devices": row.non_compliant_devices
        }
        for row in result
    ]


@router.get("/summary/counts")
def get_device_counts_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get device count summary for dashboard boxes.
    
    **Frontend Integration Notes:**
    - Use this for dashboard widgets showing device statistics
    - Returns total devices, MDM devices, and BYOD devices counts
    """
    # Total devices
    total_devices = db.query(Device).count()
    
    # MDM devices (Corporate tagged devices)
    mdm_devices = (
        db.query(Device)
        .join(DeviceTag)
        .filter(DeviceTag.tag == DeviceTagEnum.CORPORATE)
        .count()
    )
    
    # BYOD devices (BYOD tagged devices)
    byod_devices = (
        db.query(Device)
        .join(DeviceTag)
        .filter(DeviceTag.tag == DeviceTagEnum.BYOD)
        .count()
    )
    
    return {
        "total_devices": total_devices,
        "mdm_devices": mdm_devices,
        "byod_devices": byod_devices
    }


@router.get("/summary/by-status")
def get_device_status_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get device count breakdown by connection status.
    
    **Frontend Integration Notes:**
    - Use this for status distribution charts/widgets
    - Shows connected vs disconnected vs unknown devices
    - Useful for network monitoring dashboards
    """
    status_counts = (
        db.query(Device.status, func.count(Device.id))
        .group_by(Device.status)
        .all()
    )
    
    result = {status.value: 0 for status in DeviceStatusEnum}
    for status, count in status_counts:
        if status:
            result[status.value] = count
    
    return result


@router.get("/summary/compliance")
def get_device_compliance_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get device compliance breakdown with percentages.
    
    **Frontend Integration Notes:**
    - Use this for compliance dashboards and charts
    - Returns counts and percentages for compliant vs non-compliant
    - Useful for executive reporting and compliance metrics
    """
    total_devices = db.query(Device).count()
    compliant_devices = db.query(Device).filter(Device.compliant == True).count()
    non_compliant_devices = total_devices - compliant_devices
    
    compliant_percentage = round((compliant_devices / total_devices * 100), 2) if total_devices > 0 else 0
    non_compliant_percentage = round((non_compliant_devices / total_devices * 100), 2) if total_devices > 0 else 0
    
    return {
        "total_devices": total_devices,
        "compliant_devices": compliant_devices,
        "non_compliant_devices": non_compliant_devices,
        "compliant_percentage": compliant_percentage,
        "non_compliant_percentage": non_compliant_percentage
    }


@router.get("/summary/by-os")
def get_device_os_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get device count breakdown by operating system (backward compatibility).

    **Frontend Integration Notes:**
    - DEPRECATED: Use /summary/by-device-info instead
    - This endpoint extracts just the OS portion from device info
    - Maintained for backward compatibility
    """
    device_info_counts = (
        db.query(Device.os_version, func.count(Device.id))
        .filter(Device.os_version.isnot(None))
        .group_by(Device.os_version)
        .order_by(func.count(Device.id).desc())
        .all()
    )

    # Extract just OS information for backward compatibility
    os_summary = {}
    for device_info, count in device_info_counts:
        if device_info and " - " in device_info:
            # Extract OS from "MacBook Pro 16\" - macOS 14.2 Sonoma"
            _, os_version = device_info.split(" - ", 1)
        else:
            os_version = device_info or "Unknown OS"

        # Aggregate counts for the same OS
        if os_version in os_summary:
            os_summary[os_version] += count
        else:
            os_summary[os_version] = count

    return os_summary


@router.get("/summary/by-tag")
def get_device_tag_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get device count breakdown by tags.
    
    **Frontend Integration Notes:**
    - Use this for tag distribution charts
    - Shows how devices are distributed across different categories
    - Useful for organizational insights (remote vs on-site, exec vs regular, etc.)
    """
    tag_counts = (
        db.query(DeviceTag.tag, func.count(DeviceTag.device_id))
        .group_by(DeviceTag.tag)
        .all()
    )
    
    result = {tag.value: 0 for tag in DeviceTagEnum}
    for tag, count in tag_counts:
        if tag:
            result[tag.value] = count
    
    return result


@router.get("/summary/by-vlan")
def get_device_vlan_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get device count breakdown by VLAN.
    
    **Frontend Integration Notes:**
    - Use this for network segmentation analysis
    - Shows device distribution across VLANs
    - Useful for network security and planning dashboards
    """
    vlan_counts = (
        db.query(Device.vlan, func.count(Device.id))
        .filter(Device.vlan.isnot(None))
        .group_by(Device.vlan)
        .all()
    )
    
    return {vlan: count for vlan, count in vlan_counts}


@router.get("/summary/recent-activity")
def get_device_recent_activity_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get summary of recent device activity (last 24 hours, 7 days, 30 days).
    
    **Frontend Integration Notes:**
    - Use this for device activity monitoring
    - Shows devices that have checked in recently vs stale devices
    - Useful for identifying potentially lost or inactive devices
    """
    from datetime import datetime, timedelta
    
    now = datetime.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    devices_24h = db.query(Device).filter(Device.last_check_in >= last_24h).count()
    devices_7d = db.query(Device).filter(Device.last_check_in >= last_7d).count()
    devices_30d = db.query(Device).filter(Device.last_check_in >= last_30d).count()
    total_devices = db.query(Device).count()
    stale_devices = total_devices - devices_30d
    
    return {
        "last_24_hours": devices_24h,
        "last_7_days": devices_7d,
        "last_30_days": devices_30d,
        "stale_devices": stale_devices,
        "total_devices": total_devices
    }


@router.get("/summary/by-device-info")
def get_device_info_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get device count breakdown by device model and OS information.

    **Frontend Integration Notes:**
    - Use this for device model distribution analysis
    - Shows device types and their operating systems
    - Useful for hardware inventory and compatibility planning
    - Replaces the old OS-only view with comprehensive device info
    """
    device_info_counts = (
        db.query(Device.os_version, func.count(Device.id))
        .filter(Device.os_version.isnot(None))
        .group_by(Device.os_version)
        .order_by(func.count(Device.id).desc())
        .all()
    )

    # Parse device info to extract device model and OS separately
    result = {}
    for device_info, count in device_info_counts:
        if device_info and " - " in device_info:
            # Format: "MacBook Pro 16\" - macOS 14.2 Sonoma"
            device_model, os_version = device_info.split(" - ", 1)
            display_name = f"{device_model} ({os_version})"
        else:
            # Fallback for devices without proper formatting
            display_name = device_info or "Unknown Device"

        result[display_name] = count

    return result


@router.get("/summary/risk-analysis")
def get_device_risk_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get device risk analysis summary combining multiple factors.
    
    **Frontend Integration Notes:**
    - Use this for security dashboards and risk assessment
    - Combines compliance, connectivity, and activity data
    - Useful for identifying high-risk devices and users
    """
    from datetime import datetime, timedelta
    
    now = datetime.now()
    last_7d = now - timedelta(days=7)
    
    # Non-compliant devices
    non_compliant = db.query(Device).filter(Device.compliant == False).count()
    
    # Disconnected devices
    disconnected = db.query(Device).filter(Device.status == DeviceStatusEnum.DISCONNECTED).count()
    
    # Stale devices (no check-in in 7 days)
    stale = db.query(Device).filter(Device.last_check_in < last_7d).count()
    
    # High-risk devices (non-compliant AND disconnected)
    high_risk = (
        db.query(Device)
        .filter(Device.compliant == False)
        .filter(Device.status == DeviceStatusEnum.DISCONNECTED)
        .count()
    )
    
    total_devices = db.query(Device).count()
    
    return {
        "total_devices": total_devices,
        "non_compliant_devices": non_compliant,
        "disconnected_devices": disconnected,
        "stale_devices": stale,
        "high_risk_devices": high_risk,
        "risk_score_percentage": round((high_risk / total_devices * 100), 2) if total_devices > 0 else 0
    }


# Cached summary endpoints
@router.get("/summary/counts")
def get_device_counts_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get cached device counts summary for dashboard.
    
    Returns total devices, compliant/non-compliant counts, and status breakdown.
    This endpoint is cached for 5 minutes to improve dashboard performance.
    """
    cache_key = "device_counts_summary"
    
    # Try to get from cache first
    cached_result = app_cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Calculate fresh data
    total_devices = db.query(Device).count()
    compliant_devices = db.query(Device).filter(Device.compliant == True).count()
    non_compliant_devices = total_devices - compliant_devices
    
    connected_devices = db.query(Device).filter(Device.status == DeviceStatusEnum.CONNECTED).count()
    disconnected_devices = db.query(Device).filter(Device.status == DeviceStatusEnum.DISCONNECTED).count()
    unknown_devices = db.query(Device).filter(Device.status == DeviceStatusEnum.UNKNOWN).count()
    
    result = {
        "total_devices": total_devices,
        "compliant_devices": compliant_devices,
        "non_compliant_devices": non_compliant_devices,
        "connected_devices": connected_devices,
        "disconnected_devices": disconnected_devices,
        "unknown_devices": unknown_devices,
        "cached": False  # Indicates this is fresh data
    }
    
    # Cache for 5 minutes (300 seconds)
    app_cache.set(cache_key, result, ttl_seconds=300)
    
    return result


@router.get("/summary/by-status")  
def get_devices_by_status_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get cached device status breakdown for charts.
    
    Returns device counts grouped by status with percentages.
    This endpoint is cached for 5 minutes.
    """
    cache_key = "devices_by_status_summary"
    
    # Try to get from cache first
    cached_result = app_cache.get(cache_key)
    if cached_result is not None:
        cached_result["cached"] = True
        return cached_result
    
    # Calculate fresh data
    total_devices = db.query(Device).count()
    
    if total_devices == 0:
        result = {
            "total": 0,
            "breakdown": [],
            "cached": False
        }
    else:
        status_counts = db.query(
            Device.status,
            func.count(Device.id).label('count')
        ).group_by(Device.status).all()
        
        breakdown = []
        for status, count in status_counts:
            breakdown.append({
                "status": status.value,
                "count": count,
                "percentage": round((count / total_devices) * 100, 2)
            })
        
        result = {
            "total": total_devices,
            "breakdown": breakdown,
            "cached": False
        }
    
    # Cache for 5 minutes
    app_cache.set(cache_key, result, ttl_seconds=300)
    
    return result


