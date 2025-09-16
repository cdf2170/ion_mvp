from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from backend.app.db.session import get_db
from backend.app.db.models import Policy, PolicyTypeEnum, PolicySeverityEnum
from backend.app.schemas import (
    PolicySchema,
    PolicyCreateRequest,
    PolicyUpdateRequest,
    PolicyListResponse
)
from backend.app.security.auth import verify_token

router = APIRouter(prefix="/policies", tags=["policy-management"])


@router.get("", response_model=PolicyListResponse)
def get_policies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    policy_type: Optional[PolicyTypeEnum] = Query(None, description="Filter by policy type"),
    severity: Optional[PolicySeverityEnum] = Query(None, description="Filter by severity"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    query: Optional[str] = Query(None, description="Search in policy name or description"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get paginated list of policies with optional filtering and search.
    
    **Frontend Integration Notes:**
    - Use this to build policy management dashboards
    - Filter by type to show specific policy categories
    - Use severity filtering for compliance reporting
    """
    # Build query
    query_filter = db.query(Policy)
    
    # Apply filters
    if policy_type:
        query_filter = query_filter.filter(Policy.policy_type == policy_type)
    if severity:
        query_filter = query_filter.filter(Policy.severity == severity)
    if enabled is not None:
        query_filter = query_filter.filter(Policy.enabled == enabled)
    if query:
        search = f"%{query}%"
        query_filter = query_filter.filter(
            or_(
                Policy.name.ilike(search),
                Policy.description.ilike(search)
            )
        )
    
    # Order by creation date (newest first)
    query_filter = query_filter.order_by(Policy.created_at.desc())
    
    # Get total count
    total = query_filter.count()
    
    # Apply pagination
    policies = query_filter.offset((page - 1) * page_size).limit(page_size).all()
    
    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size
    
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
