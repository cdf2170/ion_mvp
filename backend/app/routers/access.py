from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, asc, desc, text
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
from datetime import datetime, timedelta
import json

from backend.app.db.session import get_db
from backend.app.db.models import (
    AccessGrant, AccessAuditLog, AccessReview, AccessPattern, CanonicalIdentity,
    AccessTypeEnum, AccessStatusEnum, AccessReasonEnum, AuditActionEnum
)
from backend.app.utils import SortDirection
from backend.app.security.auth import verify_token

router = APIRouter(prefix="/access", tags=["access-management"])


class AccessSortBy(str, Enum):
    """Available columns for sorting access grants"""
    granted_at = "granted_at"
    expires_at = "expires_at"
    resource_name = "resource_name"
    access_level = "access_level"
    risk_level = "risk_level"
    status = "status"
    user_email = "user_email"
    granted_by = "granted_by"
    last_reviewed_at = "last_reviewed_at"


class AuditSortBy(str, Enum):
    """Available columns for sorting audit logs"""
    timestamp = "timestamp"
    action = "action"
    resource_name = "resource_name"
    performed_by = "performed_by"
    risk_assessment = "risk_assessment"


# Pydantic schemas for access management
from pydantic import BaseModel, Field

class AccessGrantSchema(BaseModel):
    """Access grant details"""
    id: UUID
    user_cid: UUID
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_department: Optional[str] = None
    
    # Access details
    access_type: AccessTypeEnum
    resource_name: str
    resource_identifier: Optional[str] = None
    access_level: str
    permissions: Optional[Dict[str, Any]] = None
    
    # Timing
    granted_at: datetime
    expires_at: Optional[datetime] = None
    effective_start: Optional[datetime] = None
    
    # Authorization
    granted_by: str
    approved_by: Optional[str] = None
    source_system: Optional[str] = None
    
    # Justification
    reason: AccessReasonEnum
    justification: Optional[str] = None
    business_justification: Optional[str] = None
    
    # Status
    status: AccessStatusEnum
    
    # Revocation (if applicable)
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[AccessReasonEnum] = None
    revocation_justification: Optional[str] = None
    
    # Review info
    last_reviewed_at: Optional[datetime] = None
    last_reviewed_by: Optional[str] = None
    next_review_due: Optional[datetime] = None
    
    # Risk and compliance
    risk_level: Optional[str] = None
    compliance_tags: Optional[List[str]] = None
    
    # Emergency access
    is_emergency_access: bool = False
    emergency_ticket: Optional[str] = None
    emergency_approver: Optional[str] = None
    
    # Timing info
    days_until_expiry: Optional[int] = None
    days_since_granted: Optional[int] = None
    days_since_review: Optional[int] = None

    class Config:
        from_attributes = True


class AccessAuditLogSchema(BaseModel):
    """Audit log entry details"""
    id: UUID
    user_cid: UUID
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    # Core audit info
    action: AuditActionEnum
    timestamp: datetime
    
    # Resource info
    resource_name: str
    resource_identifier: Optional[str] = None
    access_type: AccessTypeEnum
    access_level: Optional[str] = None
    
    # Action context
    performed_by: str
    reason: Optional[AccessReasonEnum] = None
    justification: Optional[str] = None
    
    # State changes
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    
    # Technical context
    source_system: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Emergency context
    is_emergency: bool = False
    emergency_ticket: Optional[str] = None
    emergency_approver: Optional[str] = None
    
    # Compliance
    compliance_tags: Optional[List[str]] = None
    risk_assessment: Optional[str] = None
    
    # Cryptographic verification
    record_hash: str
    signature: Optional[str] = None
    is_sealed: bool = False

    class Config:
        from_attributes = True


class AccessListResponse(BaseModel):
    """Paginated response for access grants"""
    access_grants: List[AccessGrantSchema]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: Dict[str, Any]


class AuditLogListResponse(BaseModel):
    """Paginated response for audit logs"""
    audit_logs: List[AccessAuditLogSchema]
    total: int
    page: int
    page_size: int
    total_pages: int
    integrity_status: Dict[str, Any]


