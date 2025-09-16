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
