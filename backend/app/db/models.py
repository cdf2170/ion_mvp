from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
import hashlib
import hmac
from datetime import datetime


Base = declarative_base()


class StatusEnum(enum.Enum):
    ACTIVE = "Active"
    DISABLED = "Disabled"


class DeviceStatusEnum(enum.Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    UNKNOWN = "Unknown"


class AgentStatusEnum(enum.Enum):
    INSTALLED = "Installed"
    RUNNING = "Running"
    STOPPED = "Stopped"
    ERROR = "Error"
    UPDATING = "Updating"
    UNINSTALLED = "Uninstalled"


class DeviceTagEnum(enum.Enum):
    REMOTE = "Remote"
    ON_SITE = "On-Site"
    EXECUTIVE = "Executive"
    SLT = "SLT"
    FULL_TIME = "Full-Time"
    CONTRACT = "Contract"
    BYOD = "BYOD"
    CORPORATE = "Corporate"
    VIP = "VIP"
    TESTING = "Testing"
    PRODUCTION = "Production"


class AccessTypeEnum(enum.Enum):
    """Types of access that can be granted"""
    SYSTEM_ACCESS = "System Access"
    APPLICATION_ACCESS = "Application Access"
    DATA_ACCESS = "Data Access"
    NETWORK_ACCESS = "Network Access"
    PHYSICAL_ACCESS = "Physical Access"
    ADMINISTRATIVE_ACCESS = "Administrative Access"
    API_ACCESS = "API Access"
    DATABASE_ACCESS = "Database Access"


class AccessStatusEnum(enum.Enum):
    """Current status of access grants"""
    ACTIVE = "Active"
    REVOKED = "Revoked"
    EXPIRED = "Expired"
    SUSPENDED = "Suspended"
    PENDING_APPROVAL = "Pending Approval"
    PENDING_REVOCATION = "Pending Revocation"


class AccessReasonEnum(enum.Enum):
    """Reasons for access grants/revocations"""
    # Grant reasons
    JOB_REQUIREMENT = "Job Requirement"
    PROJECT_ASSIGNMENT = "Project Assignment"
    TEMPORARY_ASSIGNMENT = "Temporary Assignment"
    ROLE_CHANGE = "Role Change"
    EMERGENCY_ACCESS = "Emergency Access"
    CONTRACTOR_ACCESS = "Contractor Access"
    
    # Revocation reasons
    EMPLOYMENT_TERMINATED = "Employment Terminated"
    ROLE_CHANGED = "Role Changed"
    PROJECT_COMPLETED = "Project Completed"
    ACCESS_NO_LONGER_NEEDED = "Access No Longer Needed"
    SECURITY_VIOLATION = "Security Violation"
    POLICY_VIOLATION = "Policy Violation"
    EXPIRED_ACCESS = "Expired Access"
    ADMIN_REVOCATION = "Administrative Revocation"


class AuditActionEnum(enum.Enum):
    """Types of audit actions"""
    ACCESS_GRANTED = "Access Granted"
    ACCESS_REVOKED = "Access Revoked"
    ACCESS_MODIFIED = "Access Modified"
    ACCESS_SUSPENDED = "Access Suspended"
    ACCESS_RESTORED = "Access Restored"
    ACCESS_REVIEWED = "Access Reviewed"
    ACCESS_EXPIRED = "Access Expired"
    EMERGENCY_ACCESS = "Emergency Access"
    BULK_ACCESS_CHANGE = "Bulk Access Change"


class CanonicalIdentity(Base):
    __tablename__ = "canonical_identities"
    
    cid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True)
    department = Column(String, nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.ACTIVE)
    
    # Additional personal info
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    manager = Column(String)
    location = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMembership", back_populates="identity", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="identity", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    compliant = Column(Boolean, nullable=False, default=True)
    owner_cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"), nullable=False)

    # Network information
    ip_address = Column(INET)
    mac_address = Column(String(17))  # MAC format: XX:XX:XX:XX:XX:XX
    vlan = Column(String)

    # System information
    os_version = Column(String)
    last_check_in = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(DeviceStatusEnum), nullable=False, default=DeviceStatusEnum.UNKNOWN)

    # Agent-specific fields
    # TEMP_COMMENTED: # TEMP_COMMENTED: agent_installed = Column(Boolean, nullable=False, default=False)
    # TEMP_COMMENTED: # TEMP_COMMENTED: agent_version = Column(String)
    # TEMP_COMMENTED: # TEMP_COMMENTED: agent_status = Column(SQLEnum(AgentStatusEnum))
    # TEMP_COMMENTED: # TEMP_COMMENTED: agent_last_checkin = Column(DateTime(timezone=True))
    # TEMP_COMMENTED: # TEMP_COMMENTED: agent_config_hash = Column(String)  # Hash of agent configuration

    # Hardware fingerprinting for correlation
    # TEMP_COMMENTED: # TEMP_COMMENTED: hardware_uuid = Column(String)  # Windows: Get-WmiObject Win32_ComputerSystemProduct | Select-Object UUID
    # TEMP_COMMENTED: # TEMP_COMMENTED: motherboard_serial = Column(String)  # Additional hardware identifier
    # TEMP_COMMENTED: # TEMP_COMMENTED: cpu_id = Column(String)  # CPU identifier

    # Real-time agent data (JSONB for flexibility)
    # TEMP_COMMENTED: # TEMP_COMMENTED: agent_data = Column(JSON)  # Real-time system state, processes, etc.

    # Relationships
    owner = relationship("CanonicalIdentity", back_populates="devices")
    tags = relationship("DeviceTag", back_populates="device", cascade="all, delete-orphan")
    # TEMP_COMMENTED: # TEMP_COMMENTED: agent_events = relationship("AgentEvent", back_populates="device", cascade="all, delete-orphan")


