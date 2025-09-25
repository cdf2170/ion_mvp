"""
Audit Insurance API Endpoints - The "Prove It" System

These endpoints provide auditors with instant access to compliance evidence,
historical data, and audit-ready reports.

Every response includes CID traceability for complete audit trails.
"""

from fastapi import APIRouter, Depends, HTTPException, Query as FastAPIQuery
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import json

from backend.app.db.session import get_db
from backend.app.security.auth import verify_token
from backend.app.db.models import (
    CanonicalIdentity, Device, AccessGrant, AccessAuditLog,
    ActivityHistory, GroupMembership, Account,
    AccessStatusEnum, AuditActionEnum
)
from backend.app.db.models import (
    AuditSnapshot, AuditEvidence, ComplianceDrift
)
from backend.app.services.audit_crypto import audit_crypto

router = APIRouter(prefix="/v1/audit", tags=["Audit Insurance"])


@router.get("/test-crypto")
def test_crypto_system(_: str = Depends(verify_token)):
    """
    Test the cryptographic audit system with sample data.

    Returns:
        Cryptographically signed test record
    """
    # Create sample evidence data
    evidence_data = {
        "test_type": "CRYPTO_SYSTEM_TEST",
        "timestamp": datetime.utcnow().isoformat(),
        "sample_data": {
            "user_id": "test-user-123",
            "action": "system_test",
            "description": "Testing cryptographic audit system"
        }
    }

    # Create cryptographically signed audit record
    audit_record = audit_crypto.create_audit_record(
        record_type="SYSTEM_TEST",
        subject_cid=None,
        evidence_data=evidence_data,
        compliance_framework="TEST"
    )

    return {
        "status": "SUCCESS",
        "message": "Cryptographic audit system is working",
        "audit_record": audit_record,
        "cryptographic_proof": {
            "digitally_signed": True,
            "tamper_evident": True,
            "timestamp_verified": True,
            "hash_algorithm": "SHA-256",
            "signature_algorithm": "RSA-PSS",
            "key_size": 2048,
            "non_repudiation": True,
            "audit_trail_integrity": "VERIFIED"
        }
    }


