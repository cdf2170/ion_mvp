from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import re
import ipaddress
import json
from backend.app.db.models import (
    StatusEnum, DeviceStatusEnum, DeviceTagEnum, PolicyTypeEnum, 
    PolicySeverityEnum, ConfigChangeTypeEnum, ActivityTypeEnum,
    APIProviderEnum, APIConnectionStatusEnum, APIConnectionTagEnum,
    GroupTypeEnum
)


class DeviceTagSchema(BaseModel):
    """
    Device tag schema.
    
    Attributes:
        id: Unique tag identifier
        tag: Tag value (Remote, On-Site, Executive, etc.)
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique tag identifier")
    tag: DeviceTagEnum = Field(..., description="Tag value")


class DeviceSchema(BaseModel):
    """
    Device information schema for frontend consumption.
    
    Attributes:
        id: Unique device identifier
        name: Human-readable device name (e.g., "John's MacBook Pro")
        last_seen: Last time device was seen/active
        compliant: Whether device meets compliance requirements
        owner_cid: Canonical Identity of the device owner
        owner_name: Name of the device owner
        owner_email: Email of the device owner
        owner_department: Department of the device owner
        ip_address: Device IP address
        mac_address: Device MAC address
        vlan: VLAN identifier
        os_version: Operating system version
        last_check_in: Last time device checked in
        status: Connection status (Connected/Disconnected/Unknown)
        tags: List of device tags
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Human-readable device name")
    last_seen: datetime = Field(..., description="Last time device was seen/active")
    compliant: bool = Field(..., description="Whether device meets compliance requirements")
    owner_cid: UUID = Field(..., description="Canonical Identity of the device owner")
    owner_name: Optional[str] = Field(None, description="Name of the device owner")
    owner_email: Optional[str] = Field(None, description="Email of the device owner")
    owner_department: Optional[str] = Field(None, description="Department of the device owner")
    ip_address: Optional[str] = Field(None, description="Device IP address")
    mac_address: Optional[str] = Field(None, description="Device MAC address")
    vlan: Optional[str] = Field(None, description="VLAN identifier")
    os_version: Optional[str] = Field(None, description="Operating system version")
    last_check_in: datetime = Field(..., description="Last time device checked in")
    status: DeviceStatusEnum = Field(..., description="Connection status")
    tags: List[DeviceTagSchema] = Field(default=[], description="List of device tags")
    groups: List[str] = Field(default=[], description="Groups that the device owner belongs to")
    policies: List[str] = Field(default=[], description="Policies that apply to this device/user")
    
    @field_validator('ip_address', mode='before')
    @classmethod
    def validate_ip_address(cls, value):
        """Convert IPv4Address objects to strings"""
        if value is None:
            return None
        return str(value)


class GroupMembershipSchema(BaseModel):
    """
    User group membership schema with enhanced context.
    
    Attributes:
        id: Unique membership identifier
        group_name: Name of the group (e.g., "Engineering Team", "Senior Developers")
        group_type: Type/category of group (Department, Role, Access Level, etc.)
        description: Optional description of what this group is for
        source_system: Which system this group came from (Okta, AD, etc.)
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique membership identifier")
    group_name: str = Field(..., description="Name of the group")
    group_type: GroupTypeEnum = Field(..., description="Type/category of group")
    description: Optional[str] = Field(None, description="Description of what this group is for")
    source_system: Optional[str] = Field(None, description="Which system this group came from")


class AccountSchema(BaseModel):
    """
    External service account schema.
    
    Attributes:
        id: Unique account identifier
        service: Service name (e.g., "Slack", "AWS", "Microsoft 365")
        status: Account status (Active/Disabled)
        user_email: Email associated with this account
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique account identifier")
    service: str = Field(..., description="Service name (e.g., 'Slack', 'AWS')")
    status: StatusEnum = Field(..., description="Account status (Active/Disabled)")
    user_email: str = Field(..., description="Email associated with this account")


class UserListItemSchema(BaseModel):
    """
    Minimal user information for list views.
    
    Attributes:
        cid: Canonical Identity - unique user identifier across all systems
        email: Primary email address
        department: Department name
        last_seen: Last time user was active
        status: User status (Active/Disabled)
    """
    model_config = ConfigDict(from_attributes=True)
    
    cid: UUID = Field(..., description="Canonical Identity - unique user identifier")
    email: str = Field(..., description="Primary email address")
    department: str = Field(..., description="Department name")
    last_seen: datetime = Field(..., description="Last time user was active")
    status: StatusEnum = Field(..., description="User status (Active/Disabled)")