class DeviceTag(Base):
    __tablename__ = "device_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    tag = Column(SQLEnum(DeviceTagEnum), nullable=False)

    # Relationships
    device = relationship("Device", back_populates="tags")


class AgentEventTypeEnum(enum.Enum):
    """Temporary stub to prevent import errors"""
    TEMP_STUB = "Temporary Stub"


# TEMP_COMMENTED: AgentEvent class completely removed


class GroupTypeEnum(enum.Enum):
    DEPARTMENT = "Department"
    ROLE = "Role"
    ACCESS_LEVEL = "Access Level"
    LOCATION = "Location"
    PROJECT = "Project"
    SECURITY_CLEARANCE = "Security Clearance"
    EMPLOYMENT_TYPE = "Employment Type"
    TEAM = "Team"


class GroupMembership(Base):
    __tablename__ = "group_memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"), nullable=False)
    group_name = Column(String, nullable=False)
    group_type = Column(SQLEnum(GroupTypeEnum), nullable=False, default=GroupTypeEnum.TEAM)
    description = Column(String)  # Optional description of what this group is for
    source_system = Column(String)  # Which system this group came from (Okta, AD, etc.)
    
    # Relationships
    identity = relationship("CanonicalIdentity", back_populates="group_memberships")


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service = Column(String, nullable=False)
    status = Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.ACTIVE)
    user_email = Column(String, nullable=False)
    cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"), nullable=False)
    
    # Relationships
    identity = relationship("CanonicalIdentity", back_populates="accounts")


class PolicyTypeEnum(enum.Enum):
    ACCESS_CONTROL = "Access Control"
    PASSWORD_POLICY = "Password Policy"
    DEVICE_COMPLIANCE = "Device Compliance"
    DATA_CLASSIFICATION = "Data Classification"
    NETWORK_SECURITY = "Network Security"
    BACKUP_RETENTION = "Backup Retention"


class PolicySeverityEnum(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    policy_type = Column(SQLEnum(PolicyTypeEnum), nullable=False)
    severity = Column(SQLEnum(PolicySeverityEnum), nullable=False, default=PolicySeverityEnum.MEDIUM)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String)  # User who created the policy
    
    # Policy configuration as JSON text
    configuration = Column(Text)  # Store JSON configuration


class ConfigChangeTypeEnum(enum.Enum):
    CREATED = "Created"
    UPDATED = "Updated"
    DELETED = "Deleted"
    ENABLED = "Enabled"
    DISABLED = "Disabled"


class ConfigHistory(Base):
    __tablename__ = "config_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String, nullable=False)  # "user", "device", "policy", etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    change_type = Column(SQLEnum(ConfigChangeTypeEnum), nullable=False)
    field_name = Column(String)  # Which field was changed
    old_value = Column(Text)  # Previous value (JSON if complex)
    new_value = Column(Text)  # New value (JSON if complex)
    changed_by = Column(String)  # User who made the change
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(Text)  # Human-readable description of change