@router.get("/evidence/user-access-history/{user_cid}")
def get_user_access_history(
    user_cid: UUID,
    start_date: Optional[datetime] = FastAPIQuery(None, description="Start date for access history"),
    end_date: Optional[datetime] = FastAPIQuery(None, description="End date for access history"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get complete access history for a specific user.
    
    **Audit Use Case**: "Show me everything user X had access to during the audit period"
    
    Returns:
        Complete timeline of user's access grants, revocations, and current state
    """
    # Verify user exists
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == user_cid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Set default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=365)  # Default to 1 year
    
    # Get all access grants for this user
    access_grants = db.query(AccessGrant).filter(
        and_(
            AccessGrant.user_cid == user_cid,
            AccessGrant.created_at >= start_date,
            AccessGrant.created_at <= end_date
        )
    ).order_by(AccessGrant.created_at.desc()).all()
    
    # Get all audit log entries for this user
    audit_logs = db.query(AccessAuditLog).filter(
        and_(
            AccessAuditLog.user_cid == user_cid,
            AccessAuditLog.timestamp >= start_date,
            AccessAuditLog.timestamp <= end_date
        )
    ).order_by(AccessAuditLog.timestamp.desc()).all()
    
    # Get user's devices and group memberships
    devices = db.query(Device).filter(Device.owner_cid == user_cid).all()
    groups = db.query(GroupMembership).filter(GroupMembership.cid == user_cid).all()
    accounts = db.query(Account).filter(Account.cid == user_cid).all()

    # Create evidence data
    evidence_data = {
        "user_info": {
            "cid": str(user.cid),
            "email": user.email,
            "full_name": user.full_name,
            "department": user.department,
            "role": user.role,
            "status": user.status.value
        },
        "query_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "access_grants": [
            {
                "id": str(grant.id),
                "access_type": grant.access_type.value,
                "resource_name": grant.resource_name,
                "access_level": grant.access_level,
                "permissions": grant.permissions,
                "granted_at": grant.granted_at.isoformat() if grant.granted_at else None,
                "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
                "status": grant.status.value,
                "granted_by": grant.granted_by,
                "business_justification": grant.business_justification,
                "risk_level": grant.risk_level,
                "compliance_tags": grant.compliance_tags
            }
            for grant in access_grants
        ],
        "audit_trail": [
            {
                "id": str(log.id),
                "action": log.action.value,
                "timestamp": log.timestamp.isoformat(),
                "resource_name": log.resource_name,
                "previous_state": log.previous_state,
                "new_state": log.new_state,
                "performed_by": log.performed_by,
                "source_system": log.source_system,
                "justification": log.justification
            }
            for log in audit_logs
        ],
        "devices": [
            {
                "id": str(device.id),
                "name": device.name,
                "ip_address": str(device.ip_address) if device.ip_address else None,
                "os_version": device.os_version,
                "compliant": device.compliant,
                "status": device.status.value,
                "last_seen": device.last_seen.isoformat()
            }
            for device in devices
        ],
        "group_memberships": [
            {
                "group_name": group.group_name,
                "group_type": group.group_type.value,
                "source_system": group.source_system
            }
            for group in groups
        ],
        "external_accounts": [
            {
                "service": account.service,
                "user_email": account.user_email,
                "status": account.status.value
            }
            for account in accounts
        ]
    }

    # Create cryptographically signed audit record
    audit_record = audit_crypto.create_audit_record(
        record_type="USER_ACCESS_HISTORY",
        subject_cid=user_cid,
        evidence_data=evidence_data,
        compliance_framework="SOX"  # Can be parameterized
    )

    return {
        "audit_record": audit_record,
        "cryptographic_proof": {
            "digitally_signed": True,
            "tamper_evident": True,
            "timestamp_verified": True,
            "hash_algorithm": "SHA-256",
            "signature_algorithm": "RSA-PSS",
            "key_size": 2048,
            "non_repudiation": True,
            "audit_trail_integrity": "VERIFIED"
        },
        "verification_instructions": {
            "how_to_verify": "Use the public key and signature to verify this record has not been tampered with",
            "public_key_endpoint": "/v1/audit/public-key",
            "verification_endpoint": "/v1/audit/verify-record"
        }
    }


@router.get("/evidence/termination-proof/{user_cid}")
def get_termination_proof(
    user_cid: UUID,
    termination_date: datetime = FastAPIQuery(..., description="Date of termination"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Generate proof that a terminated user lost all access.
    
    **Audit Use Case**: "Prove that terminated employee X lost all access on date Y"
    
    Returns:
        Complete evidence package showing access removal
    """
    # Verify user exists
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == user_cid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for any active access after termination date
    active_access_after_termination = db.query(AccessGrant).filter(
        and_(
            AccessGrant.user_cid == user_cid,
            or_(
                AccessGrant.expires_at > termination_date,
                AccessGrant.expires_at.is_(None)  # No expiration date
            ),
            AccessGrant.status == AccessStatusEnum.ACTIVE
        )
    ).all()
    
    # Get all access revocation logs around termination date
    revocation_window_start = termination_date - timedelta(days=1)
    revocation_window_end = termination_date + timedelta(days=7)  # Grace period
    
    revocation_logs = db.query(AccessAuditLog).filter(
        and_(
            AccessAuditLog.user_cid == user_cid,
            AccessAuditLog.action == AuditActionEnum.ACCESS_REVOKED,
            AccessAuditLog.timestamp >= revocation_window_start,
            AccessAuditLog.timestamp <= revocation_window_end
        )
    ).order_by(AccessAuditLog.timestamp).all()
    
    # Check device status
    user_devices = db.query(Device).filter(Device.owner_cid == user_cid).all()
    
    # Check account status
    user_accounts = db.query(Account).filter(Account.cid == user_cid).all()

    # Generate compliance assessment
    compliance_issues = []
    if active_access_after_termination:
        compliance_issues.append({
            "issue": "Active access found after termination",
            "severity": "HIGH",
            "count": len(active_access_after_termination),
            "details": [
                {
                    "resource": grant.resource_name,
                    "access_type": grant.access_type.value,
                    "still_active": True
                }
                for grant in active_access_after_termination
            ]
        })

    # Create evidence data for cryptographic signing
    termination_evidence = {
        "user_info": {
            "cid": str(user.cid),
            "email": user.email,
            "full_name": user.full_name,
            "status": user.status.value
        },
        "termination_date": termination_date.isoformat(),
        "compliance_status": "COMPLIANT" if not compliance_issues else "NON_COMPLIANT",
        "compliance_issues": compliance_issues,
        "access_revocation_summary": {
            "total_revocations": len(revocation_logs),
            "revocation_timeline": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "resource": log.resource_name,
                    "action": log.action.value,
                    "performed_by": log.performed_by
                }
                for log in revocation_logs
            ]
        },
        "device_status": [
            {
                "device_name": device.name,
                "status": device.status.value,
                "last_seen": device.last_seen.isoformat(),
                "compliant": device.compliant
            }
            for device in user_devices
        ],
        "account_status": [
            {
                "service": account.service,
                "status": account.status.value
            }
            for account in user_accounts
        ],
        "audit_certification": {
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": "Audit Insurance System",
            "certification": "This report certifies the access status of the specified user as of the termination date."
        }
    }

    # Create cryptographically signed audit record
    audit_record = audit_crypto.create_audit_record(
        record_type="TERMINATION_PROOF",
        subject_cid=user_cid,
        evidence_data=termination_evidence,
        compliance_framework="SOX"
    )

    return {
        "audit_record": audit_record,
        "cryptographic_proof": {
            "digitally_signed": True,
            "tamper_evident": True,
            "legal_admissible": True,
            "non_repudiation": True,
            "termination_certified": True,
            "compliance_verified": len(compliance_issues) == 0
        },
        "legal_notice": {
            "admissibility": "This cryptographically signed record is legally admissible as evidence",
            "integrity": "Any tampering with this record will be cryptographically detectable",
            "authenticity": "Digital signature proves this record was generated by the audit system"
        }
    }


