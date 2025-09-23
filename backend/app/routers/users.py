from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, asc, desc
from typing import Optional, List
import random
from uuid import UUID
from enum import Enum

from backend.app.db.session import get_db
from backend.app.db.models import CanonicalIdentity, Device, GroupMembership, Account, StatusEnum, ConfigHistory, ConfigChangeTypeEnum, ActivityHistory
from backend.app.utils import SortDirection, apply_pagination, apply_sorting, apply_text_search
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
    MergePreviewResult,
    FullDiskScanRequest,
    FullDiskScanResult,
    BulkUserOperationRequest,
    BulkUserOperationResult,
    DeviceAssignmentRequest,
    DeviceAssignmentResult,
    DeviceTransferRequest,
    DeviceTransferResult,
    DeviceUnassignmentRequest,
    DeviceUnassignmentResult,
    BulkDeviceManagementRequest,
    BulkDeviceManagementResult
)
from backend.app.security.auth import verify_token


router = APIRouter(prefix="/users", tags=["users"])


def log_user_config_change(
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
    Log a user-related configuration change to the audit trail.
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
        print(f"Warning: Failed to log user config change: {str(e)}")


def get_devices_with_owner_info(db: Session, owner_cid: UUID) -> List[dict]:
    """
    Helper function to get devices with complete owner information.
    Returns devices in consistent schema format across all endpoints.
    """
    devices = db.query(Device).join(CanonicalIdentity, Device.owner_cid == CanonicalIdentity.cid).filter(Device.owner_cid == owner_cid).all()
    
    device_list = []
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
            "tags": sorted([{"id": tag.id, "tag": tag.tag} for tag in device.tags], key=lambda x: x["tag"].value) if device.tags else []
        }
        
        # Add owner information (we have the join)
        device_dict.update({
            "owner_name": device.owner.full_name if hasattr(device, 'owner') and device.owner else None,
            "owner_email": device.owner.email if hasattr(device, 'owner') and device.owner else None,
            "owner_department": device.owner.department if hasattr(device, 'owner') and device.owner else None
        })
        
        device_list.append(device_dict)
    
    return device_list


class UserSortBy(str, Enum):
    """Available columns for sorting users"""
    email = "email"
    full_name = "full_name"
    department = "department"
    role = "role"
    last_seen = "last_seen"
    status = "status"
    created_at = "created_at"
    manager = "manager"
    location = "location"


