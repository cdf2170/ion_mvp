from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum


Base = declarative_base()


class StatusEnum(enum.Enum):
    ACTIVE = "Active"
    DISABLED = "Disabled"


class DeviceStatusEnum(enum.Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    UNKNOWN = "Unknown"


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
    
    # Relationships
    owner = relationship("CanonicalIdentity", back_populates="devices")
    tags = relationship("DeviceTag", back_populates="device", cascade="all, delete-orphan")


class DeviceTag(Base):
    __tablename__ = "device_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    tag = Column(SQLEnum(DeviceTagEnum), nullable=False)
    
    # Relationships
    device = relationship("Device", back_populates="tags")


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