class ActivityTypeEnum(enum.Enum):
    LOGIN = "Login"
    LOGOUT = "Logout"
    ACCESS_GRANTED = "Access Granted"
    ACCESS_DENIED = "Access Denied"
    POLICY_VIOLATION = "Policy Violation"
    DEVICE_CONNECTED = "Device Connected"
    DEVICE_DISCONNECTED = "Device Disconnected"
    COMPLIANCE_SCAN = "Compliance Scan"
    DATA_ACCESS = "Data Access"
    CONFIGURATION_CHANGE = "Configuration Change"


class ActivityHistory(Base):
    __tablename__ = "activity_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"))
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"))
    activity_type = Column(SQLEnum(ActivityTypeEnum), nullable=False)
    source_system = Column(String)  # Which system generated this activity
    source_ip = Column(INET)
    user_agent = Column(String)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional context as JSON
    activity_metadata = Column(Text)  # Store additional context as JSON
    
    # Risk scoring
    risk_score = Column(String)  # Low/Medium/High/Critical
    
    # Relationships
    user = relationship("CanonicalIdentity")
    device = relationship("Device")


class APIProviderEnum(enum.Enum):
    OKTA = "Okta"
    WORKDAY = "Workday"
    CROWDSTRIKE = "CrowdStrike"
    CYBERARK = "CyberArk"
    SPLUNK = "Splunk"
    SAILPOINT = "SailPoint"
    MICROSOFT_365 = "Microsoft 365"
    AZURE_AD = "Azure AD"
    AWS_IAM = "AWS IAM"
    GOOGLE_WORKSPACE = "Google Workspace"
    SLACK = "Slack"
    JIRA = "Jira"
    CONFLUENCE = "Confluence"
    SERVICENOW = "ServiceNow"
    PING_IDENTITY = "Ping Identity"
    CUSTOM = "Custom"


class APIConnectionStatusEnum(enum.Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    ERROR = "Error"
    TESTING = "Testing"
    DISABLED = "Disabled"
    AUTHENTICATING = "Authenticating"
    RATE_LIMITED = "Rate Limited"
    MAINTENANCE = "Maintenance"


class APIConnectionTagEnum(enum.Enum):
    PRODUCTION = "Production"
    STAGING = "Staging"
    DEVELOPMENT = "Development"
    TESTING = "Testing"
    CRITICAL = "Critical"
    NON_CRITICAL = "Non-Critical"
    REAL_TIME = "Real-Time"
    BATCH_ONLY = "Batch Only"
    HIGH_VOLUME = "High Volume"
    LOW_VOLUME = "Low Volume"
    IDENTITY_SOURCE = "Identity Source"
    DEVICE_SOURCE = "Device Source"
    SECURITY_TOOL = "Security Tool"
    HR_SYSTEM = "HR System"
    IT_SYSTEM = "IT System"


class APIConnection(Base):
    __tablename__ = "api_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # User-friendly name
    provider = Column(SQLEnum(APIProviderEnum), nullable=False)
    description = Column(Text)
    
    # Connection details
    base_url = Column(String, nullable=False)
    api_version = Column(String)
    authentication_type = Column(String, nullable=False)  # oauth2, api_key, basic, etc.
    
    # Encrypted credentials (stored as JSON)
    credentials = Column(Text)  # Encrypted JSON with API keys, tokens, etc.
    
    # Configuration
    sync_enabled = Column(Boolean, nullable=False, default=True)
    sync_interval_minutes = Column(String, default="60")  # How often to sync
    last_sync = Column(DateTime(timezone=True))
    next_sync = Column(DateTime(timezone=True))
    
    # Status and health
    status = Column(SQLEnum(APIConnectionStatusEnum), nullable=False, default=APIConnectionStatusEnum.TESTING)
    last_health_check = Column(DateTime(timezone=True))
    health_check_message = Column(Text)
    connection_test_url = Column(String)  # Specific endpoint to test connection
    
    # Rate limiting
    rate_limit_requests = Column(String)  # requests per minute/hour
    rate_limit_window = Column(String)  # minute/hour
    
    # Data mapping configuration
    field_mappings = Column(Text)  # JSON configuration for field mapping
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String)
    updated_by = Column(String)
    
    # Capabilities (what this API can do)
    supports_users = Column(Boolean, default=True)
    supports_devices = Column(Boolean, default=False)
    supports_groups = Column(Boolean, default=True)
    supports_realtime = Column(Boolean, default=False)
    
    # Relationships
    tags = relationship("APIConnectionTag", back_populates="connection", cascade="all, delete-orphan")