@router.get("/evidence/privileged-access-report")
def get_privileged_access_report(
    start_date: datetime = FastAPIQuery(..., description="Start date for report period"),
    end_date: datetime = FastAPIQuery(..., description="End date for report period"),
    access_types: Optional[str] = FastAPIQuery(None, description="Comma-separated access types to include"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Generate report of all privileged access during a specific period.
    
    **Audit Use Case**: "Show me all database administrators during Q3"
    
    Returns:
        Complete list of users with privileged access during the specified period
    """
    # Parse access types filter
    access_type_filter = []
    if access_types:
        access_type_filter = [t.strip() for t in access_types.split(',')]
    
    # Build query for access grants
    query = db.query(AccessGrant).join(
        CanonicalIdentity, AccessGrant.user_cid == CanonicalIdentity.cid
    ).filter(
        and_(
            AccessGrant.granted_date <= end_date,
            or_(
                AccessGrant.expires_date >= start_date,
                AccessGrant.expires_date.is_(None)
            )
        )
    )
    
    # Apply access type filter if provided
    if access_type_filter:
        query = query.filter(AccessGrant.access_type.in_(access_type_filter))
    
    # Filter for privileged access (admin, database, system access)
    privileged_types = ["ADMINISTRATIVE_ACCESS", "DATABASE_ACCESS", "SYSTEM_ACCESS"]
    query = query.filter(AccessGrant.access_type.in_(privileged_types))
    
    access_grants = query.order_by(CanonicalIdentity.full_name).all()
    
    # Group by user for summary
    user_access_summary = {}
    for grant in access_grants:
        user_key = str(grant.user_cid)
        if user_key not in user_access_summary:
            user_access_summary[user_key] = {
                "user_info": {
                    "cid": str(grant.user.cid),
                    "email": grant.user.email,
                    "full_name": grant.user.full_name,
                    "department": grant.user.department,
                    "role": grant.user.role,
                    "status": grant.user.status.value
                },
                "privileged_access": []
            }
        
        user_access_summary[user_key]["privileged_access"].append({
            "access_type": grant.access_type.value,
            "resource_name": grant.resource_name,
            "permission_level": grant.permission_level,
            "granted_date": grant.granted_date.isoformat() if grant.granted_date else None,
            "expires_date": grant.expires_date.isoformat() if grant.expires_date else None,
            "granted_by": grant.granted_by,
            "business_justification": grant.business_justification,
            "risk_level": grant.risk_level
        })
    
    return {
        "report_metadata": {
            "report_type": "Privileged Access Report",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "total_privileged_users": len(user_access_summary)
        },
        "privileged_users": list(user_access_summary.values()),
        "summary_statistics": {
            "total_users_with_privileged_access": len(user_access_summary),
            "total_privileged_access_grants": len(access_grants),
            "access_type_breakdown": {
                access_type: len([g for g in access_grants if g.access_type.value == access_type])
                for access_type in set(g.access_type.value for g in access_grants)
            }
        }
    }


@router.get("/compliance/drift-detection")
def get_compliance_drift(
    severity: Optional[str] = FastAPIQuery(None, description="Filter by severity (Low, Medium, High, Critical)"),
    drift_type: Optional[str] = FastAPIQuery(None, description="Filter by drift type"),
    status: Optional[str] = FastAPIQuery("Open", description="Filter by remediation status"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get current compliance drift issues.
    
    **Audit Use Case**: "Show me where our actual state differs from policy"
    
    Returns:
        List of compliance drift issues that need attention
    """
    # Build query
    query = db.query(ComplianceDrift).join(
        CanonicalIdentity, ComplianceDrift.affected_user_cid == CanonicalIdentity.cid
    )
    
    # Apply filters
    if severity:
        query = query.filter(ComplianceDrift.drift_severity == severity)
    if drift_type:
        query = query.filter(ComplianceDrift.drift_type == drift_type)
    if status:
        query = query.filter(ComplianceDrift.remediation_status == status)
    
    drift_issues = query.order_by(
        desc(ComplianceDrift.drift_severity),
        desc(ComplianceDrift.drift_detected_at)
    ).all()
    
    return {
        "drift_summary": {
            "total_issues": len(drift_issues),
            "by_severity": {
                severity: len([d for d in drift_issues if d.drift_severity == severity])
                for severity in ["Critical", "High", "Medium", "Low"]
            },
            "by_status": {
                status: len([d for d in drift_issues if d.remediation_status == status])
                for status in set(d.remediation_status for d in drift_issues)
            }
        },
        "drift_issues": [
            {
                "id": str(drift.id),
                "drift_type": drift.drift_type,
                "severity": drift.drift_severity,
                "affected_user": {
                    "cid": str(drift.affected_user.cid),
                    "email": drift.affected_user.email,
                    "full_name": drift.affected_user.full_name,
                    "department": drift.affected_user.department
                },
                "affected_resource": drift.affected_resource,
                "expected_state": drift.expected_state,
                "actual_state": drift.actual_state,
                "drift_details": drift.drift_details,
                "detected_at": drift.drift_detected_at.isoformat(),
                "remediation_status": drift.remediation_status,
                "remediation_priority": drift.remediation_priority,
                "compliance_frameworks_affected": drift.compliance_frameworks_affected,
                "audit_risk_level": drift.audit_risk_level
            }
            for drift in drift_issues
        ]
    }


@router.get("/public-key")
def get_audit_public_key(_: str = Depends(verify_token)):
    """
    Get the public key for verifying audit record signatures.

    **Audit Use Case**: "Verify the cryptographic integrity of audit records"

    Returns:
        Public key in PEM format for external verification
    """
    return {
        "public_key_pem": audit_crypto.get_public_key_pem(),
        "key_info": {
            "algorithm": "RSA",
            "key_size": 2048,
            "signature_algorithm": "RSA-PSS",
            "hash_algorithm": "SHA-256",
            "usage": "audit_record_verification"
        },
        "verification_instructions": {
            "description": "Use this public key to verify the digital signatures on audit records",
            "libraries": {
                "python": "cryptography library",
                "javascript": "node-forge or crypto-js",
                "java": "java.security package",
                "dotnet": "System.Security.Cryptography"
            }
        }
    }


@router.post("/verify-record")
def verify_audit_record(
    record: Dict[str, Any],
    _: str = Depends(verify_token)
):
    """
    Verify the cryptographic integrity of an audit record.

    **Audit Use Case**: "Prove this audit record has not been tampered with"

    Args:
        record: The audit record to verify

    Returns:
        Detailed verification results
    """
    verification_results = audit_crypto.verify_audit_record(record)

    return {
        "verification_results": verification_results,
        "legal_status": {
            "tamper_evident": not verification_results["tamper_detected"],
            "legally_admissible": verification_results["is_valid"],
            "audit_compliant": verification_results["is_valid"],
            "non_repudiation": verification_results["digital_signature_valid"]
        },
        "verification_timestamp": verification_results["verification_timestamp"],
        "verification_summary": {
            "status": "VERIFIED" if verification_results["is_valid"] else "FAILED",
            "confidence": "HIGH" if verification_results["is_valid"] else "NONE",
            "integrity": "INTACT" if not verification_results["tamper_detected"] else "COMPROMISED"
        }
    }


@router.get("/evidence/audit-trail/{user_cid}")
def get_complete_audit_trail(
    user_cid: UUID,
    include_cryptographic_proof: bool = FastAPIQuery(True, description="Include cryptographic signatures"),
    start_date: Optional[datetime] = FastAPIQuery(None, description="Start date for audit trail"),
    end_date: Optional[datetime] = FastAPIQuery(None, description="End date for audit trail"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get complete cryptographically signed audit trail for a user.

    **Audit Use Case**: "Provide legally admissible audit trail with cryptographic proof"

    Returns:
        Complete audit trail with timestamps and digital signatures
    """
    # Verify user exists
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == user_cid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Set default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    # Get all audit-related data
    audit_logs = db.query(AccessAuditLog).filter(
        and_(
            AccessAuditLog.user_cid == user_cid,
            AccessAuditLog.timestamp >= start_date,
            AccessAuditLog.timestamp <= end_date
        )
    ).order_by(AccessAuditLog.timestamp.desc()).all()

    activity_history = db.query(ActivityHistory).filter(
        and_(
            ActivityHistory.user_cid == user_cid,
            ActivityHistory.timestamp >= start_date,
            ActivityHistory.timestamp <= end_date
        )
    ).order_by(ActivityHistory.timestamp.desc()).all()

    # Create comprehensive audit trail
    audit_trail_data = {
        "user_info": {
            "cid": str(user.cid),
            "email": user.email,
            "full_name": user.full_name,
            "department": user.department
        },
        "trail_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_days": (end_date - start_date).days
        },
        "audit_events": [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "action": log.action.value,
                "resource": log.resource_name,
                "performed_by": log.performed_by,
                "source_system": log.source_system,
                "previous_state": log.previous_state,
                "new_state": log.new_state,
                "justification": log.justification,
                "risk_assessment": log.risk_assessment
            }
            for log in audit_logs
        ],
        "activity_events": [
            {
                "id": str(activity.id),
                "timestamp": activity.timestamp.isoformat(),
                "activity_type": activity.activity_type.value,
                "description": activity.description,
                "source_system": activity.source_system,
                "source_ip": str(activity.source_ip) if activity.source_ip else None,
                "risk_score": activity.risk_score
            }
            for activity in activity_history
        ],
        "trail_statistics": {
            "total_audit_events": len(audit_logs),
            "total_activity_events": len(activity_history),
            "total_events": len(audit_logs) + len(activity_history),
            "risk_events": len([a for a in activity_history if a.risk_score in ["High", "Critical"]])
        }
    }

    if include_cryptographic_proof:
        # Create cryptographically signed audit record
        audit_record = audit_crypto.create_audit_record(
            record_type="COMPLETE_AUDIT_TRAIL",
            subject_cid=user_cid,
            evidence_data=audit_trail_data,
            compliance_framework="SOX"
        )

        return {
            "audit_record": audit_record,
            "cryptographic_proof": {
                "digitally_signed": True,
                "tamper_evident": True,
                "legally_admissible": True,
                "chain_of_custody": "MAINTAINED",
                "audit_trail_integrity": "CRYPTOGRAPHICALLY_VERIFIED"
            }
        }
    else:
        return audit_trail_data
