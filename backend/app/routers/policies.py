from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, asc, desc
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

from backend.app.db.session import get_db
from backend.app.db.models import Policy, PolicyTypeEnum, PolicySeverityEnum
from backend.app.utils import SortDirection, apply_pagination, apply_sorting, apply_text_search
from backend.app.schemas import (
    PolicySchema,
    PolicyCreateRequest,
    PolicyUpdateRequest,
    PolicyListResponse
)
from backend.app.security.auth import verify_token

router = APIRouter(prefix="/policies", tags=["policy-management"])


class PolicySortBy(str, Enum):
    """Available columns for sorting policies"""
    name = "name"
    policy_type = "policy_type"
    severity = "severity"
    enabled = "enabled"
    created_at = "created_at"
    updated_at = "updated_at"
    created_by = "created_by"


@router.get("", response_model=PolicyListResponse)
def get_policies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    sort_by: PolicySortBy = Query(PolicySortBy.created_at, description="Column to sort by"),
    sort_direction: SortDirection = Query(SortDirection.desc, description="Sort direction (asc/desc)"),
    policy_type: Optional[PolicyTypeEnum] = Query(None, description="Filter by policy type"),
    severity: Optional[PolicySeverityEnum] = Query(None, description="Filter by severity"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    query: Optional[str] = Query(None, description="Search in policy name, description, and creator"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get paginated list of policies with optional filtering, search, and sorting.
    
    **Frontend Integration Notes:**
    - Use this to build policy management dashboards
    - Enhanced search works across name, description, and creator
    - Supports sorting by any column with direction control
    - Multiple filter options for refined results
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page (1-100)
        sort_by: Column to sort by (name, type, severity, etc.)
        sort_direction: Sort direction (asc/desc)
        policy_type: Filter by policy type
        severity: Filter by severity level
        enabled: Filter by enabled status
        created_by: Filter by creator
        query: Search term for name, description, and creator
    
    Returns:
        Paginated list of policies with filtering and sorting applied
    """
    # Build base query
    base_query = db.query(Policy)
    
    # Apply filters
    if policy_type:
        base_query = base_query.filter(Policy.policy_type == policy_type)
    
    if severity:
        base_query = base_query.filter(Policy.severity == severity)
    
    if enabled is not None:
        base_query = base_query.filter(Policy.enabled == enabled)
    
    if created_by:
        base_query = base_query.filter(Policy.created_by.ilike(f"%{created_by}%"))
    
    # Enhanced search functionality
    if query:
        search_columns = [
            Policy.name,
            Policy.description,
            Policy.created_by
        ]
        base_query = apply_text_search(base_query, query, search_columns)
    
    # Apply sorting
    sort_mapping = {
        PolicySortBy.name: Policy.name,
        PolicySortBy.policy_type: Policy.policy_type,
        PolicySortBy.severity: Policy.severity,
        PolicySortBy.enabled: Policy.enabled,
        PolicySortBy.created_at: Policy.created_at,
        PolicySortBy.updated_at: Policy.updated_at,
        PolicySortBy.created_by: Policy.created_by
    }
    base_query = apply_sorting(base_query, sort_by.value, sort_direction, sort_mapping)
    
    # Apply pagination using utility function
    policies, total, total_pages = apply_pagination(base_query, page, page_size)
    
    return PolicyListResponse(
        policies=policies,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{policy_id}", response_model=PolicySchema)
def get_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get detailed information about a specific policy.
    
    **Frontend Integration Notes:**
    - Use this to show policy details in configuration screens
    - Parse configuration JSON for policy-specific settings
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return policy


@router.post("", response_model=PolicySchema)
def create_policy(
    request: PolicyCreateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Create a new policy.
    
    **Frontend Integration Notes:**
    - Use this to set up new compliance and security policies
    - Configuration field can store JSON for policy-specific settings
    """
    policy = Policy(
        name=request.name,
        description=request.description,
        policy_type=request.policy_type,
        severity=request.severity,
        enabled=request.enabled,
        configuration=request.configuration,
        created_by="system"  # TODO: Get from auth context
    )
    
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    return policy


@router.put("/{policy_id}", response_model=PolicySchema)
def update_policy(
    policy_id: UUID,
    request: PolicyUpdateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Update an existing policy.
    
    **Frontend Integration Notes:**
    - Use this to modify policy settings
    - Only provided fields will be updated
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Update fields if provided
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(policy, field):
            setattr(policy, field, value)
    
    policy.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(policy)
    
    return policy


@router.delete("/{policy_id}")
def delete_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Delete a policy.
    
    **Frontend Integration Notes:**
    - Use this to remove outdated policies
    - Consider soft delete for audit purposes in production
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    db.delete(policy)
    db.commit()
    
    return {"message": "Policy deleted successfully"}


@router.post("/{policy_id}/enable")
def enable_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Enable a policy.
    
    **Frontend Integration Notes:**
    - Use this for quick policy activation
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy.enabled = True
    policy.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Policy enabled successfully"}


@router.post("/{policy_id}/disable")
def disable_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Disable a policy.
    
    **Frontend Integration Notes:**
    - Use this for quick policy deactivation
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy.enabled = False
    policy.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Policy disabled successfully"}


@router.get("/summary/by-type")
def get_policy_summary_by_type(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get policy summary grouped by type.
    
    **Frontend Integration Notes:**
    - Use this for dashboard widgets showing policy distribution
    """
    type_counts = (
        db.query(Policy.policy_type, func.count(Policy.id))
        .group_by(Policy.policy_type)
        .all()
    )
    
    enabled_counts = (
        db.query(Policy.policy_type, func.count(Policy.id))
        .filter(Policy.enabled == True)
        .group_by(Policy.policy_type)
        .all()
    )
    
    total_policies = db.query(Policy).count()
    enabled_policies = db.query(Policy).filter(Policy.enabled == True).count()
    
    return {
        "total_policies": total_policies,
        "enabled_policies": enabled_policies,
        "by_type": {policy_type.value: count for policy_type, count in type_counts},
        "enabled_by_type": {policy_type.value: count for policy_type, count in enabled_counts}
    }


@router.get("/summary/by-severity")
def get_policy_summary_by_severity(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get policy summary grouped by severity.
    
    **Frontend Integration Notes:**
    - Use this for compliance dashboards showing risk levels
    """
    severity_counts = (
        db.query(Policy.severity, func.count(Policy.id))
        .group_by(Policy.severity)
        .all()
    )
    
    enabled_severity_counts = (
        db.query(Policy.severity, func.count(Policy.id))
        .filter(Policy.enabled == True)
        .group_by(Policy.severity)
        .all()
    )
    
    return {
        "by_severity": {severity.value: count for severity, count in severity_counts},
        "enabled_by_severity": {severity.value: count for severity, count in enabled_severity_counts}
    }