class APIConnectionTag(Base):
    __tablename__ = "api_connection_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("api_connections.id"), nullable=False)
    tag = Column(SQLEnum(APIConnectionTagEnum), nullable=False)
    
    # Relationships
    connection = relationship("APIConnection", back_populates="tags")


class APISyncLog(Base):
    __tablename__ = "api_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("api_connections.id"), nullable=False)
    
    # Sync details
    sync_type = Column(String, nullable=False)  # full, incremental, manual
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(String)
    
    # Results
    status = Column(String, nullable=False)  # success, error, partial
    records_processed = Column(String, default="0")
    records_created = Column(String, default="0")
    records_updated = Column(String, default="0")
    records_failed = Column(String, default="0")
    
    # Error details
    error_message = Column(Text)
    error_details = Column(Text)  # Stack trace, detailed error info
    
    # Relationships
    connection = relationship("APIConnection")


class AccessGrant(Base):
    """
    Core access grants table - tracks all access permissions granted to users.
    This is the primary table for current access state.
    """
    __tablename__ = "access_grants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who has access
    user_cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"), nullable=False)
    
    # What access
    access_type = Column(SQLEnum(AccessTypeEnum), nullable=False)
    resource_name = Column(String, nullable=False)  # e.g., "Production Database", "AWS Console", "Slack Admin"
    resource_identifier = Column(String)  # e.g., server hostname, app ID, etc.
    
    # Access details
    access_level = Column(String, nullable=False)  # e.g., "Read", "Write", "Admin", "Full Control"
    permissions = Column(JSON)  # Detailed permissions object
    
    # Why access was granted
    reason = Column(SQLEnum(AccessReasonEnum), nullable=False)
    justification = Column(Text)  # Free text explanation
    business_justification = Column(Text)  # Business case for access
    
    # When
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # NULL for permanent access
    effective_start = Column(DateTime(timezone=True))  # For future-scheduled access
    
    # Who granted it
    granted_by = Column(String, nullable=False)  # User who approved/granted
    approved_by = Column(String)  # Manager/system who approved (if different)
    source_system = Column(String)  # System that granted access (e.g., "Active Directory", "Manual")
    
    # Current status
    status = Column(SQLEnum(AccessStatusEnum), nullable=False, default=AccessStatusEnum.ACTIVE)
    
    # Revocation info (filled when revoked)
    revoked_at = Column(DateTime(timezone=True))
    revoked_by = Column(String)
    revocation_reason = Column(SQLEnum(AccessReasonEnum))
    revocation_justification = Column(Text)
    
    # Review tracking
    last_reviewed_at = Column(DateTime(timezone=True))
    last_reviewed_by = Column(String)
    next_review_due = Column(DateTime(timezone=True))
    
    # Emergency access tracking
    is_emergency_access = Column(Boolean, default=False)
    emergency_ticket = Column(String)  # Emergency ticket number
    emergency_approver = Column(String)
    
    # Risk and compliance
    risk_level = Column(String)  # "Low", "Medium", "High", "Critical"
    compliance_tags = Column(JSON)  # SOX, PCI, GDPR, etc.
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("CanonicalIdentity")
    audit_logs = relationship("AccessAuditLog", back_populates="access_grant", cascade="all, delete-orphan")


