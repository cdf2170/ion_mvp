from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
import random
from uuid import UUID

from backend.app.db.session import get_db
from backend.app.db.models import CanonicalIdentity, Device, GroupMembership, Account, StatusEnum
from backend.app.schemas import (
    UserListResponse, 
    UserListItemSchema, 
    UserDetailSchema,
    ScanResultSchema,
    IdentityMergeRequest,
    IdentityMergeResult,
    IdentityUpdateRequest,
    DeviceUpdateRequest,
    DeviceListResponse,
    DeviceSchema
)
from backend.app.security.auth import verify_token


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    status: Optional[StatusEnum] = Query(None, description="Filter by user status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    query: Optional[str] = Query(None, description="Search in email and full_name"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get paginated list of users with optional filtering and search.
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (1-100)
    - **status**: Filter by user status (Active/Disabled)
    - **department**: Filter by department name
    - **query**: Search term for email and full name
    """
    
    # Build base query
    base_query = db.query(CanonicalIdentity)
    
    # Apply filters
    if status:
        base_query = base_query.filter(CanonicalIdentity.status == status)
    
    if department:
        base_query = base_query.filter(CanonicalIdentity.department.ilike(f"%{department}%"))
    
    if query:
        search_filter = or_(
            CanonicalIdentity.email.ilike(f"%{query}%"),
            CanonicalIdentity.full_name.ilike(f"%{query}%")
        )
        base_query = base_query.filter(search_filter)
    
    # Get total count
    total = base_query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    users = base_query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return UserListResponse(
        users=[UserListItemSchema.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{cid}", response_model=UserDetailSchema)
def get_user_detail(
    cid: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get detailed user information including devices, groups, and accounts.
    
    - **cid**: User's canonical identity UUID
    """
    
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == cid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with CID {cid} not found"
        )
    
    # Transform the user data for response
    user_data = UserDetailSchema.model_validate(user)
    user_data.groups = user.group_memberships
    
    return user_data


@router.post("/scan/{cid}", response_model=ScanResultSchema)
def simulate_compliance_scan(
    cid: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Simulate a compliance scan by randomly flipping one device's compliance status.
    
    - **cid**: User's canonical identity UUID
    """
    
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == cid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with CID {cid} not found"
        )
    
    devices = db.query(Device).filter(Device.owner_cid == cid).all()
    
    if not devices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No devices found for user {cid}"
        )
    
    # Randomly select one device and flip its compliance status
    device_to_scan = random.choice(devices)
    original_status = device_to_scan.compliant
    device_to_scan.compliant = not device_to_scan.compliant
    
    db.commit()
    
    compliance_changes = 1 if device_to_scan.compliant != original_status else 0
    status_change = "compliant" if device_to_scan.compliant else "non-compliant"
    
    return ScanResultSchema(
        cid=cid,
        message=f"Compliance scan completed. Device '{device_to_scan.name}' is now {status_change}.",
        devices_scanned=len(devices),
        compliance_changes=compliance_changes
    )


@router.put("/{cid}", response_model=UserDetailSchema)
def update_user_identity(
    cid: UUID,
    update_data: IdentityUpdateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Update user identity information.
    
    **Frontend Integration Notes:**
    - Use this endpoint to rename users, change departments, update roles, etc.
    - Only provide fields that need to be updated (partial updates supported)
    - Returns the complete updated user object
    
    Args:
        cid: User's canonical identity UUID
        update_data: Fields to update (only non-null fields will be updated)
    
    Returns:
        Complete updated user information
        
    Raises:
        404: User not found
    """
    
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == cid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with CID {cid} not found"
        )
    
    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Transform the user data for response
    user_data = UserDetailSchema.model_validate(user)
    user_data.groups = user.group_memberships
    
    return user_data


@router.post("/merge", response_model=IdentityMergeResult)
def merge_user_identities(
    merge_request: IdentityMergeRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Merge two user identities into one canonical identity.
    
    **Frontend Integration Notes:**
    - Use this to consolidate duplicate user records
    - Source user will be deleted, target user will retain all data
    - Useful for correlating accounts that belong to the same person
    - Returns count of transferred items for audit purposes
    
    Args:
        merge_request: Details of merge operation including source and target CIDs
    
    Returns:
        Summary of merge results including transferred data counts
        
    Raises:
        404: Source or target user not found
        400: Attempting to merge user with themselves
    """
    
    if merge_request.source_cid == merge_request.target_cid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot merge user with themselves"
        )
    
    # Get both users
    source_user = db.query(CanonicalIdentity).filter(
        CanonicalIdentity.cid == merge_request.source_cid
    ).first()
    target_user = db.query(CanonicalIdentity).filter(
        CanonicalIdentity.cid == merge_request.target_cid
    ).first()
    
    if not source_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source user with CID {merge_request.source_cid} not found"
        )
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target user with CID {merge_request.target_cid} not found"
        )
    
    devices_transferred = 0
    accounts_transferred = 0
    groups_transferred = 0
    
    # Transfer devices
    if merge_request.merge_devices:
        devices = db.query(Device).filter(Device.owner_cid == merge_request.source_cid).all()
        for device in devices:
            device.owner_cid = merge_request.target_cid
        devices_transferred = len(devices)
    
    # Transfer accounts
    if merge_request.merge_accounts:
        accounts = db.query(Account).filter(Account.cid == merge_request.source_cid).all()
        for account in accounts:
            # Check if target already has account for this service
            existing = db.query(Account).filter(
                Account.cid == merge_request.target_cid,
                Account.service == account.service
            ).first()
            if not existing:
                account.cid = merge_request.target_cid
                accounts_transferred += 1
            else:
                # Delete duplicate account
                db.delete(account)
    
    # Transfer group memberships
    if merge_request.merge_groups:
        groups = db.query(GroupMembership).filter(
            GroupMembership.cid == merge_request.source_cid
        ).all()
        for group in groups:
            # Check if target already has this group membership
            existing = db.query(GroupMembership).filter(
                GroupMembership.cid == merge_request.target_cid,
                GroupMembership.group_name == group.group_name
            ).first()
            if not existing:
                group.cid = merge_request.target_cid
                groups_transferred += 1
            else:
                # Delete duplicate group membership
                db.delete(group)
    
    # Delete the source user
    db.delete(source_user)
    db.commit()
    
    return IdentityMergeResult(
        merged_cid=merge_request.target_cid,
        devices_transferred=devices_transferred,
        accounts_transferred=accounts_transferred,
        groups_transferred=groups_transferred,
        message=f"Successfully merged {source_user.full_name} into {target_user.full_name}. "
                f"Transferred {devices_transferred} devices, {accounts_transferred} accounts, "
                f"and {groups_transferred} group memberships."
    )