class UserDetailSchema(BaseModel):
    """
    Complete user information including all related data.
    
    Attributes:
        cid: Canonical Identity - unique user identifier across all systems
        email: Primary email address
        full_name: User's full name
        department: Department name
        role: Job title/role
        manager: Manager's name (if any)
        location: Physical location
        last_seen: Last time user was active
        status: User status (Active/Disabled)
        created_at: When user record was created
        devices: List of user's devices
        groups: List of group memberships
        accounts: List of external service accounts
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Personal info
    cid: UUID = Field(..., description="Canonical Identity - unique user identifier")
    email: str = Field(..., description="Primary email address")
    full_name: str = Field(..., description="User's full name")
    department: str = Field(..., description="Department name")
    role: str = Field(..., description="Job title/role")
    manager: Optional[str] = Field(None, description="Manager's name")
    location: Optional[str] = Field(None, description="Physical location")
    last_seen: datetime = Field(..., description="Last time user was active")
    status: StatusEnum = Field(..., description="User status (Active/Disabled)")
    created_at: datetime = Field(..., description="When user record was created")
    
    # Related data
    devices: List[DeviceSchema] = Field(default=[], description="List of user's devices")
    groups: List[GroupMembershipSchema] = Field(default=[], description="List of group memberships")
    accounts: List[AccountSchema] = Field(default=[], description="List of external service accounts")


class UserListResponse(BaseModel):
    """
    Paginated response for user list endpoint.
    
    Attributes:
        users: List of users for current page
        total: Total number of users matching filters
        page: Current page number (1-based)
        page_size: Number of items per page
        total_pages: Total number of pages
    """
    users: List[UserListItemSchema] = Field(..., description="List of users for current page")
    total: int = Field(..., description="Total number of users matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


class ScanResultSchema(BaseModel):
    """
    Result of a compliance scan operation.
    
    Attributes:
        cid: User's canonical identity
        message: Human-readable scan result message
        devices_scanned: Number of devices that were scanned
        compliance_changes: Number of devices that changed compliance status
    """
    cid: UUID = Field(..., description="User's canonical identity")
    message: str = Field(..., description="Human-readable scan result message")
    devices_scanned: int = Field(..., description="Number of devices that were scanned")
    compliance_changes: int = Field(..., description="Number of devices that changed compliance status")


# New schemas for identity and device management
class IdentityMergeRequest(BaseModel):
    """
    Request to merge two user identities.
    
    Attributes:
        source_cid: CID of user to merge FROM (will be deleted)
        target_cid: CID of user to merge TO (will retain data)
        merge_devices: Whether to transfer devices from source to target
        merge_accounts: Whether to transfer accounts from source to target
        merge_groups: Whether to transfer group memberships from source to target
    """
    source_cid: UUID = Field(..., description="CID of user to merge FROM (will be deleted)")
    target_cid: UUID = Field(..., description="CID of user to merge TO (will retain data)")
    merge_devices: bool = Field(True, description="Whether to transfer devices from source to target")
    merge_accounts: bool = Field(True, description="Whether to transfer accounts from source to target")
    merge_groups: bool = Field(True, description="Whether to transfer group memberships from source to target")


class IdentityUpdateRequest(BaseModel):
    """
    Request to update user identity information.
    
    Attributes:
        email: New email address
        full_name: New full name
        department: New department
        role: New role/title
        manager: New manager name
        location: New location
        status: New status
    """
    email: Optional[str] = Field(None, description="New email address")
    full_name: Optional[str] = Field(None, description="New full name")
    department: Optional[str] = Field(None, description="New department")
    role: Optional[str] = Field(None, description="New role/title")
    manager: Optional[str] = Field(None, description="New manager name")
    location: Optional[str] = Field(None, description="New location")
    status: Optional[StatusEnum] = Field(None, description="New status")


class DeviceUpdateRequest(BaseModel):
    """
    Request to update device information.
    
    Attributes:
        name: New device name
        compliant: New compliance status
        owner_cid: New owner's canonical identity
        ip_address: New IP address
        mac_address: New MAC address
        vlan: New VLAN identifier
        os_version: New operating system version
        status: New connection status
    """
    name: Optional[str] = Field(None, description="New device name")
    compliant: Optional[bool] = Field(None, description="New compliance status")
    owner_cid: Optional[UUID] = Field(None, description="New owner's canonical identity")
    ip_address: Optional[str] = Field(None, description="New IP address")
    mac_address: Optional[str] = Field(None, description="New MAC address")
    vlan: Optional[str] = Field(None, description="New VLAN identifier")
    os_version: Optional[str] = Field(None, description="New operating system version")
    status: Optional[DeviceStatusEnum] = Field(None, description="New connection status")


class DeviceTagRequest(BaseModel):
    """
    Request to add or remove device tags.
    
    Attributes:
        tags: List of tags to set for the device
    """
    tags: List[DeviceTagEnum] = Field(..., description="List of tags to set for the device")


class DeviceCreateRequest(BaseModel):
    """
    Request to create a new device.
    
    Attributes:
        name: Device name
        owner_cid: Owner's canonical identity
        ip_address: Device IP address
        mac_address: Device MAC address
        vlan: VLAN identifier
        os_version: Operating system version
        status: Connection status
        compliant: Compliance status
        tags: List of device tags
    """
    name: str = Field(..., description="Device name")
    owner_cid: UUID = Field(..., description="Owner's canonical identity")
    ip_address: Optional[str] = Field(None, description="Device IP address")
    mac_address: Optional[str] = Field(None, description="Device MAC address")
    vlan: Optional[str] = Field(None, description="VLAN identifier")
    os_version: Optional[str] = Field(None, description="Operating system version")
    status: DeviceStatusEnum = Field(DeviceStatusEnum.UNKNOWN, description="Connection status")
    compliant: bool = Field(True, description="Compliance status")
    tags: List[DeviceTagEnum] = Field(default=[], description="List of device tags")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Device name must be at least 3 characters long')
        if len(v) > 100:
            raise ValueError('Device name must be less than 100 characters')
        return v.strip()

    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v):
        if v is None:
            return v
        try:
            ipaddress.ip_address(v.strip())
            return v.strip()
        except ValueError:
            raise ValueError('Invalid IP address format')

    @field_validator('mac_address')
    @classmethod
    def validate_mac_address(cls, v):
        if v is None:
            return v
        # MAC address pattern: XX:XX:XX:XX:XX:XX
        mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        if not re.match(mac_pattern, v.strip()):
            raise ValueError('Invalid MAC address format (expected XX:XX:XX:XX:XX:XX)')
        return v.strip().lower()

    @field_validator('os_version')
    @classmethod
    def validate_os_version(cls, v):
        if v is None:
            return v
        if len(v.strip()) > 200:
            raise ValueError('OS version must be less than 200 characters')
        return v.strip()


class DeviceListResponse(BaseModel):
    """
    Paginated response for device list endpoint.
    
    Attributes:
        devices: List of devices for current page
        total: Total number of devices matching filters
        page: Current page number (1-based)
        page_size: Number of items per page
        total_pages: Total number of pages
    """
    devices: List[DeviceSchema] = Field(..., description="List of devices for current page")
    total: int = Field(..., description="Total number of devices matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


class IdentityMergeResult(BaseModel):
    """
    Result of an identity merge operation.
    
    Attributes:
        merged_cid: The target CID that now contains merged data
        devices_transferred: Number of devices transferred
        accounts_transferred: Number of accounts transferred
        groups_transferred: Number of group memberships transferred
        message: Human-readable result message
    """
    merged_cid: UUID = Field(..., description="The target CID that now contains merged data")
    devices_transferred: int = Field(..., description="Number of devices transferred")
    accounts_transferred: int = Field(..., description="Number of accounts transferred")
    groups_transferred: int = Field(..., description="Number of group memberships transferred")
    message: str = Field(..., description="Human-readable result message")


# Policy Management Schemas
class PolicySchema(BaseModel):
    """
    Policy information schema.
    
    Attributes:
        id: Unique policy identifier
        name: Policy name
        description: Policy description
        policy_type: Type of policy (Access Control, Device Compliance, etc.)
        severity: Policy severity level
        enabled: Whether policy is currently enabled
        created_at: When policy was created
        updated_at: When policy was last updated
        created_by: User who created the policy
        configuration: Policy configuration as JSON string
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    policy_type: PolicyTypeEnum = Field(..., description="Type of policy")
    severity: PolicySeverityEnum = Field(..., description="Policy severity level")
    enabled: bool = Field(..., description="Whether policy is currently enabled")
    created_at: datetime = Field(..., description="When policy was created")
    updated_at: datetime = Field(..., description="When policy was last updated")
    created_by: Optional[str] = Field(None, description="User who created the policy")
    configuration: Optional[str] = Field(None, description="Policy configuration as JSON string")