class AccessAuditLog(Base):
    """
    Immutable audit log for all access-related actions.
    Each record is cryptographically signed to prevent tampering.
    """
    __tablename__ = "access_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to access grant (if applicable)
    access_grant_id = Column(UUID(as_uuid=True), ForeignKey("access_grants.id"))
    
    # Core audit info
    user_cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"), nullable=False)
    action = Column(SQLEnum(AuditActionEnum), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # What was acted upon
    resource_name = Column(String, nullable=False)
    resource_identifier = Column(String)
    access_type = Column(SQLEnum(AccessTypeEnum), nullable=False)
    access_level = Column(String)
    
    # Context of the action
    performed_by = Column(String, nullable=False)  # Who performed the action
    reason = Column(SQLEnum(AccessReasonEnum))
    justification = Column(Text)
    
    # Before/after state for modifications
    previous_state = Column(JSON)  # Previous access state
    new_state = Column(JSON)  # New access state
    
    # Additional context
    source_system = Column(String)
    ip_address = Column(INET)
    user_agent = Column(String)
    session_id = Column(String)
    request_id = Column(String)  # For tracing across systems
    
    # Emergency/special circumstances
    is_emergency = Column(Boolean, default=False)
    emergency_ticket = Column(String)
    emergency_approver = Column(String)
    
    # Compliance and risk info
    compliance_tags = Column(JSON)
    risk_assessment = Column(String)
    
    # Cryptographic integrity
    record_hash = Column(String, nullable=False)  # SHA-256 hash of record
    previous_hash = Column(String)  # Hash of previous record for chaining
    signature = Column(String)  # HMAC signature for integrity
    
    # Immutability enforcement
    is_sealed = Column(Boolean, default=False)  # Once sealed, cannot be modified
    sealed_at = Column(DateTime(timezone=True))
    sealed_by = Column(String)
    
    # Relationships
    user = relationship("CanonicalIdentity")
    access_grant = relationship("AccessGrant", back_populates="audit_logs")
    
    def generate_record_hash(self):
        """Generate SHA-256 hash of the record for integrity verification"""
        # Create a deterministic string representation of the record
        record_data = {
            'id': str(self.id),
            'user_cid': str(self.user_cid),
            'action': self.action.value if self.action else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'resource_name': self.resource_name,
            'access_type': self.access_type.value if self.access_type else None,
            'performed_by': self.performed_by,
            'previous_state': self.previous_state,
            'new_state': self.new_state
        }
        
        # Sort keys for deterministic hash
        record_string = str(sorted(record_data.items()))
        return hashlib.sha256(record_string.encode()).hexdigest()
    
    def generate_signature(self, secret_key: str):
        """Generate HMAC signature for the record"""
        if not self.record_hash:
            self.record_hash = self.generate_record_hash()
        
        return hmac.new(
            secret_key.encode(),
            self.record_hash.encode(),
            hashlib.sha256
        ).hexdigest()


class AccessReview(Base):
    """
    Tracks access reviews and certifications - critical for compliance.
    """
    __tablename__ = "access_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Review details
    review_period_start = Column(DateTime(timezone=True), nullable=False)
    review_period_end = Column(DateTime(timezone=True), nullable=False)
    review_type = Column(String, nullable=False)  # "Quarterly", "Annual", "Ad-hoc", "Emergency"
    
    # Scope
    scope_description = Column(Text)
    users_in_scope = Column(JSON)  # List of user CIDs
    systems_in_scope = Column(JSON)  # List of systems/resources
    
    # Review status
    status = Column(String, nullable=False)  # "In Progress", "Completed", "Overdue"
    completion_percentage = Column(Integer, default=0)
    
    # Reviewers
    primary_reviewer = Column(String, nullable=False)
    secondary_reviewers = Column(JSON)  # List of additional reviewers
    
    # Results
    total_access_reviewed = Column(Integer, default=0)
    access_certified = Column(Integer, default=0)
    access_revoked = Column(Integer, default=0)
    access_flagged = Column(Integer, default=0)
    
    # Findings
    findings = Column(JSON)  # Detailed findings and recommendations
    exceptions = Column(JSON)  # Approved exceptions
    
    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    
    # Compliance
    compliance_framework = Column(String)  # SOX, PCI, ISO27001, etc.
    auditor_notes = Column(Text)
    
    # Audit trail
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AccessPattern(Base):
    """
    Machine learning insights into access patterns for anomaly detection.
    """
    __tablename__ = "access_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Pattern details
    user_cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"), nullable=False)
    resource_name = Column(String, nullable=False)
    
    # Pattern metrics
    access_frequency = Column(String)  # "Daily", "Weekly", "Monthly", "Rare"
    typical_access_times = Column(JSON)  # Time patterns
    typical_access_duration = Column(String)  # Average session length
    access_locations = Column(JSON)  # Geographic/network patterns
    
    # Risk scoring
    risk_score = Column(Integer)  # 0-100 risk score
    anomaly_indicators = Column(JSON)  # List of unusual behaviors
    
    # ML model info
    model_version = Column(String)
    confidence_score = Column(String)  # Model confidence in the pattern
    
    # Timing
    pattern_period_start = Column(DateTime(timezone=True))
    pattern_period_end = Column(DateTime(timezone=True))
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("CanonicalIdentity")


# ============================================================================
# AUDIT INSURANCE MODELS - The "Prove It" System
# ============================================================================

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