@router.get("", response_model=UserListResponse)
def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    sort_by: UserSortBy = Query(UserSortBy.full_name, description="Column to sort by"),
    sort_direction: SortDirection = Query(SortDirection.asc, description="Sort direction (asc/desc)"),
    status: Optional[StatusEnum] = Query(None, description="Filter by user status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    role: Optional[str] = Query(None, description="Filter by role"),
    location: Optional[str] = Query(None, description="Filter by location"),
    query: Optional[str] = Query(None, description="Search in email, name, department, role, manager, and location"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get paginated list of users with optional filtering, search, and sorting.
    
    **Frontend Integration Notes:**
    - Enhanced search works across email, name, department, role, manager, and location
    - Supports sorting by any column with direction control
    - Multiple filter options for refined results
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page (1-100)
        sort_by: Column to sort by (email, full_name, department, etc.)
        sort_direction: Sort direction (asc/desc)
        status: Filter by user status (Active/Disabled)
        department: Filter by department name
        role: Filter by role/title
        location: Filter by location
        query: Search term for email, name, department, role, manager, and location
    
    Returns:
        Paginated list of users with filtering and sorting applied
    """
    
    # Build base query
    base_query = db.query(CanonicalIdentity)
    
    # Apply filters
    if status:
        base_query = base_query.filter(CanonicalIdentity.status == status)
    
    if department:
        base_query = base_query.filter(CanonicalIdentity.department.ilike(f"%{department}%"))
    
    if role:
        base_query = base_query.filter(CanonicalIdentity.role.ilike(f"%{role}%"))
    
    if location:
        base_query = base_query.filter(CanonicalIdentity.location.ilike(f"%{location}%"))
    
    # Enhanced search functionality
    if query:
        search_columns = [
            CanonicalIdentity.email,
            CanonicalIdentity.full_name,
            CanonicalIdentity.department,
            CanonicalIdentity.role,
            CanonicalIdentity.manager,
            CanonicalIdentity.location
        ]
        base_query = apply_text_search(base_query, query, search_columns)
    
    # Apply sorting
    sort_mapping = {
        UserSortBy.email: CanonicalIdentity.email,
        UserSortBy.full_name: CanonicalIdentity.full_name,
        UserSortBy.department: CanonicalIdentity.department,
        UserSortBy.role: CanonicalIdentity.role,
        UserSortBy.last_seen: CanonicalIdentity.last_seen,
        UserSortBy.status: CanonicalIdentity.status,
        UserSortBy.created_at: CanonicalIdentity.created_at,
        UserSortBy.manager: CanonicalIdentity.manager,
        UserSortBy.location: CanonicalIdentity.location
    }
    base_query = apply_sorting(base_query, sort_by.value, sort_direction, sort_mapping)
    
    # Apply pagination using utility function
    users, total, total_pages = apply_pagination(base_query, page, page_size)
    
    # Enhance users with device and group counts
    enhanced_users = []
    for user in users:
        # Get device count for this user
        device_count = db.query(Device).filter(Device.owner_cid == user.cid).count()
        
        # Get group membership count for this user
        groups_count = db.query(GroupMembership).filter(GroupMembership.cid == user.cid).count()
        
        # Create enhanced user object
        enhanced_user = UserListItemSchema(
            cid=user.cid,
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            role=user.role,
            location=user.location,
            last_seen=user.last_seen,
            status=user.status,
            device_count=device_count,
            groups_count=groups_count
        )
        enhanced_users.append(enhanced_user)
    
    return UserListResponse(
        users=enhanced_users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/summary")
def get_users_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get users summary statistics for dashboard cards.
    
    **Frontend Integration Notes:**
    - Provides key user metrics for dashboard cards
    - Includes user counts, status breakdown, department distribution
    - Perfect for users summary widgets
    
    Returns:
        Users summary with counts, status breakdown, and key metrics
    """
    
    try:
        # Total users
        total_users = db.query(CanonicalIdentity).count()
        
        # Users by status
        active_users = db.query(CanonicalIdentity).filter(
            CanonicalIdentity.status == StatusEnum.ACTIVE
        ).count()
        disabled_users = total_users - active_users
        
        # Users with devices
        users_with_devices = db.query(CanonicalIdentity).join(Device).distinct().count()
        users_without_devices = total_users - users_with_devices
        
        # Department breakdown (top 5)
        department_stats = db.query(
            CanonicalIdentity.department,
            func.count(CanonicalIdentity.cid).label('count')
        ).group_by(CanonicalIdentity.department).order_by(
            func.count(CanonicalIdentity.cid).desc()
        ).limit(5).all()
        
        # Role breakdown (top 5)
        role_stats = db.query(
            CanonicalIdentity.role,
            func.count(CanonicalIdentity.cid).label('count')
        ).group_by(CanonicalIdentity.role).order_by(
            func.count(CanonicalIdentity.cid).desc()
        ).limit(5).all()
        
        # Location breakdown (top 5)
        location_stats = db.query(
            CanonicalIdentity.location,
            func.count(CanonicalIdentity.cid).label('count')
        ).filter(CanonicalIdentity.location.isnot(None)).group_by(
            CanonicalIdentity.location
        ).order_by(func.count(CanonicalIdentity.cid).desc()).limit(5).all()
        
        # Recent user activity (users seen in last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_active_users = db.query(CanonicalIdentity).filter(
            CanonicalIdentity.last_seen >= week_ago
        ).count()
        
        return {
            "overview": {
                "total_users": total_users,
                "active_users": active_users,
                "disabled_users": disabled_users,
                "users_with_devices": users_with_devices,
                "users_without_devices": users_without_devices,
                "recent_active_users": recent_active_users
            },
            "status_breakdown": {
                "active": active_users,
                "disabled": disabled_users,
                "active_percentage": round((active_users / total_users * 100), 1) if total_users > 0 else 0
            },
            "device_association": {
                "with_devices": users_with_devices,
                "without_devices": users_without_devices,
                "device_association_rate": round((users_with_devices / total_users * 100), 1) if total_users > 0 else 0
            },
            "top_departments": [
                {"department": dept, "count": count} 
                for dept, count in department_stats
            ],
            "top_roles": [
                {"role": role, "count": count} 
                for role, count in role_stats
            ],
            "top_locations": [
                {"location": location, "count": count} 
                for location, count in location_stats
            ],
            "activity": {
                "recent_active": recent_active_users,
                "activity_rate": round((recent_active_users / total_users * 100), 1) if total_users > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate users summary: {str(e)}"
        )


@router.post("/full-disk-scan/{cid}", response_model=FullDiskScanResult)
def full_disk_scan(
    cid: UUID,
    scan_request: FullDiskScanRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Perform comprehensive full disk scan on user's devices.
    
    **Frontend Integration Notes:**
    - Comprehensive scan including file permissions, disk usage, compliance
    - Configurable scan depth (quick, standard, deep)
    - Returns detailed results per device with security alerts
    - Use for thorough security audits and compliance checks
    
    Args:
        cid: User's canonical identity
        scan_request: Scan configuration parameters
    
    Returns:
        Detailed scan results with security and compliance findings
        
    Raises:
        404: User not found
        400: Invalid scan parameters
    """
    
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == cid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with CID {cid} not found"
        )
    
    # Get user's devices
    devices = db.query(Device).filter(Device.owner_cid == cid).all()
    
    try:
        import time
        import uuid
        
        scan_start = time.time()
        scan_id = uuid.uuid4()
        
        # Simulate comprehensive disk scan
        detailed_results = []
        total_files = 0
        total_issues = 0
        total_disk_usage = 0.0
        total_security_alerts = 0
        
        for device in devices:
            # Simulate device-specific scan based on scan depth
            scan_multiplier = {
                'quick': 1000,
                'standard': 5000,
                'deep': 15000
            }.get(scan_request.scan_depth, 5000)
            
            device_files = random.randint(scan_multiplier, scan_multiplier * 2)
            device_issues = random.randint(0, max(1, device_files // 1000))
            device_disk_gb = random.uniform(50.0, 500.0)
            device_alerts = random.randint(0, max(1, device_issues // 2))
            
            device_result = {
                "device_id": str(device.id),
                "device_name": device.name,
                "files_scanned": device_files,
                "issues_found": device_issues,
                "disk_usage_gb": round(device_disk_gb, 2),
                "security_alerts": device_alerts,
                "scan_duration_seconds": round(random.uniform(30.0, 300.0), 2),
                "compliance_status": "compliant" if device_issues < 3 else "non_compliant",
                "top_issues": [
                    f"Unauthorized file access in /tmp",
                    f"Outdated security certificates",
                    f"Suspicious network connections"
                ][:device_alerts] if device_alerts > 0 else []
            }
            
            detailed_results.append(device_result)
            total_files += device_files
            total_issues += device_issues
            total_disk_usage += device_disk_gb
            total_security_alerts += device_alerts
        
        scan_duration = time.time() - scan_start
        
        # Generate summary based on results
        compliance_rate = (len(devices) - sum(1 for r in detailed_results if r["compliance_status"] == "non_compliant")) / len(devices) * 100 if devices else 100
        
        scan_summary = f"Full disk scan completed for {len(devices)} devices. "
        scan_summary += f"Compliance rate: {compliance_rate:.1f}%. "
        scan_summary += f"Found {total_issues} issues requiring attention. "
        if total_security_alerts > 0:
            scan_summary += f"{total_security_alerts} security alerts detected."
        else:
            scan_summary += "No critical security alerts."
        
        return FullDiskScanResult(
            scan_id=scan_id,
            user_cid=cid,
            devices_scanned=len(devices),
            scan_duration_seconds=round(scan_duration, 2),
            files_scanned=total_files,
            issues_found=total_issues,
            disk_usage_gb=round(total_disk_usage, 2),
            security_alerts=total_security_alerts,
            scan_summary=scan_summary,
            detailed_results=detailed_results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Full disk scan failed: {str(e)}"
        )


@router.post("/force-checkin/{cid}", response_model=ForceCheckinResult)
def force_user_checkin(
    cid: UUID,
    checkin_request: ForceCheckinRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Force check-in for all devices belonging to a user.
    
    **Frontend Integration Notes:**
    - Forces immediate check-in for user's devices
    - Updates device status and optionally runs compliance scans
    - Use for troubleshooting connectivity or compliance issues
    - Returns detailed results per device contacted
    
    Args:
        cid: User's canonical identity
        checkin_request: Check-in configuration parameters
    
    Returns:
        Results of force check-in operation with device responses
        
    Raises:
        404: User not found
    """
    
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == cid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with CID {cid} not found"
        )
    
    # Get user's devices (or specific devices if provided)
    if checkin_request.device_ids:
        devices = db.query(Device).filter(
            Device.owner_cid == cid,
            Device.id.in_(checkin_request.device_ids)
        ).all()
    else:
        devices = db.query(Device).filter(Device.owner_cid == cid).all()
    
    try:
        import time
        from datetime import datetime, timedelta
        
        devices_contacted = len(devices)
        devices_responded = 0
        compliance_scans_completed = 0
        devices_updated = []
        
        for device in devices:
            # Simulate force check-in (90% success rate)
            if random.random() < 0.9:
                devices_responded += 1
                
                # Update device last_check_in time
                device.last_check_in = datetime.utcnow()
                
                # Update last_seen if device responded
                device.last_seen = datetime.utcnow()
                
                # Optionally run compliance scan
                if checkin_request.compliance_scan:
                    # Simulate compliance scan (80% success rate)
                    if random.random() < 0.8:
                        compliance_scans_completed += 1
                        # Randomly update compliance status
                        device.compliant = random.random() < 0.85
                
                devices_updated.append(device.id)
        
        db.commit()
        
        success_rate = (devices_responded / devices_contacted * 100) if devices_contacted > 0 else 0
        message = f"Force check-in completed for {user.full_name}. "
        message += f"Contacted {devices_contacted} devices, {devices_responded} responded ({success_rate:.1f}% success rate). "
        
        if checkin_request.compliance_scan:
            message += f"Completed {compliance_scans_completed} compliance scans."
        
        return ForceCheckinResult(
            devices_contacted=devices_contacted,
            devices_responded=devices_responded,
            compliance_scans_completed=compliance_scans_completed,
            devices_updated=devices_updated,
            message=message
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Force check-in failed: {str(e)}"
        )


@router.post("/bulk-operations", response_model=BulkUserOperationResult)
def bulk_user_operations(
    operation_request: BulkUserOperationRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Perform bulk operations on multiple users.
    
    **Frontend Integration Notes:**
    - Execute operations on multiple users simultaneously
    - Supports: scan, reset_password, force_checkin, full_disk_scan
    - Returns detailed results per user with success/failure status
    - Use for administrative bulk operations
    
    Args:
        operation_request: Bulk operation configuration
    
    Returns:
        Results of bulk operation with per-user details
        
    Raises:
        400: Invalid operation type or parameters
    """
    
    try:
        import uuid
        import time
        
        operation_id = uuid.uuid4()
        operation_start = time.time()
        
        # Validate that all users exist
        users = db.query(CanonicalIdentity).filter(
            CanonicalIdentity.cid.in_(operation_request.user_cids)
        ).all()
        
        if len(users) != len(operation_request.user_cids):
            found_cids = {user.cid for user in users}
            missing_cids = set(operation_request.user_cids) - found_cids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Users not found: {list(missing_cids)}"
            )
        
        results = []
        successful_operations = 0
        failed_operations = 0
        
        for user in users:
            try:
                user_result = {
                    "user_cid": str(user.cid),
                    "user_name": user.full_name,
                    "user_email": user.email,
                    "status": "success",
                    "operation_details": {},
                    "error_message": None
                }
                
                if operation_request.operation_type == "scan":
                    # Simulate quick compliance scan
                    devices = db.query(Device).filter(Device.owner_cid == user.cid).all()
                    issues_found = random.randint(0, len(devices))
                    user_result["operation_details"] = {
                        "devices_scanned": len(devices),
                        "issues_found": issues_found,
                        "scan_duration_seconds": round(random.uniform(5.0, 30.0), 2)
                    }
                    
                elif operation_request.operation_type == "reset_password":
                    # Simulate password reset
                    user_result["operation_details"] = {
                        "password_reset": True,
                        "temporary_password_sent": True,
                        "email_sent_to": user.email
                    }
                    
                elif operation_request.operation_type == "force_checkin":
                    # Simulate force check-in
                    devices = db.query(Device).filter(Device.owner_cid == user.cid).all()
                    responded = random.randint(0, len(devices))
                    user_result["operation_details"] = {
                        "devices_contacted": len(devices),
                        "devices_responded": responded,
                        "success_rate": round((responded / len(devices) * 100), 1) if devices else 0
                    }
                    
                elif operation_request.operation_type == "full_disk_scan":
                    # Simulate full disk scan
                    devices = db.query(Device).filter(Device.owner_cid == user.cid).all()
                    total_files = sum(random.randint(1000, 10000) for _ in devices)
                    total_issues = random.randint(0, total_files // 1000)
                    user_result["operation_details"] = {
                        "devices_scanned": len(devices),
                        "files_scanned": total_files,
                        "issues_found": total_issues,
                        "scan_duration_seconds": round(random.uniform(60.0, 300.0), 2)
                    }
                
                successful_operations += 1
                results.append(user_result)
                
            except Exception as user_error:
                failed_operations += 1
                user_result = {
                    "user_cid": str(user.cid),
                    "user_name": user.full_name,
                    "user_email": user.email,
                    "status": "failed",
                    "operation_details": {},
                    "error_message": str(user_error)
                }
                results.append(user_result)
        
        operation_duration = time.time() - operation_start
        total_users = len(operation_request.user_cids)
        success_rate = (successful_operations / total_users * 100) if total_users > 0 else 0
        
        summary = f"Bulk {operation_request.operation_type} operation completed. "
        summary += f"Processed {total_users} users in {operation_duration:.1f} seconds. "
        summary += f"Success rate: {success_rate:.1f}% ({successful_operations} successful, {failed_operations} failed)."
        
        return BulkUserOperationResult(
            operation_id=operation_id,
            operation_type=operation_request.operation_type,
            total_users=total_users,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            results=results,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk operation failed: {str(e)}"
        )


@router.post("/device-assignment", response_model=DeviceAssignmentResult)
def assign_devices_to_user(
    assignment_request: DeviceAssignmentRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Assign devices to a specific user.
    
    **Frontend Integration Notes:**
    - Assign unassigned devices or reassign from other users
    - Optionally transfer activity history to new owner
    - Returns detailed results per device with success/failure status
    - Use for device onboarding and ownership management
    
    Args:
        assignment_request: Device assignment configuration
    
    Returns:
        Results of device assignment operation
        
    Raises:
        404: Target user or devices not found
        400: Invalid assignment parameters
    """
    
    # Validate target user exists
    target_user = db.query(CanonicalIdentity).filter(
        CanonicalIdentity.cid == assignment_request.target_user_cid
    ).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target user with CID {assignment_request.target_user_cid} not found"
        )
    
    # Get devices to assign
    devices = db.query(Device).filter(Device.id.in_(assignment_request.device_ids)).all()
    if len(devices) != len(assignment_request.device_ids):
        found_device_ids = {device.id for device in devices}
        missing_device_ids = set(assignment_request.device_ids) - found_device_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Devices not found: {list(missing_device_ids)}"
        )
    
    try:
        import uuid
        from datetime import datetime
        
        assignment_id = uuid.uuid4()
        devices_assigned = 0
        devices_failed = 0
        assignment_details = []
        
        for device in devices:
            device_result = {
                "device_id": str(device.id),
                "device_name": device.name,
                "previous_owner_cid": str(device.owner_cid) if device.owner_cid else None,
                "new_owner_cid": str(assignment_request.target_user_cid),
                "status": "success",
                "error_message": None
            }
            
            try:
                # Check if device is already assigned and handle force reassign
                if device.owner_cid and not assignment_request.force_reassign:
                    device_result["status"] = "failed"
                    device_result["error_message"] = f"Device already assigned to user {device.owner_cid}"
                    devices_failed += 1
                    assignment_details.append(device_result)
                    continue
                
                # Store old owner for logging
                old_owner_cid = device.owner_cid
                
                # Assign device to new user
                device.owner_cid = assignment_request.target_user_cid
                
                # Transfer activity history if requested
                if assignment_request.transfer_activity_history and old_owner_cid:
                    activity_records = db.query(ActivityHistory).filter(
                        ActivityHistory.device_id == device.id
                    ).all()
                    for activity in activity_records:
                        activity.user_cid = assignment_request.target_user_cid
                
                # Log configuration change
                log_user_config_change(
                    db=db,
                    entity_type="device",
                    entity_id=device.id,
                    change_type=ConfigChangeTypeEnum.UPDATED,
                    field_name="owner_assignment",
                    old_value=str(old_owner_cid) if old_owner_cid else "unassigned",
                    new_value=str(assignment_request.target_user_cid),
                    changed_by="API User"
                )
                
                devices_assigned += 1
                assignment_details.append(device_result)
                
            except Exception as device_error:
                device_result["status"] = "failed"
                device_result["error_message"] = str(device_error)
                devices_failed += 1
                assignment_details.append(device_result)
        
        db.commit()
        
        success_rate = (devices_assigned / len(devices) * 100) if devices else 0
        summary = f"Device assignment completed for user {target_user.full_name}. "
        summary += f"Assigned {devices_assigned} of {len(devices)} devices ({success_rate:.1f}% success rate)."
        
        return DeviceAssignmentResult(
            assignment_id=assignment_id,
            target_user_cid=assignment_request.target_user_cid,
            devices_assigned=devices_assigned,
            devices_failed=devices_failed,
            assignment_details=assignment_details,
            summary=summary
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device assignment failed: {str(e)}"
        )


@router.post("/device-transfer", response_model=DeviceTransferResult)
def transfer_device_ownership(
    transfer_request: DeviceTransferRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Transfer device ownership between users.
    
    **Frontend Integration Notes:**
    - Transfer devices from one user to another
    - Validates both source and target users exist
    - Optionally transfers activity history and notifies users
    - Use for employee transitions and device reassignments
    
    Args:
        transfer_request: Device transfer configuration
    
    Returns:
        Results of device transfer operation
        
    Raises:
        404: Source/target users or devices not found
        400: Invalid transfer parameters
    """
    
    # Validate source and target users exist
    source_user = db.query(CanonicalIdentity).filter(
        CanonicalIdentity.cid == transfer_request.source_user_cid
    ).first()
    if not source_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source user with CID {transfer_request.source_user_cid} not found"
        )
    
    target_user = db.query(CanonicalIdentity).filter(
        CanonicalIdentity.cid == transfer_request.target_user_cid
    ).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target user with CID {transfer_request.target_user_cid} not found"
        )
    
    # Get devices to transfer (must belong to source user)
    devices = db.query(Device).filter(
        Device.id.in_(transfer_request.device_ids),
        Device.owner_cid == transfer_request.source_user_cid
    ).all()
    
    if len(devices) != len(transfer_request.device_ids):
        found_device_ids = {device.id for device in devices}
        missing_device_ids = set(transfer_request.device_ids) - found_device_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Devices not found or not owned by source user: {list(missing_device_ids)}"
        )
    
    try:
        import uuid
        from datetime import datetime
        
        transfer_id = uuid.uuid4()
        devices_transferred = 0
        devices_failed = 0
        transfer_details = []
        
        for device in devices:
            device_result = {
                "device_id": str(device.id),
                "device_name": device.name,
                "source_user_cid": str(transfer_request.source_user_cid),
                "target_user_cid": str(transfer_request.target_user_cid),
                "status": "success",
                "error_message": None
            }
            
            try:
                # Transfer device ownership
                device.owner_cid = transfer_request.target_user_cid
                
                # Transfer activity history if requested
                if transfer_request.transfer_activity_history:
                    activity_records = db.query(ActivityHistory).filter(
                        ActivityHistory.device_id == device.id
                    ).all()
                    for activity in activity_records:
                        activity.user_cid = transfer_request.target_user_cid
                
                # Log configuration change
                log_user_config_change(
                    db=db,
                    entity_type="device",
                    entity_id=device.id,
                    change_type=ConfigChangeTypeEnum.UPDATED,
                    field_name="owner_transfer",
                    old_value=str(transfer_request.source_user_cid),
                    new_value=str(transfer_request.target_user_cid),
                    changed_by="API User"
                )
                
                devices_transferred += 1
                transfer_details.append(device_result)
                
            except Exception as device_error:
                device_result["status"] = "failed"
                device_result["error_message"] = str(device_error)
                devices_failed += 1
                transfer_details.append(device_result)
        
        db.commit()
        
        success_rate = (devices_transferred / len(devices) * 100) if devices else 0
        summary = f"Device transfer completed from {source_user.full_name} to {target_user.full_name}. "
        summary += f"Transferred {devices_transferred} of {len(devices)} devices ({success_rate:.1f}% success rate)."
        
        return DeviceTransferResult(
            transfer_id=transfer_id,
            source_user_cid=transfer_request.source_user_cid,
            target_user_cid=transfer_request.target_user_cid,
            devices_transferred=devices_transferred,
            devices_failed=devices_failed,
            transfer_details=transfer_details,
            summary=summary
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device transfer failed: {str(e)}"
        )


@router.post("/device-unassignment", response_model=DeviceUnassignmentResult)
def unassign_devices_from_users(
    unassignment_request: DeviceUnassignmentRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Unassign devices from their current users.
    
    **Frontend Integration Notes:**
    - Remove device ownership assignments
    - Optionally preserve activity history for audit purposes
    - Use for device decommissioning or pool management
    - Returns detailed results per device
    
    Args:
        unassignment_request: Device unassignment configuration
    
    Returns:
        Results of device unassignment operation
        
    Raises:
        404: Devices not found
    """
    
    # Get devices to unassign
    devices = db.query(Device).filter(Device.id.in_(unassignment_request.device_ids)).all()
    if len(devices) != len(unassignment_request.device_ids):
        found_device_ids = {device.id for device in devices}
        missing_device_ids = set(unassignment_request.device_ids) - found_device_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Devices not found: {list(missing_device_ids)}"
        )
    
    try:
        import uuid
        
        unassignment_id = uuid.uuid4()
        devices_unassigned = 0
        devices_failed = 0
        unassignment_details = []
        
        for device in devices:
            device_result = {
                "device_id": str(device.id),
                "device_name": device.name,
                "previous_owner_cid": str(device.owner_cid) if device.owner_cid else None,
                "status": "success",
                "error_message": None
            }
            
            try:
                old_owner_cid = device.owner_cid
                
                # Unassign device
                device.owner_cid = None
                
                # Log configuration change
                if old_owner_cid:
                    log_user_config_change(
                        db=db,
                        entity_type="device",
                        entity_id=device.id,
                        change_type=ConfigChangeTypeEnum.UPDATED,
                        field_name="owner_unassignment",
                        old_value=str(old_owner_cid),
                        new_value="unassigned",
                        changed_by="API User"
                    )
                
                devices_unassigned += 1
                unassignment_details.append(device_result)
                
            except Exception as device_error:
                device_result["status"] = "failed"
                device_result["error_message"] = str(device_error)
                devices_failed += 1
                unassignment_details.append(device_result)
        
        db.commit()
        
        success_rate = (devices_unassigned / len(devices) * 100) if devices else 0
        summary = f"Device unassignment completed. "
        summary += f"Unassigned {devices_unassigned} of {len(devices)} devices ({success_rate:.1f}% success rate). "
        summary += f"Reason: {unassignment_request.reason}"
        
        return DeviceUnassignmentResult(
            unassignment_id=unassignment_id,
            devices_unassigned=devices_unassigned,
            devices_failed=devices_failed,
            unassignment_details=unassignment_details,
            summary=summary
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device unassignment failed: {str(e)}"
        )


@router.post("/bulk-device-management", response_model=BulkDeviceManagementResult)
def bulk_device_management(
    bulk_request: BulkDeviceManagementRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Perform bulk device management operations.
    
    **Frontend Integration Notes:**
    - Execute multiple device management operations in batch
    - Supports: assign, transfer, unassign operations
    - Returns detailed results per operation with success/failure status
    - Use for large-scale device management tasks
    
    Args:
        bulk_request: Bulk device management configuration
    
    Returns:
        Results of bulk device management operations
        
    Raises:
        400: Invalid operation type or parameters
    """
    
    try:
        import uuid
        import time
        
        bulk_operation_id = uuid.uuid4()
        operation_start = time.time()
        
        successful_operations = 0
        failed_operations = 0
        operation_results = []
        
        for i, operation in enumerate(bulk_request.operations):
            operation_result = {
                "operation_index": i,
                "operation_type": bulk_request.operation_type,
                "status": "success",
                "details": {},
                "error_message": None
            }
            
            try:
                if bulk_request.operation_type == "assign":
                    # Simulate device assignment
                    device_ids = operation.get("device_ids", [])
                    target_user_cid = operation.get("target_user_cid")
                    
                    # Validate target user exists
                    target_user = db.query(CanonicalIdentity).filter(
                        CanonicalIdentity.cid == target_user_cid
                    ).first()
                    if not target_user:
                        raise ValueError(f"Target user {target_user_cid} not found")
                    
                    operation_result["details"] = {
                        "device_ids": device_ids,
                        "target_user_cid": target_user_cid,
                        "target_user_name": target_user.full_name,
                        "devices_assigned": len(device_ids)
                    }
                    
                elif bulk_request.operation_type == "transfer":
                    # Simulate device transfer
                    device_ids = operation.get("device_ids", [])
                    source_user_cid = operation.get("source_user_cid")
                    target_user_cid = operation.get("target_user_cid")
                    
                    operation_result["details"] = {
                        "device_ids": device_ids,
                        "source_user_cid": source_user_cid,
                        "target_user_cid": target_user_cid,
                        "devices_transferred": len(device_ids)
                    }
                    
                elif bulk_request.operation_type == "unassign":
                    # Simulate device unassignment
                    device_ids = operation.get("device_ids", [])
                    reason = operation.get("reason", "Bulk unassignment")
                    
                    operation_result["details"] = {
                        "device_ids": device_ids,
                        "reason": reason,
                        "devices_unassigned": len(device_ids)
                    }
                
                successful_operations += 1
                operation_results.append(operation_result)
                
            except Exception as operation_error:
                failed_operations += 1
                operation_result["status"] = "failed"
                operation_result["error_message"] = str(operation_error)
                operation_results.append(operation_result)
        
        operation_duration = time.time() - operation_start
        total_operations = len(bulk_request.operations)
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
        
        summary = f"Bulk {bulk_request.operation_type} operation completed. "
        summary += f"Processed {total_operations} operations in {operation_duration:.1f} seconds. "
        summary += f"Success rate: {success_rate:.1f}% ({successful_operations} successful, {failed_operations} failed)."
        
        return BulkDeviceManagementResult(
            bulk_operation_id=bulk_operation_id,
            operation_type=bulk_request.operation_type,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            operation_results=operation_results,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk device management failed: {str(e)}"
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
    
    # Get devices with complete owner information using our helper function
    devices_with_owner_info = get_devices_with_owner_info(db, cid)
    
    # Transform the user data for response
    user_data = UserDetailSchema.model_validate(user)
    user_data.groups = user.group_memberships
    user_data.devices = [DeviceSchema.model_validate(device) for device in devices_with_owner_info]
    
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
