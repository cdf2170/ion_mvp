from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from backend.app.db.models import StatusEnum


class DeviceSchema(BaseModel):
    """
    Device information schema for frontend consumption.
    
    Attributes:
        id: Unique device identifier
        name: Human-readable device name (e.g., "John's MacBook Pro")
        last_seen: Last time device was seen/active
        compliant: Whether device meets compliance requirements
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Human-readable device name")
    last_seen: datetime = Field(..., description="Last time device was seen/active")
    compliant: bool = Field(..., description="Whether device meets compliance requirements")


class GroupMembershipSchema(BaseModel):
    """
    User group membership schema.
    
    Attributes:
        id: Unique membership identifier
        group_name: Name of the group (e.g., "Developers", "Managers")
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique membership identifier")
    group_name: str = Field(..., description="Name of the group")


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
    """
    name: Optional[str] = Field(None, description="New device name")
    compliant: Optional[bool] = Field(None, description="New compliance status")
    owner_cid: Optional[UUID] = Field(None, description="New owner's canonical identity")


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
