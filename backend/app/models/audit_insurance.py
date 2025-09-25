"""
Audit Insurance Models - The "Prove It" System

These models provide comprehensive audit trails and evidence generation
for compliance frameworks like SOX, PCI, HIPAA, GDPR, etc.

All models link back to CanonicalIdentity (CID) as the single source of truth.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime

from backend.app.db.models import Base


class AuditSnapshotTypeEnum(enum.Enum):
    """Types of audit snapshots we can take"""
    DAILY_SNAPSHOT = "Daily Snapshot"
    WEEKLY_SNAPSHOT = "Weekly Snapshot"
    MONTHLY_SNAPSHOT = "Monthly Snapshot"
    QUARTERLY_SNAPSHOT = "Quarterly Snapshot"
    ANNUAL_SNAPSHOT = "Annual Snapshot"
    COMPLIANCE_SNAPSHOT = "Compliance Snapshot"
    INCIDENT_SNAPSHOT = "Incident Snapshot"
    TERMINATION_SNAPSHOT = "Termination Snapshot"
    AUDIT_REQUEST_SNAPSHOT = "Audit Request Snapshot"


class ComplianceFrameworkEnum(enum.Enum):
    """Compliance frameworks we support"""
    SOX = "Sarbanes-Oxley (SOX)"
    PCI_DSS = "PCI DSS"
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    ISO27001 = "ISO 27001"
    NIST = "NIST Cybersecurity Framework"
    FISMA = "FISMA"
    FEDRAMP = "FedRAMP"
    SOC2 = "SOC 2"
    CCPA = "CCPA"


class AuditSnapshot(Base):
    """
    Point-in-time snapshots of complete system state for audit purposes.
    
    This is the "time machine" that lets auditors see exactly what access
    existed at any point in time.
    """
    __tablename__ = "audit_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Snapshot metadata
    snapshot_type = Column(String, nullable=False)  # From AuditSnapshotTypeEnum
    snapshot_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text)
    
    # Compliance context
    compliance_frameworks = Column(JSON)  # List of applicable frameworks
    audit_period_start = Column(DateTime(timezone=True))
    audit_period_end = Column(DateTime(timezone=True))
    
    # Snapshot data (JSON for flexibility)
    user_access_snapshot = Column(JSON)  # Complete user access at this point
    device_compliance_snapshot = Column(JSON)  # Device compliance state
    group_membership_snapshot = Column(JSON)  # Group memberships
    policy_compliance_snapshot = Column(JSON)  # Policy compliance state
    
    # Statistics for quick reference
    total_users = Column(Integer)
    total_devices = Column(Integer)
    total_access_grants = Column(Integer)
    compliance_violations = Column(Integer)
    
    # Audit trail
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Integrity verification
    snapshot_hash = Column(String, nullable=False)  # SHA-256 of snapshot data
    is_sealed = Column(Boolean, default=True)  # Immutable once sealed


class AuditEvidence(Base):
    """
    Specific pieces of evidence that auditors request.
    
    This table stores pre-generated evidence for common audit questions
    like "Prove user X never had admin access" or "Show all database admins in Q3".
    """
    __tablename__ = "audit_evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Evidence metadata
    evidence_type = Column(String, nullable=False)  # "USER_ACCESS_PROOF", "TERMINATION_PROOF", etc.
    evidence_title = Column(String, nullable=False)
    evidence_description = Column(Text, nullable=False)
    
    # Who/what this evidence is about
    subject_cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"))
    subject_resource = Column(String)  # System, application, or resource name
    
    # Time period this evidence covers
    evidence_period_start = Column(DateTime(timezone=True), nullable=False)
    evidence_period_end = Column(DateTime(timezone=True), nullable=False)
    
    # The actual evidence (JSON for flexibility)
    evidence_data = Column(JSON, nullable=False)
    
    # Compliance context
    compliance_framework = Column(String)  # Which framework this supports
    audit_question = Column(Text)  # The specific question this answers
    
    # Evidence integrity
    evidence_hash = Column(String, nullable=False)
    digital_signature = Column(String)  # Cryptographic signature
    
    # Audit trail
    generated_by = Column(String, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subject_user = relationship("CanonicalIdentity")


class ComplianceDrift(Base):
    """
    Tracks when reality drifts from policy - critical for audit findings.
    
    This identifies discrepancies between what should be and what actually is.
    """
    __tablename__ = "compliance_drift"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # What drifted
    drift_type = Column(String, nullable=False)  # "ACCESS_CREEP", "ORPHANED_ACCOUNT", etc.
    drift_severity = Column(String, nullable=False)  # "Low", "Medium", "High", "Critical"
    
    # Who is affected
    affected_user_cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"))
    affected_resource = Column(String, nullable=False)
    affected_system = Column(String)
    
    # What the drift is
    expected_state = Column(JSON)  # What should be according to policy
    actual_state = Column(JSON)    # What actually exists
    drift_details = Column(JSON)   # Detailed explanation of the drift
    
    # When it happened
    drift_detected_at = Column(DateTime(timezone=True), server_default=func.now())
    drift_first_occurred = Column(DateTime(timezone=True))  # When drift likely started
    
    # Remediation
    remediation_required = Column(Boolean, default=True)
    remediation_priority = Column(String)  # "Immediate", "High", "Medium", "Low"
    remediation_status = Column(String, default="Open")  # "Open", "In Progress", "Resolved", "Accepted Risk"
    remediation_notes = Column(Text)
    remediation_completed_at = Column(DateTime(timezone=True))
    
    # Compliance impact
    compliance_frameworks_affected = Column(JSON)  # List of frameworks this impacts
    audit_risk_level = Column(String)  # Risk level for audit findings
    
    # Relationships
    affected_user = relationship("CanonicalIdentity")


class AuditReport(Base):
    """
    Pre-generated audit reports for common compliance scenarios.
    
    These are the "one-click" reports that make auditors happy.
    """
    __tablename__ = "audit_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Report metadata
    report_type = Column(String, nullable=False)  # "SOX_QUARTERLY", "TERMINATION_AUDIT", etc.
    report_title = Column(String, nullable=False)
    report_description = Column(Text)
    
    # Report scope
    report_period_start = Column(DateTime(timezone=True), nullable=False)
    report_period_end = Column(DateTime(timezone=True), nullable=False)
    scope_users = Column(JSON)  # List of CIDs in scope
    scope_systems = Column(JSON)  # List of systems in scope
    
    # Report data
    report_data = Column(JSON, nullable=False)  # The actual report content
    executive_summary = Column(Text)
    key_findings = Column(JSON)
    recommendations = Column(JSON)
    
    # Compliance context
    compliance_framework = Column(String, nullable=False)
    auditor_requirements = Column(JSON)  # What the auditor specifically asked for
    
    # Report status
    status = Column(String, default="Generated")  # "Generated", "Reviewed", "Approved", "Delivered"
    
    # Audit trail
    generated_by = Column(String, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_by = Column(String)
    approved_at = Column(DateTime(timezone=True))
    
    # File references (for PDF/Excel exports)
    report_file_path = Column(String)
    report_file_hash = Column(String)


class HistoricalAccess(Base):
    """
    Historical view of user access for point-in-time queries.
    
    This enables questions like "What access did user X have on date Y?"
    """
    __tablename__ = "historical_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who had access
    user_cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"), nullable=False)
    
    # What access
    resource_name = Column(String, nullable=False)
    access_type = Column(String, nullable=False)
    permission_level = Column(String)
    
    # When they had it
    access_granted_date = Column(DateTime(timezone=True), nullable=False)
    access_revoked_date = Column(DateTime(timezone=True))  # NULL if still active
    
    # How they got it
    grant_reason = Column(String)
    granted_by = Column(String)
    approval_ticket = Column(String)
    
    # Source system
    source_system = Column(String, nullable=False)
    source_record_id = Column(String)
    
    # Compliance context
    compliance_tags = Column(JSON)
    risk_level = Column(String)
    
    # Relationships
    user = relationship("CanonicalIdentity")