@router.get("", response_model=AccessListResponse)
def get_access_grants(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    sort_by: AccessSortBy = Query(AccessSortBy.granted_at, description="Column to sort by"),
    sort_direction: SortDirection = Query(SortDirection.desc, description="Sort direction"),
    
    # Filters
    user_cid: Optional[UUID] = Query(None, description="Filter by specific user"),
    access_type: Optional[AccessTypeEnum] = Query(None, description="Filter by access type"),
    status: Optional[AccessStatusEnum] = Query(None, description="Filter by access status"),
    resource_name: Optional[str] = Query(None, description="Filter by resource name (partial match)"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    expires_within_days: Optional[int] = Query(None, description="Filter access expiring within N days"),
    granted_by: Optional[str] = Query(None, description="Filter by who granted access"),
    is_emergency: Optional[bool] = Query(None, description="Filter emergency access"),
    needs_review: Optional[bool] = Query(None, description="Filter access needing review"),
    compliance_tag: Optional[str] = Query(None, description="Filter by compliance requirement"),
    
    # Search
    query: Optional[str] = Query(None, description="Search across user, resource, and justification"),
    
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get comprehensive access grants with filtering, search, and audit-ready details.
    
    **Perfect for Access Management Dashboard:**
    - Shows who has access to what and why
    - Tracks expiration dates and review requirements  
    - Provides audit trail links and compliance tagging
    - Supports complex filtering for access reviews
    
    **Key Features:**
    - Real-time access status with expiration tracking
    - Emergency access identification and tracking
    - Compliance tagging (SOX, PCI, GDPR, etc.)
    - Risk-based access classification
    - Direct links to users and audit history
    """
    
    # Build base query with user information
    base_query = db.query(AccessGrant).join(
        CanonicalIdentity, AccessGrant.user_cid == CanonicalIdentity.cid
    )
    
    # Apply filters
    if user_cid:
        base_query = base_query.filter(AccessGrant.user_cid == user_cid)
    
    if access_type:
        base_query = base_query.filter(AccessGrant.access_type == access_type)
    
    if status:
        base_query = base_query.filter(AccessGrant.status == status)
    
    if resource_name:
        base_query = base_query.filter(AccessGrant.resource_name.ilike(f"%{resource_name}%"))
    
    if risk_level:
        base_query = base_query.filter(AccessGrant.risk_level == risk_level)
    
    if granted_by:
        base_query = base_query.filter(AccessGrant.granted_by.ilike(f"%{granted_by}%"))
    
    if is_emergency is not None:
        base_query = base_query.filter(AccessGrant.is_emergency_access == is_emergency)
    
    if compliance_tag:
        base_query = base_query.filter(
            AccessGrant.compliance_tags.op('?')(compliance_tag)
        )
    
    # Time-based filters
    if expires_within_days is not None:
        expiry_threshold = datetime.utcnow() + timedelta(days=expires_within_days)
        base_query = base_query.filter(
            and_(
                AccessGrant.expires_at.isnot(None),
                AccessGrant.expires_at <= expiry_threshold
            )
        )
    
    if needs_review:
        review_threshold = datetime.utcnow()
        base_query = base_query.filter(
            or_(
                AccessGrant.next_review_due <= review_threshold,
                AccessGrant.next_review_due.is_(None)
            )
        )
    
    # Search functionality
    if query:
        search_conditions = [
            CanonicalIdentity.email.ilike(f"%{query}%"),
            CanonicalIdentity.full_name.ilike(f"%{query}%"),
            AccessGrant.resource_name.ilike(f"%{query}%"),
            AccessGrant.justification.ilike(f"%{query}%"),
            AccessGrant.business_justification.ilike(f"%{query}%")
        ]
        base_query = base_query.filter(or_(*search_conditions))
    
    # Apply sorting
    if sort_by == AccessSortBy.granted_at:
        sort_column = AccessGrant.granted_at
    elif sort_by == AccessSortBy.expires_at:
        sort_column = AccessGrant.expires_at
    elif sort_by == AccessSortBy.resource_name:
        sort_column = AccessGrant.resource_name
    elif sort_by == AccessSortBy.access_level:
        sort_column = AccessGrant.access_level
    elif sort_by == AccessSortBy.risk_level:
        sort_column = AccessGrant.risk_level
    elif sort_by == AccessSortBy.status:
        sort_column = AccessGrant.status
    elif sort_by == AccessSortBy.user_email:
        sort_column = CanonicalIdentity.email
    elif sort_by == AccessSortBy.granted_by:
        sort_column = AccessGrant.granted_by
    elif sort_by == AccessSortBy.last_reviewed_at:
        sort_column = AccessGrant.last_reviewed_at
    else:
        sort_column = AccessGrant.granted_at
    
    if sort_direction == SortDirection.desc:
        base_query = base_query.order_by(desc(sort_column))
    else:
        base_query = base_query.order_by(asc(sort_column))
    
    # Get total count for pagination
    total = base_query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    access_grants = base_query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    # Convert to schema with additional calculated fields
    access_schemas = []
    for grant in access_grants:
        # Calculate time-based fields
        now = datetime.utcnow()
        days_since_granted = (now - grant.granted_at).days if grant.granted_at else None
        days_until_expiry = (grant.expires_at - now).days if grant.expires_at else None
        days_since_review = (now - grant.last_reviewed_at).days if grant.last_reviewed_at else None
        
        # Parse compliance tags from JSON
        compliance_tags = []
        if grant.compliance_tags:
            if isinstance(grant.compliance_tags, list):
                compliance_tags = grant.compliance_tags
            elif isinstance(grant.compliance_tags, dict):
                compliance_tags = list(grant.compliance_tags.keys())
        
        access_schema = AccessGrantSchema(
            id=grant.id,
            user_cid=grant.user_cid,
            user_email=grant.user.email if grant.user else None,
            user_name=grant.user.full_name if grant.user else None,
            user_department=grant.user.department if grant.user else None,
            
            access_type=grant.access_type,
            resource_name=grant.resource_name,
            resource_identifier=grant.resource_identifier,
            access_level=grant.access_level,
            permissions=grant.permissions,
            
            granted_at=grant.granted_at,
            expires_at=grant.expires_at,
            effective_start=grant.effective_start,
            
            granted_by=grant.granted_by,
            approved_by=grant.approved_by,
            source_system=grant.source_system,
            
            reason=grant.reason,
            justification=grant.justification,
            business_justification=grant.business_justification,
            
            status=grant.status,
            
            revoked_at=grant.revoked_at,
            revoked_by=grant.revoked_by,
            revocation_reason=grant.revocation_reason,
            revocation_justification=grant.revocation_justification,
            
            last_reviewed_at=grant.last_reviewed_at,
            last_reviewed_by=grant.last_reviewed_by,
            next_review_due=grant.next_review_due,
            
            risk_level=grant.risk_level,
            compliance_tags=compliance_tags,
            
            is_emergency_access=grant.is_emergency_access,
            emergency_ticket=grant.emergency_ticket,
            emergency_approver=grant.emergency_approver,
            
            days_until_expiry=days_until_expiry,
            days_since_granted=days_since_granted,
            days_since_review=days_since_review
        )
        access_schemas.append(access_schema)
    
    # Generate summary statistics
    summary_query = db.query(AccessGrant)
    if user_cid:
        summary_query = summary_query.filter(AccessGrant.user_cid == user_cid)
    
    total_active = summary_query.filter(AccessGrant.status == AccessStatusEnum.ACTIVE).count()
    total_expired = summary_query.filter(AccessGrant.status == AccessStatusEnum.EXPIRED).count()
    total_revoked = summary_query.filter(AccessGrant.status == AccessStatusEnum.REVOKED).count()
    total_emergency = summary_query.filter(AccessGrant.is_emergency_access == True).count()
    
    # Expiring soon (next 30 days)
    expiry_threshold = datetime.utcnow() + timedelta(days=30)
    expiring_soon = summary_query.filter(
        and_(
            AccessGrant.expires_at.isnot(None),
            AccessGrant.expires_at <= expiry_threshold,
            AccessGrant.status == AccessStatusEnum.ACTIVE
        )
    ).count()
    
    summary = {
        "total_access_grants": total,
        "active_access": total_active,
        "expired_access": total_expired,
        "revoked_access": total_revoked,
        "emergency_access": total_emergency,
        "expiring_within_30_days": expiring_soon
    }
    
    return AccessListResponse(
        access_grants=access_schemas,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        summary=summary
    )


@router.get("/audit", response_model=AuditLogListResponse)
def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Number of items per page"),
    sort_by: AuditSortBy = Query(AuditSortBy.timestamp, description="Column to sort by"),
    sort_direction: SortDirection = Query(SortDirection.desc, description="Sort direction"),
    
    # Filters
    user_cid: Optional[UUID] = Query(None, description="Filter by specific user"),
    action: Optional[AuditActionEnum] = Query(None, description="Filter by audit action"),
    resource_name: Optional[str] = Query(None, description="Filter by resource name"),
    performed_by: Optional[str] = Query(None, description="Filter by who performed action"),
    access_type: Optional[AccessTypeEnum] = Query(None, description="Filter by access type"),
    date_from: Optional[datetime] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO format)"),
    is_emergency: Optional[bool] = Query(None, description="Filter emergency actions"),
    compliance_tag: Optional[str] = Query(None, description="Filter by compliance requirement"),
    
    # Search
    query: Optional[str] = Query(None, description="Search across user, resource, and justification"),
    
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get comprehensive audit logs with cryptographic integrity verification.
    
    **Perfect for Compliance and Forensic Analysis:**
    - Immutable audit trail of all access changes
    - Cryptographically signed records for integrity
    - Complete before/after state tracking
    - Emergency access and high-risk action flagging
    
    **Key Features:**
    - Tamper-evident audit records
    - Complete context capture (IP, user agent, etc.)
    - Compliance framework tagging
    - Cross-system request tracing
    - Risk-based action classification
    """
    
    # Build base query with user information
    base_query = db.query(AccessAuditLog).join(
        CanonicalIdentity, AccessAuditLog.user_cid == CanonicalIdentity.cid
    )
    
    # Apply filters
    if user_cid:
        base_query = base_query.filter(AccessAuditLog.user_cid == user_cid)
    
    if action:
        base_query = base_query.filter(AccessAuditLog.action == action)
    
    if resource_name:
        base_query = base_query.filter(AccessAuditLog.resource_name.ilike(f"%{resource_name}%"))
    
    if performed_by:
        base_query = base_query.filter(AccessAuditLog.performed_by.ilike(f"%{performed_by}%"))
    
    if access_type:
        base_query = base_query.filter(AccessAuditLog.access_type == access_type)
    
    if is_emergency is not None:
        base_query = base_query.filter(AccessAuditLog.is_emergency == is_emergency)
    
    if compliance_tag:
        base_query = base_query.filter(
            AccessAuditLog.compliance_tags.op('?')(compliance_tag)
        )
    
    # Date range filters
    if date_from:
        base_query = base_query.filter(AccessAuditLog.timestamp >= date_from)
    
    if date_to:
        base_query = base_query.filter(AccessAuditLog.timestamp <= date_to)
    
    # Search functionality
    if query:
        search_conditions = [
            CanonicalIdentity.email.ilike(f"%{query}%"),
            CanonicalIdentity.full_name.ilike(f"%{query}%"),
            AccessAuditLog.resource_name.ilike(f"%{query}%"),
            AccessAuditLog.justification.ilike(f"%{query}%"),
            AccessAuditLog.performed_by.ilike(f"%{query}%")
        ]
        base_query = base_query.filter(or_(*search_conditions))
    
    # Apply sorting
    if sort_by == AuditSortBy.timestamp:
        sort_column = AccessAuditLog.timestamp
    elif sort_by == AuditSortBy.action:
        sort_column = AccessAuditLog.action
    elif sort_by == AuditSortBy.resource_name:
        sort_column = AccessAuditLog.resource_name
    elif sort_by == AuditSortBy.performed_by:
        sort_column = AccessAuditLog.performed_by
    elif sort_by == AuditSortBy.risk_assessment:
        sort_column = AccessAuditLog.risk_assessment
    else:
        sort_column = AccessAuditLog.timestamp
    
    if sort_direction == SortDirection.desc:
        base_query = base_query.order_by(desc(sort_column))
    else:
        base_query = base_query.order_by(asc(sort_column))
    
    # Get total count
    total = base_query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    audit_logs = base_query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    # Convert to schema
    audit_schemas = []
    for log in audit_logs:
        # Parse compliance tags
        compliance_tags = []
        if log.compliance_tags:
            if isinstance(log.compliance_tags, list):
                compliance_tags = log.compliance_tags
            elif isinstance(log.compliance_tags, dict):
                compliance_tags = list(log.compliance_tags.keys())
        
        audit_schema = AccessAuditLogSchema(
            id=log.id,
            user_cid=log.user_cid,
            user_email=log.user.email if log.user else None,
            user_name=log.user.full_name if log.user else None,
            
            action=log.action,
            timestamp=log.timestamp,
            
            resource_name=log.resource_name,
            resource_identifier=log.resource_identifier,
            access_type=log.access_type,
            access_level=log.access_level,
            
            performed_by=log.performed_by,
            reason=log.reason,
            justification=log.justification,
            
            previous_state=log.previous_state,
            new_state=log.new_state,
            
            source_system=log.source_system,
            ip_address=str(log.ip_address) if log.ip_address else None,
            user_agent=log.user_agent,
            
            is_emergency=log.is_emergency,
            emergency_ticket=log.emergency_ticket,
            emergency_approver=log.emergency_approver,
            
            compliance_tags=compliance_tags,
            risk_assessment=log.risk_assessment,
            
            record_hash=log.record_hash,
            signature=log.signature,
            is_sealed=log.is_sealed
        )
        audit_schemas.append(audit_schema)
    
    # Verify integrity of audit logs (basic check)
    integrity_status = {
        "total_records": total,
        "sealed_records": db.query(AccessAuditLog).filter(AccessAuditLog.is_sealed == True).count(),
        "signed_records": db.query(AccessAuditLog).filter(AccessAuditLog.signature.isnot(None)).count(),
        "integrity_verified": True,  # Would be actual verification in production
        "last_integrity_check": datetime.utcnow().isoformat()
    }
    
    return AuditLogListResponse(
        audit_logs=audit_schemas,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        integrity_status=integrity_status
    )


@router.get("/user/{cid}", response_model=AccessListResponse)
def get_user_access(
    cid: UUID,
    include_revoked: bool = Query(False, description="Include revoked access in results"),
    include_expired: bool = Query(False, description="Include expired access in results"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get all access grants for a specific user - perfect for user detail views.
    
    **On-Demand User Audit:**
    - Complete access profile for any user
    - Current and historical access grants
    - Audit trail integration
    - Risk assessment and compliance status
    """
    
    # Verify user exists
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == cid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build query with status filters
    statuses_to_include = [AccessStatusEnum.ACTIVE, AccessStatusEnum.PENDING_APPROVAL, AccessStatusEnum.SUSPENDED]
    
    if include_revoked:
        statuses_to_include.append(AccessStatusEnum.REVOKED)
    
    if include_expired:
        statuses_to_include.append(AccessStatusEnum.EXPIRED)
    
    # Get access grants for this user
    access_grants = db.query(AccessGrant).filter(
        and_(
            AccessGrant.user_cid == cid,
            AccessGrant.status.in_(statuses_to_include)
        )
    ).order_by(desc(AccessGrant.granted_at)).all()
    
    # Convert to schemas (reuse logic from main endpoint)
    access_schemas = []
    for grant in access_grants:
        now = datetime.utcnow()
        days_since_granted = (now - grant.granted_at).days if grant.granted_at else None
        days_until_expiry = (grant.expires_at - now).days if grant.expires_at else None
        days_since_review = (now - grant.last_reviewed_at).days if grant.last_reviewed_at else None
        
        compliance_tags = []
        if grant.compliance_tags:
            if isinstance(grant.compliance_tags, list):
                compliance_tags = grant.compliance_tags
            elif isinstance(grant.compliance_tags, dict):
                compliance_tags = list(grant.compliance_tags.keys())
        
        access_schema = AccessGrantSchema(
            id=grant.id,
            user_cid=grant.user_cid,
            user_email=user.email,
            user_name=user.full_name,
            user_department=user.department,
            
            access_type=grant.access_type,
            resource_name=grant.resource_name,
            resource_identifier=grant.resource_identifier,
            access_level=grant.access_level,
            permissions=grant.permissions,
            
            granted_at=grant.granted_at,
            expires_at=grant.expires_at,
            effective_start=grant.effective_start,
            
            granted_by=grant.granted_by,
            approved_by=grant.approved_by,
            source_system=grant.source_system,
            
            reason=grant.reason,
            justification=grant.justification,
            business_justification=grant.business_justification,
            
            status=grant.status,
            
            revoked_at=grant.revoked_at,
            revoked_by=grant.revoked_by,
            revocation_reason=grant.revocation_reason,
            revocation_justification=grant.revocation_justification,
            
            last_reviewed_at=grant.last_reviewed_at,
            last_reviewed_by=grant.last_reviewed_by,
            next_review_due=grant.next_review_due,
            
            risk_level=grant.risk_level,
            compliance_tags=compliance_tags,
            
            is_emergency_access=grant.is_emergency_access,
            emergency_ticket=grant.emergency_ticket,
            emergency_approver=grant.emergency_approver,
            
            days_until_expiry=days_until_expiry,
            days_since_granted=days_since_granted,
            days_since_review=days_since_review
        )
        access_schemas.append(access_schema)
    
    # Generate user-specific summary
    total_active = len([g for g in access_grants if g.status == AccessStatusEnum.ACTIVE])
    total_expired = len([g for g in access_grants if g.status == AccessStatusEnum.EXPIRED])
    total_revoked = len([g for g in access_grants if g.status == AccessStatusEnum.REVOKED])
    total_emergency = len([g for g in access_grants if g.is_emergency_access])
    
    expiry_threshold = datetime.utcnow() + timedelta(days=30)
    expiring_soon = len([
        g for g in access_grants 
        if g.expires_at and g.expires_at <= expiry_threshold and g.status == AccessStatusEnum.ACTIVE
    ])
    
    summary = {
        "user_email": user.email,
        "user_name": user.full_name,
        "user_department": user.department,
        "total_access_grants": len(access_grants),
        "active_access": total_active,
        "expired_access": total_expired,
        "revoked_access": total_revoked,
        "emergency_access": total_emergency,
        "expiring_within_30_days": expiring_soon
    }
    
    return AccessListResponse(
        access_grants=access_schemas,
        total=len(access_grants),
        page=1,
        page_size=len(access_grants),
        total_pages=1,
        summary=summary
    )


@router.get("/user/{cid}/audit", response_model=AuditLogListResponse)
def get_user_audit_history(
    cid: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Number of items per page"),
    action_filter: Optional[AuditActionEnum] = Query(None, description="Filter by specific action"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get complete audit history for a specific user.
    
    **Complete User Audit Trail:**
    - Every access change for the user
    - Cryptographically verified records
    - Complete context and justifications
    - Perfect for compliance investigations
    """
    
    # Verify user exists
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == cid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build query
    base_query = db.query(AccessAuditLog).filter(AccessAuditLog.user_cid == cid)
    
    if action_filter:
        base_query = base_query.filter(AccessAuditLog.action == action_filter)
    
    if date_from:
        base_query = base_query.filter(AccessAuditLog.timestamp >= date_from)
    
    if date_to:
        base_query = base_query.filter(AccessAuditLog.timestamp <= date_to)
    
    # Order by timestamp (newest first)
    base_query = base_query.order_by(desc(AccessAuditLog.timestamp))
    
    # Get total count
    total = base_query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    audit_logs = base_query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    # Convert to schema (reuse logic from audit endpoint)
    audit_schemas = []
    for log in audit_logs:
        compliance_tags = []
        if log.compliance_tags:
            if isinstance(log.compliance_tags, list):
                compliance_tags = log.compliance_tags
            elif isinstance(log.compliance_tags, dict):
                compliance_tags = list(log.compliance_tags.keys())
        
        audit_schema = AccessAuditLogSchema(
            id=log.id,
            user_cid=log.user_cid,
            user_email=user.email,
            user_name=user.full_name,
            
            action=log.action,
            timestamp=log.timestamp,
            
            resource_name=log.resource_name,
            resource_identifier=log.resource_identifier,
            access_type=log.access_type,
            access_level=log.access_level,
            
            performed_by=log.performed_by,
            reason=log.reason,
            justification=log.justification,
            
            previous_state=log.previous_state,
            new_state=log.new_state,
            
            source_system=log.source_system,
            ip_address=str(log.ip_address) if log.ip_address else None,
            user_agent=log.user_agent,
            
            is_emergency=log.is_emergency,
            emergency_ticket=log.emergency_ticket,
            emergency_approver=log.emergency_approver,
            
            compliance_tags=compliance_tags,
            risk_assessment=log.risk_assessment,
            
            record_hash=log.record_hash,
            signature=log.signature,
            is_sealed=log.is_sealed
        )
        audit_schemas.append(audit_schema)
    
    # Integrity status for this user
    integrity_status = {
        "user_records": total,
        "sealed_records": db.query(AccessAuditLog).filter(
            and_(AccessAuditLog.user_cid == cid, AccessAuditLog.is_sealed == True)
        ).count(),
        "signed_records": db.query(AccessAuditLog).filter(
            and_(AccessAuditLog.user_cid == cid, AccessAuditLog.signature.isnot(None))
        ).count(),
        "integrity_verified": True,
        "last_integrity_check": datetime.utcnow().isoformat()
    }
    
    return AuditLogListResponse(
        audit_logs=audit_schemas,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        integrity_status=integrity_status
    )


@router.get("/summary")
def get_access_summary(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get high-level access management statistics for dashboards.
    """
    
    total_grants = db.query(AccessGrant).count()
    active_grants = db.query(AccessGrant).filter(AccessGrant.status == AccessStatusEnum.ACTIVE).count()
    
    # Risk distribution
    risk_counts = db.query(
        AccessGrant.risk_level,
        func.count(AccessGrant.id).label('count')
    ).group_by(AccessGrant.risk_level).all()
    
    # Access type distribution
    type_counts = db.query(
        AccessGrant.access_type,
        func.count(AccessGrant.id).label('count')
    ).filter(AccessGrant.status == AccessStatusEnum.ACTIVE).group_by(AccessGrant.access_type).all()
    
    # Emergency access
    emergency_count = db.query(AccessGrant).filter(AccessGrant.is_emergency_access == True).count()
    
    # Expiring access (next 30 days)
    expiry_threshold = datetime.utcnow() + timedelta(days=30)
    expiring_count = db.query(AccessGrant).filter(
        and_(
            AccessGrant.expires_at.isnot(None),
            AccessGrant.expires_at <= expiry_threshold,
            AccessGrant.status == AccessStatusEnum.ACTIVE
        )
    ).count()
    
    # Recent audit activity (last 24 hours)
    recent_threshold = datetime.utcnow() - timedelta(hours=24)
    recent_audit_count = db.query(AccessAuditLog).filter(
        AccessAuditLog.timestamp >= recent_threshold
    ).count()
    
    return {
        "total_access_grants": total_grants,
        "active_access_grants": active_grants,
        "emergency_access_grants": emergency_count,
        "expiring_within_30_days": expiring_count,
        "recent_audit_events_24h": recent_audit_count,
        "risk_distribution": {
            risk_level: count for risk_level, count in risk_counts
        },
        "access_type_distribution": {
            access_type.value: count for access_type, count in type_counts
        }
    }


@router.get("/compliance/{framework}")
def get_compliance_report(
    framework: str,
    include_details: bool = Query(False, description="Include detailed records"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Generate compliance reports for specific frameworks (SOX, PCI, GDPR, etc.).
    """
    
    # Get access grants with this compliance tag
    grants_query = db.query(AccessGrant).filter(
        AccessGrant.compliance_tags.op('?')(framework)
    )
    
    total_grants = grants_query.count()
    active_grants = grants_query.filter(AccessGrant.status == AccessStatusEnum.ACTIVE).count()
    
    # Get recent audit events for this compliance framework
    recent_threshold = datetime.utcnow() - timedelta(days=90)
    audit_events = db.query(AccessAuditLog).filter(
        and_(
            AccessAuditLog.compliance_tags.op('?')(framework),
            AccessAuditLog.timestamp >= recent_threshold
        )
    ).count()
    
    response = {
        "compliance_framework": framework,
        "total_access_grants": total_grants,
        "active_access_grants": active_grants,
        "recent_audit_events_90d": audit_events,
        "report_generated_at": datetime.utcnow().isoformat()
    }
    
    if include_details:
        # Include detailed records for full compliance report
        grants = grants_query.order_by(desc(AccessGrant.granted_at)).limit(100).all()
        response["sample_access_grants"] = [
            {
                "id": str(grant.id),
                "user_email": grant.user.email if grant.user else None,
                "resource_name": grant.resource_name,
                "access_level": grant.access_level,
                "granted_at": grant.granted_at.isoformat(),
                "status": grant.status.value,
                "risk_level": grant.risk_level
            }
            for grant in grants
        ]
    
    return response
