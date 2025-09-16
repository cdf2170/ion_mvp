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
    DeviceSchema,
    PasswordResetRequest,
    PasswordResetResult,
    ForceCheckinRequest,
    ForceCheckinResult,
    SyncRequest,
    SyncResult,
    AdvancedMergeRequest,
    MergePreviewResult
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


@router.post("/password-reset", response_model=PasswordResetResult)
def reset_user_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Reset user password across connected systems.
    
    **Frontend Integration Notes:**
    - Use this for helpdesk password reset workflows
    - Systems list can be empty to reset on all connected systems
    """
    # Verify user exists
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == request.user_cid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Simulate password reset across systems
    # In production, this would integrate with actual APIs
    if not request.systems:
        # Default to common systems if none specified
        systems_to_reset = ["Okta", "Active Directory", "Google Workspace"]
    else:
        systems_to_reset = request.systems
    
    # Simulate reset results
    systems_processed = []
    systems_failed = []
    
    for system in systems_to_reset:
        # In production, make actual API calls here
        if system in ["Okta", "Active Directory", "Google Workspace", "Microsoft 365"]:
            systems_processed.append(system)
        else:
            systems_failed.append(system)
    
    # Send notification (simulated)
    notification_sent = request.notification_method in ["email", "both"]
    
    return PasswordResetResult(
        user_cid=request.user_cid,
        systems_processed=systems_processed,
        systems_failed=systems_failed,
        notification_sent=notification_sent,
        message=f"Password reset initiated for {len(systems_processed)} systems"
    )


@router.post("/sync", response_model=SyncResult)
def sync_user_data(
    request: SyncRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Trigger synchronization of user data from external systems.
    
    **Frontend Integration Notes:**
    - Use this to refresh user data from connected APIs
    - Monitor sync_duration for performance optimization
    """
    import time
    start_time = time.time()
    
    # Simulate sync process
    if not request.systems:
        systems_to_sync = ["Okta", "Workday", "Active Directory"]
    else:
        systems_to_sync = request.systems
    
    # Simulate sync results
    users_updated = 0
    devices_updated = 0
    accounts_updated = 0
    errors = []
    
    for system in systems_to_sync:
        # In production, make actual API calls here
        if system == "Okta":
            users_updated += 15
            accounts_updated += 25
        elif system == "Workday":
            users_updated += 8
        elif system == "Active Directory":
            users_updated += 12
            accounts_updated += 18
        elif system == "CrowdStrike":
            devices_updated += 5
        else:
            errors.append(f"Unknown system: {system}")
    
    sync_duration = time.time() - start_time
    
    return SyncResult(
        systems_synced=systems_to_sync,
        users_updated=users_updated,
        devices_updated=devices_updated,
        accounts_updated=accounts_updated,
        errors=errors,
        sync_duration=sync_duration,
        message=f"Sync completed for {len(systems_to_sync)} systems"
    )


@router.post("/advanced-merge", response_model=MergePreviewResult)
def preview_advanced_merge(
    request: AdvancedMergeRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Preview advanced identity merge with conflict resolution.
    
    **Frontend Integration Notes:**
    - Use this to show merge conflicts before executing
    - Review conflicts to guide user through resolution process
    """
    # Verify both users exist
    source_user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == request.source_cid).first()
    target_user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == request.target_cid).first()
    
    if not source_user:
        raise HTTPException(status_code=404, detail="Source user not found")
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Analyze conflicts
    from backend.app.schemas import MergeConflict
    conflicts = []
    
    # Check for field conflicts
    if source_user.full_name != target_user.full_name:
        conflicts.append(MergeConflict(
            field_name="full_name",
            source_value=source_user.full_name,
            target_value=target_user.full_name,
            recommended_action="Use target value (more recent)"
        ))
    
    if source_user.department != target_user.department:
        conflicts.append(MergeConflict(
            field_name="department",
            source_value=source_user.department,
            target_value=target_user.department,
            recommended_action="Use target value (current assignment)"
        ))
    
    if source_user.role != target_user.role:
        conflicts.append(MergeConflict(
            field_name="role",
            source_value=source_user.role,
            target_value=target_user.role,
            recommended_action="Use target value (current role)"
        ))
    
    # Count items to transfer
    devices_to_transfer = len(source_user.devices) if request.merge_devices else 0
    accounts_to_transfer = len(source_user.accounts) if request.merge_accounts else 0
    groups_to_transfer = len(source_user.group_memberships) if request.merge_groups else 0
    
    # Estimate duration based on data size
    estimated_duration = 0.5 + (devices_to_transfer * 0.1) + (accounts_to_transfer * 0.05)
    
    return MergePreviewResult(
        source_cid=request.source_cid,
        target_cid=request.target_cid,
        conflicts=conflicts,
        devices_to_transfer=devices_to_transfer,
        accounts_to_transfer=accounts_to_transfer,
        groups_to_transfer=groups_to_transfer,
        estimated_duration=estimated_duration
    )


@router.post("/advanced-merge/execute")
def execute_advanced_merge(
    request: AdvancedMergeRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Execute advanced identity merge with the specified conflict resolution.
    
    **Frontend Integration Notes:**
    - Call preview endpoint first to show conflicts to user
    - Use this after user confirms conflict resolution strategy
    """
    # Verify both users exist
    source_user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == request.source_cid).first()
    target_user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == request.target_cid).first()
    
    if not source_user:
        raise HTTPException(status_code=404, detail="Source user not found")
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    items_transferred = {
        "devices": 0,
        "accounts": 0,
        "groups": 0
    }
    
    try:
        # Transfer devices
        if request.merge_devices:
            for device in source_user.devices:
                device.owner_cid = request.target_cid
                items_transferred["devices"] += 1
        
        # Transfer accounts  
        if request.merge_accounts:
            for account in source_user.accounts:
                account.user_cid = request.target_cid
                items_transferred["accounts"] += 1
        
        # Transfer group memberships
        if request.merge_groups:
            for membership in source_user.group_memberships:
                membership.user_cid = request.target_cid
                items_transferred["groups"] += 1
        
        # Apply conflict resolution strategy
        if request.conflict_resolution == "take_source":
            target_user.full_name = source_user.full_name
            target_user.department = source_user.department
            target_user.role = source_user.role
            target_user.manager = source_user.manager
            target_user.location = source_user.location
        elif request.conflict_resolution == "merge":
            # For merge strategy, prefer non-null values
            if source_user.manager and not target_user.manager:
                target_user.manager = source_user.manager
            if source_user.location and not target_user.location:
                target_user.location = source_user.location
        # For "take_target", no action needed
        
        # Preserve history if requested
        if request.preserve_history:
            # In production, you might copy activity history records
            pass
        
        # Mark source user as inactive instead of deleting
        source_user.status = StatusEnum.DISABLED
        
        db.commit()
        
        return {
            "message": "Advanced merge completed successfully",
            "source_cid": request.source_cid,
            "target_cid": request.target_cid,
            "items_transferred": items_transferred,
            "conflict_resolution_applied": request.conflict_resolution
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Merge failed: {str(e)}"
        )
