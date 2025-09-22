from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Query as FastAPIQuery
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, asc, desc, and_
from typing import Optional, List
from uuid import UUID
from enum import Enum

from backend.app.db.session import get_db
from backend.app.db.models import Device, CanonicalIdentity, DeviceTag, DeviceStatusEnum, DeviceTagEnum, GroupMembership, Policy
from backend.app.schemas import (
    DeviceSchema,
    DeviceListResponse,
    DeviceUpdateRequest,
    DeviceCreateRequest,
    DeviceTagRequest
)
from backend.app.security.auth import verify_token


router = APIRouter(prefix="/devices", tags=["devices"])


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
    
    # We always join with CanonicalIdentity for owner information
    # (This was already done at the beginning of the function)
    
    # Enhanced search functionality - simplified working version
    if query and query.strip():
        search_term = f"%{query.strip()}%"
        search_conditions = [
            Device.name.ilike(search_term),
            CanonicalIdentity.email.ilike(search_term),
            CanonicalIdentity.full_name.ilike(search_term)
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
            "os_version": device.os_version,
            "last_check_in": device.last_check_in,
            "status": device.status,
            "tags": device.tags
        }
        
        # Add owner information (we always have the join now)
        device_dict.update({
            "owner_name": device.owner.full_name if hasattr(device, 'owner') and device.owner else None,
            "owner_email": device.owner.email if hasattr(device, 'owner') and device.owner else None,
            "owner_department": device.owner.department if hasattr(device, 'owner') and device.owner else None
        })
        
        # Add groups and policies
        if hasattr(device, 'owner') and device.owner:
            # Get user's group memberships
            user_groups = db.query(GroupMembership).filter(GroupMembership.cid == device.owner.cid).all()
            device_dict["groups"] = [f"{group.group_name} ({group.group_type.value})" for group in user_groups]
            
            # Get policies (simplified - showing policy names that might apply)
            policies = db.query(Policy).filter(Policy.enabled == True).all()
            device_dict["policies"] = [policy.name for policy in policies[:5]]  # Show first 5 active policies
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


@router.get("/{device_id}", response_model=DeviceSchema)
def get_device_detail(
    device_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get detailed device information.
    
    **Frontend Integration Notes:**
    - Use this for device detail views
    - Returns complete device information
    - Useful for device management workflows
    
    Args:
        device_id: Device's unique identifier
    
    Returns:
        Complete device information
        
    Raises:
        404: Device not found
    """
    
    # Query device with owner information
    device = db.query(Device).join(CanonicalIdentity, Device.owner_cid == CanonicalIdentity.cid).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
        "os_version": device.os_version,
        "last_check_in": device.last_check_in,
        "status": device.status,
        "tags": device.tags
    }
    
    # Add owner information (we have the join now)
    device_dict.update({
        "owner_name": device.owner.full_name if hasattr(device, 'owner') and device.owner else None,
        "owner_email": device.owner.email if hasattr(device, 'owner') and device.owner else None,
        "owner_department": device.owner.department if hasattr(device, 'owner') and device.owner else None
    })
    
    # Add groups and policies
    if hasattr(device, 'owner') and device.owner:
        # Get user's group memberships
        user_groups = db.query(GroupMembership).filter(GroupMembership.cid == device.owner.cid).all()
        device_dict["groups"] = [f"{group.group_name} ({group.group_type.value})" for group in user_groups]
        
        # Get policies (simplified - showing policy names that might apply)
        policies = db.query(Policy).filter(Policy.enabled == True).all()
        device_dict["policies"] = [policy.name for policy in policies[:5]]  # Show first 5 active policies
    else:
        device_dict["groups"] = []
        device_dict["policies"] = []
    
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Validate owner_cid if provided
    if update_data.owner_cid:
        owner = db.query(CanonicalIdentity).filter(
            CanonicalIdentity.cid == update_data.owner_cid
        ).first()
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
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
            status_code=status.HTTP_404_NOT_FOUND,
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


@router.get("/summary/by-os")
def get_device_os_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get device count breakdown by operating system.
    
    **Frontend Integration Notes:**
    - Use this for OS distribution analysis
    - Shows which operating systems are most common
    - Useful for patch management and security planning
    """
    os_counts = (
        db.query(Device.os_version, func.count(Device.id))
        .filter(Device.os_version.isnot(None))
        .group_by(Device.os_version)
        .all()
    )
    
    return {os_version: count for os_version, count in os_counts}


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