class PolicyCreateRequest(BaseModel):
    """
    Request to create a new policy.
    
    Attributes:
        name: Policy name
        description: Policy description
        policy_type: Type of policy
        severity: Policy severity level
        enabled: Whether policy should be enabled
        configuration: Policy configuration as JSON string
    """
    name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    policy_type: PolicyTypeEnum = Field(..., description="Type of policy")
    severity: PolicySeverityEnum = Field(PolicySeverityEnum.MEDIUM, description="Policy severity level")
    enabled: bool = Field(True, description="Whether policy should be enabled")
    configuration: Optional[str] = Field(None, description="Policy configuration as JSON string")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Policy name must be at least 3 characters long')
        if len(v) > 200:
            raise ValueError('Policy name must be less than 200 characters')
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is None:
            return v
        if len(v.strip()) > 1000:
            raise ValueError('Policy description must be less than 1000 characters')
        return v.strip()

    @field_validator('configuration')
    @classmethod
    def validate_configuration(cls, v):
        if v is None:
            return v
        try:
            # Validate that it's valid JSON
            json.loads(v)
            return v
        except json.JSONDecodeError:
            raise ValueError('Configuration must be valid JSON')


class PolicyUpdateRequest(BaseModel):
    """
    Request to update a policy.
    
    Attributes:
        name: New policy name
        description: New policy description
        severity: New policy severity level
        enabled: New enabled status
        configuration: New policy configuration
    """
    name: Optional[str] = Field(None, description="New policy name")
    description: Optional[str] = Field(None, description="New policy description")
    severity: Optional[PolicySeverityEnum] = Field(None, description="New policy severity level")
    enabled: Optional[bool] = Field(None, description="New enabled status")
    configuration: Optional[str] = Field(None, description="New policy configuration")


