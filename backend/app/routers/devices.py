from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from uuid import UUID

from backend.app.db.session import get_db
from backend.app.db.models import Device, CanonicalIdentity, DeviceTag, DeviceStatusEnum, DeviceTagEnum
from backend.app.schemas import (
    DeviceSchema,
    DeviceListResponse,
    DeviceUpdateRequest,
    DeviceCreateRequest,
    DeviceTagRequest
)
from backend.app.security.auth import verify_token


router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=DeviceListResponse)
def get_devices(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    compliant: Optional[bool] = Query(None, description="Filter by compliance status"),
    owner_cid: Optional[UUID] = Query(None, description="Filter by owner's canonical identity"),
    status: Optional[DeviceStatusEnum] = Query(None, description="Filter by connection status"),
    vlan: Optional[str] = Query(None, description="Filter by VLAN"),
    tag: Optional[DeviceTagEnum] = Query(None, description="Filter by tag"),
    query: Optional[str] = Query(None, description="Search in device name"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get paginated list of devices with optional filtering and search.
    
    **Frontend Integration Notes:**
    - Use this to build device dashboards and compliance reports
    - Supports filtering by compliance status and owner
    - Search works on device names
    - Returns pagination info for infinite scroll or page navigation
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page (1-100)
        compliant: Filter by compliance status (true/false)
        owner_cid: Filter by owner's canonical identity
        query: Search term for device name
    
    Returns:
        Paginated list of devices with filtering applied
    """
    
    # Build base query
    base_query = db.query(Device)
    
    # Apply filters
    if compliant is not None:
        base_query = base_query.filter(Device.compliant == compliant)
    
    if owner_cid:
        base_query = base_query.filter(Device.owner_cid == owner_cid)
    
    if query:
        base_query = base_query.filter(Device.name.ilike(f"%{query}%"))
    
    # Get total count
    total = base_query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    devices = base_query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return DeviceListResponse(
        devices=[DeviceSchema.model_validate(device) for device in devices],
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
    
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    return DeviceSchema.model_validate(device)


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