class PolicyListResponse(BaseModel):
    """
    Paginated response for policy list endpoint.
    
    Attributes:
        policies: List of policies for current page
        total: Total number of policies matching filters
        page: Current page number (1-based)
        page_size: Number of items per page
        total_pages: Total number of pages
    """
    policies: List[PolicySchema] = Field(..., description="List of policies for current page")
    total: int = Field(..., description="Total number of policies matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


# Configuration History Schemas
class ConfigHistorySchema(BaseModel):
    """
    Configuration change history schema.
    
    Attributes:
        id: Unique history record identifier
        entity_type: Type of entity that was changed
        entity_id: ID of the entity that was changed
        change_type: Type of change made
        field_name: Name of the field that was changed
        old_value: Previous value
        new_value: New value
        changed_by: User who made the change
        changed_at: When the change was made
        description: Human-readable description of change
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique history record identifier")
    entity_type: str = Field(..., description="Type of entity that was changed")
    entity_id: UUID = Field(..., description="ID of the entity that was changed")
    change_type: ConfigChangeTypeEnum = Field(..., description="Type of change made")
    field_name: Optional[str] = Field(None, description="Name of the field that was changed")
    old_value: Optional[str] = Field(None, description="Previous value")
    new_value: Optional[str] = Field(None, description="New value")
    changed_by: Optional[str] = Field(None, description="User who made the change")
    changed_at: datetime = Field(..., description="When the change was made")
    description: Optional[str] = Field(None, description="Human-readable description of change")


class ConfigHistoryListResponse(BaseModel):
    """
    Paginated response for configuration history endpoint.
    
    Attributes:
        changes: List of configuration changes for current page
        total: Total number of changes matching filters
        page: Current page number (1-based)
        page_size: Number of items per page
        total_pages: Total number of pages
    """
    changes: List[ConfigHistorySchema] = Field(..., description="List of configuration changes for current page")
    total: int = Field(..., description="Total number of changes matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


# Activity History Schemas
class ActivityHistorySchema(BaseModel):
    """
    Activity history schema.

    Attributes:
        id: Unique activity record identifier
        user_cid: Canonical ID of the user involved
        device_id: ID of the device involved
        activity_type: Type of activity
        source_system: System that generated this activity
        source_ip: IP address where activity originated
        user_agent: User agent string
        description: Description of the activity
        timestamp: When the activity occurred
        activity_metadata: Additional context as JSON string
        risk_score: Risk level assessment
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique activity record identifier")
    user_cid: Optional[UUID] = Field(None, description="Canonical ID of the user involved")
    device_id: Optional[UUID] = Field(None, description="ID of the device involved")
    activity_type: ActivityTypeEnum = Field(..., description="Type of activity")
    source_system: Optional[str] = Field(None, description="System that generated this activity")
    source_ip: Optional[str] = Field(None, description="IP address where activity originated")
    user_agent: Optional[str] = Field(None, description="User agent string")
    description: str = Field(..., description="Description of the activity")
    timestamp: datetime = Field(..., description="When the activity occurred")
    activity_metadata: Optional[str] = Field(None, description="Additional context as JSON string")
    risk_score: Optional[str] = Field(None, description="Risk level assessment")
    


class ActivityHistoryListResponse(BaseModel):
    """
    Paginated response for activity history endpoint.
    
    Attributes:
        activities: List of activities for current page
        total: Total number of activities matching filters
        page: Current page number (1-based)
        page_size: Number of items per page
        total_pages: Total number of pages
    """
    activities: List[ActivityHistorySchema] = Field(..., description="List of activities for current page")
    total: int = Field(..., description="Total number of activities matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


class ActivityCreateRequest(BaseModel):
    """
    Request to create a new activity record.
    
    Attributes:
        user_cid: Canonical ID of the user involved
        device_id: ID of the device involved
        activity_type: Type of activity
        source_system: System generating this activity
        source_ip: IP address where activity originated
        user_agent: User agent string
        description: Description of the activity
        activity_metadata: Additional context as JSON string
        risk_score: Risk level assessment
    """
    user_cid: Optional[UUID] = Field(None, description="Canonical ID of the user involved")
    device_id: Optional[UUID] = Field(None, description="ID of the device involved")
    activity_type: ActivityTypeEnum = Field(..., description="Type of activity")
    source_system: Optional[str] = Field(None, description="System generating this activity")
    source_ip: Optional[str] = Field(None, description="IP address where activity originated")
    user_agent: Optional[str] = Field(None, description="User agent string")
    description: str = Field(..., description="Description of the activity")
    activity_metadata: Optional[str] = Field(None, description="Additional context as JSON string")
    risk_score: Optional[str] = Field(None, description="Risk level assessment")


# Password Reset Schema
class PasswordResetRequest(BaseModel):
    """
    Request to reset user password across connected systems.
    
    Attributes:
        user_cid: Canonical ID of the user
        systems: List of systems to reset password on (empty = all systems)
        force_change: Whether to force password change on next login
        notification_method: How to notify user (email, sms, both)
    """
    user_cid: UUID = Field(..., description="Canonical ID of the user")
    systems: List[str] = Field(default=[], description="List of systems to reset password on (empty = all systems)")
    force_change: bool = Field(True, description="Whether to force password change on next login")
    notification_method: str = Field("email", description="How to notify user (email, sms, both)")


class PasswordResetResult(BaseModel):
    """
    Result of password reset operation.
    
    Attributes:
        user_cid: Canonical ID of the user
        systems_processed: List of systems where password was reset
        systems_failed: List of systems where reset failed
        notification_sent: Whether notification was sent to user
        message: Human-readable result message
    """
    user_cid: UUID = Field(..., description="Canonical ID of the user")
    systems_processed: List[str] = Field(..., description="List of systems where password was reset")
    systems_failed: List[str] = Field(..., description="List of systems where reset failed")
    notification_sent: bool = Field(..., description="Whether notification was sent to user")
    message: str = Field(..., description="Human-readable result message")


# Force Check-in Schema
class ForceCheckinRequest(BaseModel):
    """
    Request to force device check-in.
    
    Attributes:
        device_ids: List of device IDs to force check-in (empty = all devices)
        user_cid: Force check-in for all devices of specific user
        compliance_scan: Whether to run compliance scan during check-in
        update_inventory: Whether to update device inventory
    """
    device_ids: List[UUID] = Field(default=[], description="List of device IDs to force check-in")
    user_cid: Optional[UUID] = Field(None, description="Force check-in for all devices of specific user")
    compliance_scan: bool = Field(True, description="Whether to run compliance scan during check-in")
    update_inventory: bool = Field(True, description="Whether to update device inventory")


class ForceCheckinResult(BaseModel):
    """
    Result of force check-in operation.
    
    Attributes:
        devices_contacted: Number of devices contacted
        devices_responded: Number of devices that responded
        compliance_scans_completed: Number of compliance scans completed
        devices_updated: List of device IDs that were updated
        message: Human-readable result message
    """
    devices_contacted: int = Field(..., description="Number of devices contacted")
    devices_responded: int = Field(..., description="Number of devices that responded")
    compliance_scans_completed: int = Field(..., description="Number of compliance scans completed")
    devices_updated: List[UUID] = Field(..., description="List of device IDs that were updated")
    message: str = Field(..., description="Human-readable result message")


# Sync Operation Schema
class SyncRequest(BaseModel):
    """
    Request to sync data from external systems.
    
    Attributes:
        systems: List of systems to sync (empty = all configured systems)
        sync_type: Type of sync (full, incremental, users_only, devices_only)
        force_refresh: Whether to force refresh cached data
    """
    systems: List[str] = Field(default=[], description="List of systems to sync (empty = all configured systems)")
    sync_type: str = Field("incremental", description="Type of sync (full, incremental, users_only, devices_only)")
    force_refresh: bool = Field(False, description="Whether to force refresh cached data")


class SyncResult(BaseModel):
    """
    Result of sync operation.
    
    Attributes:
        systems_synced: List of systems that were synced
        users_updated: Number of users updated
        devices_updated: Number of devices updated
        accounts_updated: Number of accounts updated
        errors: List of errors encountered during sync
        sync_duration: Duration of sync operation in seconds
        message: Human-readable result message
    """
    systems_synced: List[str] = Field(..., description="List of systems that were synced")
    users_updated: int = Field(..., description="Number of users updated")
    devices_updated: int = Field(..., description="Number of devices updated")
    accounts_updated: int = Field(..., description="Number of accounts updated")
    errors: List[str] = Field(..., description="List of errors encountered during sync")
    sync_duration: float = Field(..., description="Duration of sync operation in seconds")
    message: str = Field(..., description="Human-readable result message")


# Enhanced Merge Schema
class AdvancedMergeRequest(BaseModel):
    """
    Request for advanced identity merge with conflict resolution.
    
    Attributes:
        source_cid: CID of user to merge FROM
        target_cid: CID of user to merge TO
        merge_devices: Whether to transfer devices
        merge_accounts: Whether to transfer accounts
        merge_groups: Whether to transfer group memberships
        conflict_resolution: How to handle conflicts (take_source, take_target, merge)
        preserve_history: Whether to preserve activity history
    """
    source_cid: UUID = Field(..., description="CID of user to merge FROM")
    target_cid: UUID = Field(..., description="CID of user to merge TO")
    merge_devices: bool = Field(True, description="Whether to transfer devices")
    merge_accounts: bool = Field(True, description="Whether to transfer accounts")
    merge_groups: bool = Field(True, description="Whether to transfer group memberships")
    conflict_resolution: str = Field("take_target", description="How to handle conflicts (take_source, take_target, merge)")
    preserve_history: bool = Field(True, description="Whether to preserve activity history")


class MergeConflict(BaseModel):
    """
    Schema for merge conflicts that need resolution.
    
    Attributes:
        field_name: Name of the conflicting field
        source_value: Value from source identity
        target_value: Value from target identity
        recommended_action: Recommended resolution action
    """
    field_name: str = Field(..., description="Name of the conflicting field")
    source_value: Optional[str] = Field(None, description="Value from source identity")
    target_value: Optional[str] = Field(None, description="Value from target identity")
    recommended_action: str = Field(..., description="Recommended resolution action")


class MergePreviewResult(BaseModel):
    """
    Preview of merge operation showing potential conflicts.
    
    Attributes:
        source_cid: CID of source user
        target_cid: CID of target user
        conflicts: List of conflicts that would occur
        devices_to_transfer: Number of devices that would be transferred
        accounts_to_transfer: Number of accounts that would be transferred
        groups_to_transfer: Number of group memberships that would be transferred
        estimated_duration: Estimated time for merge operation
    """
    source_cid: UUID = Field(..., description="CID of source user")
    target_cid: UUID = Field(..., description="CID of target user")
    conflicts: List[MergeConflict] = Field(..., description="List of conflicts that would occur")
    devices_to_transfer: int = Field(..., description="Number of devices that would be transferred")
    accounts_to_transfer: int = Field(..., description="Number of accounts that would be transferred")
    groups_to_transfer: int = Field(..., description="Number of group memberships that would be transferred")
    estimated_duration: float = Field(..., description="Estimated time for merge operation")


# API Management Schemas
class APIConnectionTagSchema(BaseModel):
    """
    API connection tag schema.
    
    Attributes:
        id: Unique tag identifier
        tag: Tag value (Production, Critical, Identity Source, etc.)
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique tag identifier")
    tag: APIConnectionTagEnum = Field(..., description="Tag value")


class APIConnectionSchema(BaseModel):
    """
    API connection information schema.
    
    Attributes:
        id: Unique connection identifier
        name: User-friendly name for the connection
        provider: API provider type
        description: Connection description
        base_url: Base URL for the API
        api_version: API version
        authentication_type: Type of authentication used
        sync_enabled: Whether automatic sync is enabled
        sync_interval_minutes: How often to sync in minutes
        last_sync: When last sync occurred
        next_sync: When next sync is scheduled
        status: Current connection status
        last_health_check: When health check was last performed
        health_check_message: Result of last health check
        rate_limit_requests: Rate limit requests per window
        rate_limit_window: Rate limit time window
        created_at: When connection was created
        updated_at: When connection was last updated
        created_by: User who created the connection
        supports_users: Whether this API supports user data
        supports_devices: Whether this API supports device data
        supports_groups: Whether this API supports group data
        supports_realtime: Whether this API supports real-time updates
        connection_test_url: Specific endpoint to test connection
        tags: List of API connection tags
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique connection identifier")
    name: str = Field(..., description="User-friendly name for the connection")
    provider: APIProviderEnum = Field(..., description="API provider type")
    description: Optional[str] = Field(None, description="Connection description")
    base_url: str = Field(..., description="Base URL for the API")
    api_version: Optional[str] = Field(None, description="API version")
    authentication_type: str = Field(..., description="Type of authentication used")
    sync_enabled: bool = Field(..., description="Whether automatic sync is enabled")
    sync_interval_minutes: Optional[str] = Field(None, description="How often to sync in minutes")
    last_sync: Optional[datetime] = Field(None, description="When last sync occurred")
    next_sync: Optional[datetime] = Field(None, description="When next sync is scheduled")
    status: APIConnectionStatusEnum = Field(..., description="Current connection status")
    last_health_check: Optional[datetime] = Field(None, description="When health check was last performed")
    health_check_message: Optional[str] = Field(None, description="Result of last health check")
    connection_test_url: Optional[str] = Field(None, description="Specific endpoint to test connection")
    rate_limit_requests: Optional[str] = Field(None, description="Rate limit requests per window")
    rate_limit_window: Optional[str] = Field(None, description="Rate limit time window")
    created_at: datetime = Field(..., description="When connection was created")
    updated_at: datetime = Field(..., description="When connection was last updated")
    created_by: Optional[str] = Field(None, description="User who created the connection")
    supports_users: bool = Field(..., description="Whether this API supports user data")
    supports_devices: bool = Field(..., description="Whether this API supports device data")
    supports_groups: bool = Field(..., description="Whether this API supports group data")
    supports_realtime: bool = Field(..., description="Whether this API supports real-time updates")
    tags: List[APIConnectionTagSchema] = Field(default=[], description="List of API connection tags")


class APIConnectionCreateRequest(BaseModel):
    """
    Request to create a new API connection.
    
    Attributes:
        name: User-friendly name for the connection
        provider: API provider type
        description: Connection description
        base_url: Base URL for the API
        api_version: API version
        authentication_type: Type of authentication
        credentials: Authentication credentials (will be encrypted)
        sync_enabled: Whether to enable automatic sync
        sync_interval_minutes: How often to sync in minutes
        rate_limit_requests: Rate limit requests per window
        rate_limit_window: Rate limit time window
        field_mappings: JSON configuration for field mapping
        supports_users: Whether this API supports user data
        supports_devices: Whether this API supports device data
        supports_groups: Whether this API supports group data
        supports_realtime: Whether this API supports real-time updates
        connection_test_url: Specific endpoint to test connection
        tags: List of tags to assign to the connection
    """
    name: str = Field(..., description="User-friendly name for the connection")
    provider: APIProviderEnum = Field(..., description="API provider type")
    description: Optional[str] = Field(None, description="Connection description")
    base_url: str = Field(..., description="Base URL for the API")
    api_version: Optional[str] = Field(None, description="API version")
    authentication_type: str = Field(..., description="Type of authentication")
    credentials: str = Field(..., description="Authentication credentials (will be encrypted)")
    sync_enabled: bool = Field(True, description="Whether to enable automatic sync")
    sync_interval_minutes: str = Field("60", description="How often to sync in minutes")
    connection_test_url: Optional[str] = Field(None, description="Specific endpoint to test connection")
    rate_limit_requests: Optional[str] = Field(None, description="Rate limit requests per window")
    rate_limit_window: Optional[str] = Field(None, description="Rate limit time window")
    field_mappings: Optional[str] = Field(None, description="JSON configuration for field mapping")
    supports_users: bool = Field(True, description="Whether this API supports user data")
    supports_devices: bool = Field(False, description="Whether this API supports device data")
    supports_groups: bool = Field(True, description="Whether this API supports group data")
    supports_realtime: bool = Field(False, description="Whether this API supports real-time updates")
    tags: List[APIConnectionTagEnum] = Field(default=[], description="List of tags to assign to the connection")


class APIConnectionUpdateRequest(BaseModel):
    """
    Request to update an API connection.
    
    Attributes:
        name: New connection name
        description: New description
        base_url: New base URL
        api_version: New API version
        authentication_type: New authentication type
        credentials: New credentials (will be encrypted)
        sync_enabled: New sync enabled status
        sync_interval_minutes: New sync interval
        rate_limit_requests: New rate limit requests
        rate_limit_window: New rate limit window
        field_mappings: New field mappings configuration
        supports_users: New user support status
        supports_devices: New device support status
        supports_groups: New group support status
        supports_realtime: New real-time support status
    """
    name: Optional[str] = Field(None, description="New connection name")
    description: Optional[str] = Field(None, description="New description")
    base_url: Optional[str] = Field(None, description="New base URL")
    api_version: Optional[str] = Field(None, description="New API version")
    authentication_type: Optional[str] = Field(None, description="New authentication type")
    credentials: Optional[str] = Field(None, description="New credentials (will be encrypted)")
    sync_enabled: Optional[bool] = Field(None, description="New sync enabled status")
    sync_interval_minutes: Optional[str] = Field(None, description="New sync interval")
    rate_limit_requests: Optional[str] = Field(None, description="New rate limit requests")
    rate_limit_window: Optional[str] = Field(None, description="New rate limit window")
    field_mappings: Optional[str] = Field(None, description="New field mappings configuration")
    supports_users: Optional[bool] = Field(None, description="New user support status")
    supports_devices: Optional[bool] = Field(None, description="New device support status")
    supports_groups: Optional[bool] = Field(None, description="New group support status")
    supports_realtime: Optional[bool] = Field(None, description="New real-time support status")


class APIConnectionListResponse(BaseModel):
    """
    Paginated response for API connections list.
    
    Attributes:
        connections: List of API connections for current page
        total: Total number of connections matching filters
        page: Current page number (1-based)
        page_size: Number of items per page
        total_pages: Total number of pages
    """
    connections: List[APIConnectionSchema] = Field(..., description="List of API connections for current page")
    total: int = Field(..., description="Total number of connections matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


class APIHealthCheckResult(BaseModel):
    """
    Result of API health check.
    
    Attributes:
        connection_id: ID of the connection tested
        status: Health check status
        response_time_ms: Response time in milliseconds
        message: Health check result message
        last_checked: When the check was performed
        capabilities_verified: List of capabilities that were verified
    """
    connection_id: UUID = Field(..., description="ID of the connection tested")
    status: str = Field(..., description="Health check status")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    message: str = Field(..., description="Health check result message")
    last_checked: datetime = Field(..., description="When the check was performed")
    capabilities_verified: List[str] = Field(..., description="List of capabilities that were verified")


class APISyncLogSchema(BaseModel):
    """
    API sync log entry schema.
    
    Attributes:
        id: Unique log entry identifier
        connection_id: ID of the API connection
        sync_type: Type of sync performed
        started_at: When sync started
        completed_at: When sync completed
        duration_seconds: How long sync took
        status: Sync result status
        records_processed: Number of records processed
        records_created: Number of new records created
        records_updated: Number of records updated
        records_failed: Number of records that failed
        error_message: Error message if sync failed
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique log entry identifier")
    connection_id: UUID = Field(..., description="ID of the API connection")
    sync_type: str = Field(..., description="Type of sync performed")
    started_at: datetime = Field(..., description="When sync started")
    completed_at: Optional[datetime] = Field(None, description="When sync completed")
    duration_seconds: Optional[str] = Field(None, description="How long sync took")
    status: str = Field(..., description="Sync result status")
    records_processed: str = Field(..., description="Number of records processed")
    records_created: str = Field(..., description="Number of new records created")
    records_updated: str = Field(..., description="Number of records updated")
    records_failed: str = Field(..., description="Number of records that failed")
    error_message: Optional[str] = Field(None, description="Error message if sync failed")


class APISyncLogListResponse(BaseModel):
    """
    Paginated response for API sync logs.
    
    Attributes:
        logs: List of sync log entries for current page
        total: Total number of log entries matching filters
        page: Current page number (1-based)
        page_size: Number of items per page
        total_pages: Total number of pages
    """
    logs: List[APISyncLogSchema] = Field(..., description="List of sync log entries for current page")
    total: int = Field(..., description="Total number of log entries matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
