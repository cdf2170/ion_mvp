#!/usr/bin/env python3
"""
Modern, comprehensive database seeding script for Identity Management Platform MVP.
This script creates realistic, enterprise-grade data that reflects all current features.

Features covered:
- Realistic user identities with proper organizational structure
- Modern device types with hardware specifications
- Enterprise-grade policies with proper configurations
- API connections for identity providers and security tools
- Comprehensive access management with audit trails
- Activity history and configuration changes
- Group memberships and organizational relationships
"""

import os
import sys
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import json

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from faker import Faker
from backend.app.db.session import get_db
from backend.app.db.models import (
    # Core models
    CanonicalIdentity, Device, DeviceTag, GroupMembership, Account, Policy,
    
    # Access management
    AccessGrant, AccessAuditLog, AccessReview, AccessPattern,
    
    # API management
    APIConnection, APIConnectionTag, APISyncLog,
    
    # Activity and configuration
    ActivityHistory, ConfigHistory,
    
    # Enums
    StatusEnum, DeviceStatusEnum, DeviceTagEnum, GroupTypeEnum,
    PolicyTypeEnum, PolicySeverityEnum, AccessTypeEnum, AccessStatusEnum,
    AccessReasonEnum, AuditActionEnum, APIProviderEnum, APIConnectionStatusEnum,
    APIConnectionTagEnum, ActivityTypeEnum, ConfigChangeTypeEnum
)

fake = Faker()

# Modern device types with realistic specifications
MODERN_DEVICE_TYPES = {
    "laptops": [
        {"type": "MacBook Pro 16\"", "os": ["macOS 14.2 Sonoma", "macOS 13.6 Ventura"], "ram": ["16GB", "32GB", "64GB"], "storage": ["512GB", "1TB", "2TB", "4TB"]},
        {"type": "MacBook Air 15\"", "os": ["macOS 14.2 Sonoma", "macOS 13.6 Ventura"], "ram": ["8GB", "16GB", "24GB"], "storage": ["256GB", "512GB", "1TB", "2TB"]},
        {"type": "ThinkPad X1 Carbon Gen 11", "os": ["Windows 11 Pro 23H2", "Windows 11 Enterprise"], "ram": ["16GB", "32GB"], "storage": ["512GB", "1TB", "2TB"]},
        {"type": "ThinkPad P1 Gen 6", "os": ["Windows 11 Pro 23H2", "Ubuntu 22.04 LTS"], "ram": ["32GB", "64GB"], "storage": ["1TB", "2TB", "4TB"]},
        {"type": "Dell XPS 15 9530", "os": ["Windows 11 Pro 23H2", "Windows 11 Enterprise"], "ram": ["16GB", "32GB", "64GB"], "storage": ["512GB", "1TB", "2TB"]},
        {"type": "HP Spectre x360 16", "os": ["Windows 11 Pro 23H2", "Windows 11 Enterprise"], "ram": ["16GB", "32GB"], "storage": ["512GB", "1TB", "2TB"]},
        {"type": "Surface Laptop Studio 2", "os": ["Windows 11 Pro 23H2", "Windows 11 Enterprise"], "ram": ["16GB", "32GB", "64GB"], "storage": ["512GB", "1TB", "2TB"]},
    ],
    "desktops": [
        {"type": "Mac Studio M2 Ultra", "os": ["macOS 14.2 Sonoma", "macOS 13.6 Ventura"], "ram": ["64GB", "128GB"], "storage": ["1TB", "2TB", "4TB", "8TB"]},
        {"type": "Mac Pro M2 Ultra", "os": ["macOS 14.2 Sonoma", "macOS 13.6 Ventura"], "ram": ["64GB", "128GB", "192GB"], "storage": ["1TB", "2TB", "4TB", "8TB"]},
        {"type": "Dell Precision 5820", "os": ["Windows 11 Pro 23H2", "Ubuntu 22.04 LTS"], "ram": ["32GB", "64GB", "128GB"], "storage": ["1TB", "2TB", "4TB"]},
        {"type": "HP Z8 G5", "os": ["Windows 11 Pro 23H2", "Ubuntu 22.04 LTS"], "ram": ["64GB", "128GB", "256GB"], "storage": ["2TB", "4TB", "8TB"]},
    ],
    "mobile": [
        {"type": "iPhone 15 Pro Max", "os": ["iOS 17.1", "iOS 17.0"], "ram": ["8GB"], "storage": ["256GB", "512GB", "1TB"]},
        {"type": "iPhone 15 Pro", "os": ["iOS 17.1", "iOS 17.0"], "ram": ["8GB"], "storage": ["128GB", "256GB", "512GB", "1TB"]},
        {"type": "iPad Pro 12.9\"", "os": ["iPadOS 17.1", "iPadOS 17.0"], "ram": ["8GB", "16GB"], "storage": ["256GB", "512GB", "1TB", "2TB"]},
        {"type": "Samsung Galaxy S24 Ultra", "os": ["Android 14", "Android 13"], "ram": ["12GB"], "storage": ["256GB", "512GB", "1TB"]},
        {"type": "Google Pixel 8 Pro", "os": ["Android 14", "Android 13"], "ram": ["12GB"], "storage": ["128GB", "256GB", "512GB", "1TB"]},
    ]
}

# Enterprise departments with realistic roles
ENTERPRISE_DEPARTMENTS = {
    "Engineering": {
        "roles": ["Software Engineer", "Senior Software Engineer", "Staff Engineer", "Principal Engineer", "Engineering Manager", "Director of Engineering", "VP of Engineering", "CTO"],
        "managers": ["Engineering Manager", "Director of Engineering", "VP of Engineering", "CTO"],
        "locations": ["San Francisco, CA", "Austin, TX", "Seattle, WA", "Remote", "New York, NY"]
    },
    "Product": {
        "roles": ["Product Manager", "Senior Product Manager", "Principal Product Manager", "Director of Product", "VP of Product", "CPO"],
        "managers": ["Senior Product Manager", "Director of Product", "VP of Product", "CPO"],
        "locations": ["San Francisco, CA", "New York, NY", "Remote", "Austin, TX"]
    },
    "Sales": {
        "roles": ["Sales Development Rep", "Account Executive", "Senior Account Executive", "Sales Manager", "Director of Sales", "VP of Sales", "CRO"],
        "managers": ["Sales Manager", "Director of Sales", "VP of Sales", "CRO"],
        "locations": ["New York, NY", "Chicago, IL", "Los Angeles, CA", "Remote", "San Francisco, CA"]
    },
    "Marketing": {
        "roles": ["Marketing Coordinator", "Marketing Manager", "Senior Marketing Manager", "Director of Marketing", "VP of Marketing", "CMO"],
        "managers": ["Marketing Manager", "Director of Marketing", "VP of Marketing", "CMO"],
        "locations": ["San Francisco, CA", "New York, NY", "Remote", "Los Angeles, CA"]
    },
    "Finance": {
        "roles": ["Financial Analyst", "Senior Financial Analyst", "Finance Manager", "Director of Finance", "VP of Finance", "CFO"],
        "managers": ["Finance Manager", "Director of Finance", "VP of Finance", "CFO"],
        "locations": ["San Francisco, CA", "New York, NY", "Remote"]
    },
    "Human Resources": {
        "roles": ["HR Coordinator", "HR Business Partner", "Senior HR Business Partner", "HR Manager", "Director of HR", "VP of HR", "CHRO"],
        "managers": ["HR Manager", "Director of HR", "VP of HR", "CHRO"],
        "locations": ["San Francisco, CA", "New York, NY", "Remote", "Austin, TX"]
    },
    "IT": {
        "roles": ["IT Support Specialist", "Senior IT Support Specialist", "IT Manager", "Director of IT", "VP of IT", "CIO"],
        "managers": ["IT Manager", "Director of IT", "VP of IT", "CIO"],
        "locations": ["San Francisco, CA", "Austin, TX", "Remote", "New York, NY"]
    },
    "Security": {
        "roles": ["Security Analyst", "Senior Security Analyst", "Security Engineer", "Senior Security Engineer", "Security Manager", "Director of Security", "CISO"],
        "managers": ["Security Manager", "Director of Security", "CISO"],
        "locations": ["San Francisco, CA", "Austin, TX", "Remote", "New York, NY"]
    },
    "Operations": {
        "roles": ["Operations Coordinator", "Operations Manager", "Senior Operations Manager", "Director of Operations", "VP of Operations", "COO"],
        "managers": ["Operations Manager", "Director of Operations", "VP of Operations", "COO"],
        "locations": ["San Francisco, CA", "Austin, TX", "Remote", "New York, NY"]
    },
    "Legal": {
        "roles": ["Legal Assistant", "Legal Counsel", "Senior Legal Counsel", "Director of Legal", "General Counsel"],
        "managers": ["Senior Legal Counsel", "Director of Legal", "General Counsel"],
        "locations": ["San Francisco, CA", "New York, NY", "Remote"]
    }
}

# Enterprise-grade policies
ENTERPRISE_POLICIES = [
    {
        "name": "Corporate Password Policy",
        "description": "Enterprise-wide password complexity and rotation requirements for all corporate accounts",
        "policy_type": PolicyTypeEnum.PASSWORD_POLICY,
        "severity": PolicySeverityEnum.HIGH,
        "configuration": {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special_chars": True,
            "rotation_days": 90,
            "history_count": 12,
            "lockout_attempts": 5,
            "lockout_duration_minutes": 30
        }
    },
    {
        "name": "Privileged Account Password Policy",
        "description": "Enhanced password requirements for administrative and privileged accounts",
        "policy_type": PolicyTypeEnum.PASSWORD_POLICY,
        "severity": PolicySeverityEnum.CRITICAL,
        "configuration": {
            "min_length": 16,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special_chars": True,
            "rotation_days": 30,
            "history_count": 24,
            "lockout_attempts": 3,
            "lockout_duration_minutes": 60,
            "require_mfa": True
        }
    },
    {
        "name": "Corporate Device Encryption",
        "description": "Full disk encryption mandatory for all corporate devices accessing sensitive data",
        "policy_type": PolicyTypeEnum.DEVICE_COMPLIANCE,
        "severity": PolicySeverityEnum.CRITICAL,
        "configuration": {
            "encryption_required": True,
            "encryption_type": "AES-256",
            "tpm_required": True,
            "secure_boot_required": True,
            "compliance_check_interval_hours": 24
        }
    },
    {
        "name": "Mobile Device Management (MDM)",
        "description": "Security controls and compliance requirements for mobile devices accessing corporate resources",
        "policy_type": PolicyTypeEnum.DEVICE_COMPLIANCE,
        "severity": PolicySeverityEnum.HIGH,
        "configuration": {
            "mdm_enrollment_required": True,
            "jailbreak_detection": True,
            "app_whitelisting": True,
            "remote_wipe_capability": True,
            "screen_lock_required": True,
            "biometric_auth_required": True
        }
    },
    {
        "name": "Endpoint Detection and Response (EDR)",
        "description": "Required security agents for all workstations and servers with real-time monitoring",
        "policy_type": PolicyTypeEnum.DEVICE_COMPLIANCE,
        "severity": PolicySeverityEnum.CRITICAL,
        "configuration": {
            "edr_agent_required": True,
            "real_time_monitoring": True,
            "threat_detection": True,
            "automated_response": True,
            "compliance_reporting": True
        }
    },
    {
        "name": "Network Access Control (NAC)",
        "description": "Network-level security controls and device compliance verification",
        "policy_type": PolicyTypeEnum.NETWORK_SECURITY,
        "severity": PolicySeverityEnum.HIGH,
        "configuration": {
            "device_authentication": True,
            "compliance_verification": True,
            "network_segmentation": True,
            "quarantine_non_compliant": True,
            "vlan_assignment": True
        }
    },
    {
        "name": "Data Classification and Handling",
        "description": "Data classification standards and handling requirements for sensitive information",
        "policy_type": PolicyTypeEnum.DATA_CLASSIFICATION,
        "severity": PolicySeverityEnum.HIGH,
        "configuration": {
            "classification_levels": ["Public", "Internal", "Confidential", "Restricted"],
            "encryption_required": ["Confidential", "Restricted"],
            "access_logging": True,
            "retention_policies": True,
            "data_loss_prevention": True
        }
    },
    {
        "name": "Backup and Recovery Policy",
        "description": "Comprehensive backup and disaster recovery requirements for all corporate data",
        "policy_type": PolicyTypeEnum.BACKUP_RETENTION,
        "severity": PolicySeverityEnum.MEDIUM,
        "configuration": {
            "backup_frequency": "daily",
            "retention_period_days": 90,
            "offsite_backup": True,
            "encrypted_backups": True,
            "recovery_testing": "quarterly"
        }
    }
]

# Modern API connections for enterprise tools
API_CONNECTIONS = [
    {
        "name": "Okta Identity Provider",
        "provider": APIProviderEnum.OKTA,
        "description": "Primary identity provider for user authentication and SSO",
        "base_url": "https://company.okta.com",
        "api_version": "v1",
        "authentication_type": "oauth2",
        "credentials": json.dumps({
            "client_id": "0oa1b2c3d4e5f6g7h8i9j0k",
            "client_secret": "encrypted_secret_here",
            "domain": "company.okta.com"
        }),
        "sync_interval_minutes": "15",
        "status": APIConnectionStatusEnum.CONNECTED,
        "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.IDENTITY_SOURCE, APIConnectionTagEnum.CRITICAL],
        "supports_users": True,
        "supports_groups": True,
        "supports_realtime": True
    },
    {
        "name": "Microsoft 365 Tenant",
        "provider": APIProviderEnum.MICROSOFT_365,
        "description": "Microsoft 365 tenant for email, collaboration, and device management",
        "base_url": "https://graph.microsoft.com",
        "api_version": "v1.0",
        "authentication_type": "oauth2",
        "credentials": json.dumps({
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            "client_id": "87654321-4321-4321-4321-210987654321",
            "client_secret": "encrypted_secret_here"
        }),
        "sync_interval_minutes": "30",
        "status": APIConnectionStatusEnum.CONNECTED,
        "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.IDENTITY_SOURCE, APIConnectionTagEnum.CRITICAL],
        "supports_users": True,
        "supports_devices": True,
        "supports_groups": True,
        "supports_realtime": True
    },
    {
        "name": "CrowdStrike Falcon",
        "provider": APIProviderEnum.CROWDSTRIKE,
        "description": "Endpoint detection and response platform for device security monitoring",
        "base_url": "https://api.crowdstrike.com",
        "api_version": "v1",
        "authentication_type": "api_key",
        "credentials": json.dumps({
            "client_id": "crowdstrike_client_id",
            "client_secret": "encrypted_secret_here"
        }),
        "sync_interval_minutes": "5",
        "status": APIConnectionStatusEnum.CONNECTED,
        "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.DEVICE_SOURCE, APIConnectionTagEnum.SECURITY_TOOL, APIConnectionTagEnum.REAL_TIME],
        "supports_devices": True,
        "supports_realtime": True
    },
    {
        "name": "Splunk SIEM",
        "provider": APIProviderEnum.SPLUNK,
        "description": "Security information and event management for log analysis and threat detection",
        "base_url": "https://splunk.company.com:8089",
        "api_version": "v1",
        "authentication_type": "basic",
        "credentials": json.dumps({
            "username": "splunk_api_user",
            "password": "encrypted_password_here"
        }),
        "sync_interval_minutes": "10",
        "status": APIConnectionStatusEnum.CONNECTED,
        "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.SECURITY_TOOL, APIConnectionTagEnum.REAL_TIME, APIConnectionTagEnum.HIGH_VOLUME],
        "supports_realtime": True
    },
    {
        "name": "Workday HR System",
        "provider": APIProviderEnum.WORKDAY,
        "description": "Human resources management system for employee data and organizational structure",
        "base_url": "https://company.workday.com",
        "api_version": "v1",
        "authentication_type": "oauth2",
        "credentials": json.dumps({
            "client_id": "workday_client_id",
            "client_secret": "encrypted_secret_here",
            "tenant": "company"
        }),
        "sync_interval_minutes": "60",
        "status": APIConnectionStatusEnum.CONNECTED,
        "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.HR_SYSTEM, APIConnectionTagEnum.IDENTITY_SOURCE],
        "supports_users": True,
        "supports_groups": True
    }
]

def create_enterprise_users(db: Session, count: int = 100) -> List[CanonicalIdentity]:
    """Create realistic enterprise users with proper organizational structure."""
    print(f"Creating {count} enterprise users...")
    
    users = []
    created_managers = {}  # Track managers by department
    
    for i in range(count):
        # Select department and role
        dept_name = random.choice(list(ENTERPRISE_DEPARTMENTS.keys()))
        dept_info = ENTERPRISE_DEPARTMENTS[dept_name]
        
        # Determine if this should be a manager
        is_manager = random.random() < 0.15  # 15% chance of being a manager
        if is_manager:
            role = random.choice(dept_info["managers"])
        else:
            role = random.choice(dept_info["roles"])
        
        # Generate realistic name and email
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@techcorp.com"
        
        # Determine manager
        manager_name = None
        if not is_manager and dept_name in created_managers:
            manager_name = random.choice(created_managers[dept_name])
        elif is_manager:
            # Some managers report to other managers
            if random.random() < 0.3 and dept_name in created_managers:
                manager_name = random.choice(created_managers[dept_name])
        
        # Create user
        user = CanonicalIdentity(
            email=email,
            full_name=f"{first_name} {last_name}",
            department=dept_name,
            role=role,
            manager=manager_name,
            location=random.choice(dept_info["locations"]),
            status=StatusEnum.ACTIVE,
            last_seen=fake.date_time_between(start_date='-7d', end_date='now', tzinfo=timezone.utc)
        )
        
        db.add(user)
        users.append(user)
        
        # Track managers for future users
        if is_manager:
            if dept_name not in created_managers:
                created_managers[dept_name] = []
            created_managers[dept_name].append(f"{first_name} {last_name}")
    
    db.flush()  # Get IDs
    print(f"✓ Created {len(users)} users")
    return users

def create_modern_devices(db: Session, users: List[CanonicalIdentity], count: int = 150) -> List[Device]:
    """Create modern devices with realistic hardware specifications."""
    print(f"Creating {count} modern devices...")
    
    devices = []
    device_categories = list(MODERN_DEVICE_TYPES.keys())
    
    for i in range(count):
        user = random.choice(users)
        
        # Select device category and type
        category = random.choice(device_categories)
        device_spec = random.choice(MODERN_DEVICE_TYPES[category])
        
        device_type = device_spec["type"]
        os_version = random.choice(device_spec["os"])
        ram = random.choice(device_spec["ram"])
        storage = random.choice(device_spec["storage"])
        
        # Create device name
        if category == "mobile":
            device_name = f"{user.full_name.split()[0]}'s {device_type}"
        else:
            # Generate asset number
            asset_number = random.randint(1000, 9999)
            device_name = f"TC-{category.upper()[:3]}-{asset_number}"
        
        # Create device
        device = Device(
            name=device_name,
            device_type=device_type,
            os_version=f"{device_type} - {os_version} ({ram}, {storage})",
            owner_cid=user.cid,
            last_seen=fake.date_time_between(start_date='-7d', end_date='now', tzinfo=timezone.utc),
            last_check_in=fake.date_time_between(start_date='-24h', end_date='now', tzinfo=timezone.utc),
            compliant=random.choice([True, True, True, False]) if random.random() > 0.1 else True,  # 90% compliant
            ip_address=fake.ipv4_private(),
            mac_address=fake.mac_address(),
            vlan=random.choice([
                "VLAN_100_CORPORATE", "VLAN_200_GUEST", "VLAN_300_SECURE", 
                "VLAN_400_BYOD", "DMZ_ZONE", "QUARANTINE_VLAN"
            ]),
            status=random.choice([
                DeviceStatusEnum.CONNECTED, DeviceStatusEnum.CONNECTED, DeviceStatusEnum.CONNECTED,  # 75% connected
                DeviceStatusEnum.DISCONNECTED, DeviceStatusEnum.UNKNOWN
            ])
        )
        
        db.add(device)
        devices.append(device)
    
    db.flush()  # Get IDs
    print(f"✓ Created {len(devices)} devices")
    return devices

def create_device_tags(db: Session, devices: List[Device]):
    """Create realistic device tags."""
    print("Creating device tags...")
    
    tag_count = 0
    for device in devices:
        # Each device gets 2-4 tags
        num_tags = random.randint(2, 4)
        selected_tags = random.sample(list(DeviceTagEnum), num_tags)
        
        for tag_enum in selected_tags:
            tag = DeviceTag(
                device_id=device.id,
                tag=tag_enum
            )
            db.add(tag)
            tag_count += 1
    
    print(f"✓ Created {tag_count} device tags")

def create_enterprise_groups(db: Session, users: List[CanonicalIdentity]):
    """Create realistic enterprise group memberships."""
    print("Creating enterprise groups...")
    
    # Define realistic groups by department
    group_templates = {
        "Engineering": [
            ("Frontend Team", GroupTypeEnum.TEAM),
            ("Backend Team", GroupTypeEnum.TEAM),
            ("DevOps Team", GroupTypeEnum.TEAM),
            ("QA Team", GroupTypeEnum.TEAM),
            ("Senior Engineers", GroupTypeEnum.ACCESS_LEVEL),
            ("Code Reviewers", GroupTypeEnum.ACCESS_LEVEL),
            ("Production Access", GroupTypeEnum.ACCESS_LEVEL)
        ],
        "Sales": [
            ("Enterprise Sales", GroupTypeEnum.TEAM),
            ("SMB Sales", GroupTypeEnum.TEAM),
            ("Sales Development", GroupTypeEnum.TEAM),
            ("Sales Managers", GroupTypeEnum.ACCESS_LEVEL),
            ("CRM Access", GroupTypeEnum.ACCESS_LEVEL)
        ],
        "Marketing": [
            ("Digital Marketing", GroupTypeEnum.TEAM),
            ("Content Marketing", GroupTypeEnum.TEAM),
            ("Product Marketing", GroupTypeEnum.TEAM),
            ("Marketing Analytics", GroupTypeEnum.ACCESS_LEVEL)
        ],
        "Finance": [
            ("Financial Planning", GroupTypeEnum.TEAM),
            ("Accounting", GroupTypeEnum.TEAM),
            ("Financial Systems Access", GroupTypeEnum.ACCESS_LEVEL),
            ("Audit Access", GroupTypeEnum.ACCESS_LEVEL)
        ],
        "IT": [
            ("IT Support", GroupTypeEnum.TEAM),
            ("Infrastructure", GroupTypeEnum.TEAM),
            ("System Administrators", GroupTypeEnum.ACCESS_LEVEL),
            ("Domain Admins", GroupTypeEnum.ACCESS_LEVEL)
        ],
        "Security": [
            ("Security Operations", GroupTypeEnum.TEAM),
            ("Incident Response", GroupTypeEnum.TEAM),
            ("Security Analysts", GroupTypeEnum.ACCESS_LEVEL),
            ("Security Clearance", GroupTypeEnum.SECURITY_CLEARANCE)
        ]
    }
    
    group_count = 0
    for user in users:
        dept = user.department
        
        # Add department-based groups
        if dept in group_templates:
            for group_name, group_type in group_templates[dept]:
                if random.random() < 0.7:  # 70% chance of being in department groups
                    membership = GroupMembership(
                        cid=user.cid,
                        group_name=group_name,
                        group_type=group_type,
                        description=f"Membership in {group_name}",
                        source_system="HR System"
                    )
                    db.add(membership)
                    group_count += 1
        
        # Add cross-functional groups
        cross_functional_groups = [
            ("Executive Team", GroupTypeEnum.ACCESS_LEVEL),
            ("All Hands", GroupTypeEnum.DEPARTMENT),
            ("Remote Workers", GroupTypeEnum.LOCATION),
            ("New Hires", GroupTypeEnum.EMPLOYMENT_TYPE)
        ]
        
        for group_name, group_type in cross_functional_groups:
            if random.random() < 0.3:  # 30% chance of cross-functional membership
                membership = GroupMembership(
                    cid=user.cid,
                    group_name=group_name,
                    group_type=group_type,
                    description=f"Membership in {group_name}",
                    source_system="HR System"
                )
                db.add(membership)
                group_count += 1
    
    print(f"✓ Created {group_count} group memberships")

def create_enterprise_policies(db: Session) -> List[Policy]:
    """Create enterprise-grade policies."""
    print("Creating enterprise policies...")
    
    policies = []
    for policy_data in ENTERPRISE_POLICIES:
        policy = Policy(
            name=policy_data["name"],
            description=policy_data["description"],
            policy_type=policy_data["policy_type"],
            severity=policy_data["severity"],
            enabled=True,
            configuration=json.dumps(policy_data["configuration"]),
            created_by="System Administrator"
        )
        db.add(policy)
        policies.append(policy)
    
    db.flush()  # Get IDs
    print(f"✓ Created {len(policies)} policies")
    return policies

def create_api_connections(db: Session) -> List[APIConnection]:
    """Create realistic API connections."""
    print("Creating API connections...")
    
    connections = []
    for conn_data in API_CONNECTIONS:
        connection = APIConnection(
            name=conn_data["name"],
            provider=conn_data["provider"],
            description=conn_data["description"],
            base_url=conn_data["base_url"],
            api_version=conn_data["api_version"],
            authentication_type=conn_data["authentication_type"],
            credentials=conn_data["credentials"],
            sync_enabled=True,
            sync_interval_minutes=conn_data["sync_interval_minutes"],
            status=conn_data["status"],
            connection_test_url=f"{conn_data['base_url']}/health",
            rate_limit_requests="1000",
            rate_limit_window="hour",
            field_mappings=json.dumps({"default": "standard_mapping"}),
            supports_users=conn_data.get("supports_users", False),
            supports_devices=conn_data.get("supports_devices", False),
            supports_groups=conn_data.get("supports_groups", False),
            supports_realtime=conn_data.get("supports_realtime", False),
            created_by="System Administrator"
        )
        db.add(connection)
        connections.append(connection)
    
    db.flush()  # Get IDs
    
    # Add tags to connections
    for i, conn_data in enumerate(API_CONNECTIONS):
        connection = connections[i]
        for tag_enum in conn_data["tags"]:
            tag = APIConnectionTag(
                connection_id=connection.id,
                tag=tag_enum
            )
            db.add(tag)
    
    print(f"✓ Created {len(connections)} API connections")
    return connections

def create_access_grants(db: Session, users: List[CanonicalIdentity], count: int = 200):
    """Create realistic access grants."""
    print(f"Creating {count} access grants...")
    
    resources = [
        ("Production Database", "prod-db-01", AccessTypeEnum.DATABASE_ACCESS),
        ("AWS Console", "aws-account-123", AccessTypeEnum.ADMINISTRATIVE_ACCESS),
        ("Slack Admin", "slack-workspace", AccessTypeEnum.ADMINISTRATIVE_ACCESS),
        ("GitHub Repository", "company/repo", AccessTypeEnum.APPLICATION_ACCESS),
        ("Jira Admin", "jira-instance", AccessTypeEnum.ADMINISTRATIVE_ACCESS),
        ("Confluence", "confluence-wiki", AccessTypeEnum.APPLICATION_ACCESS),
        ("Salesforce", "salesforce-org", AccessTypeEnum.APPLICATION_ACCESS),
        ("Office 365 Admin", "office365-tenant", AccessTypeEnum.ADMINISTRATIVE_ACCESS),
        ("VPN Access", "corporate-vpn", AccessTypeEnum.NETWORK_ACCESS),
        ("Server Room", "datacenter-01", AccessTypeEnum.PHYSICAL_ACCESS)
    ]
    
    access_levels = ["Read", "Write", "Admin", "Full Control"]
    
    for i in range(count):
        user = random.choice(users)
        resource_name, resource_id, access_type = random.choice(resources)
        access_level = random.choice(access_levels)
        
        # Determine if access should be temporary
        expires_at = None
        if random.random() < 0.2:  # 20% temporary access
            expires_at = fake.date_time_between(start_date='now', end_date='+90d', tzinfo=timezone.utc)
        
        grant = AccessGrant(
            user_cid=user.cid,
            access_type=access_type,
            resource_name=resource_name,
            resource_identifier=resource_id,
            access_level=access_level,
            permissions=json.dumps({"permissions": ["read", "write"] if access_level in ["Write", "Admin", "Full Control"] else ["read"]}),
            reason=random.choice(list(AccessReasonEnum)),
            justification=f"Access required for {user.role} role",
            business_justification="Business requirement for daily operations",
            granted_at=fake.date_time_between(start_date='-180d', end_date='now', tzinfo=timezone.utc),
            expires_at=expires_at,
            granted_by=random.choice([u.full_name for u in users if "Manager" in u.role or "Director" in u.role]),
            source_system="Active Directory",
            status=AccessStatusEnum.ACTIVE,
            risk_level=random.choice(["Low", "Medium", "High", "Critical"]),
            compliance_tags=json.dumps(["SOX", "PCI"] if random.random() < 0.3 else [])
        )
        db.add(grant)
    
    print(f"✓ Created {count} access grants")

def create_activity_history(db: Session, users: List[CanonicalIdentity], devices: List[Device], count: int = 300):
    """Create realistic activity history."""
    print(f"Creating {count} activity history records...")
    
    activity_types = list(ActivityTypeEnum)
    source_systems = ["Active Directory", "Okta", "CrowdStrike", "Splunk", "Office 365", "Slack"]
    
    for i in range(count):
        user = random.choice(users)
        device = random.choice(devices) if random.random() < 0.7 else None
        activity_type = random.choice(activity_types)
        source_system = random.choice(source_systems)
        
        # Generate realistic descriptions based on activity type
        descriptions = {
            ActivityTypeEnum.LOGIN: f"User logged in from {fake.ipv4()}",
            ActivityTypeEnum.LOGOUT: f"User logged out after {random.randint(1, 8)} hours",
            ActivityTypeEnum.ACCESS_GRANTED: f"Access granted to {random.choice(['Production Database', 'AWS Console', 'Slack Admin'])}",
            ActivityTypeEnum.ACCESS_DENIED: f"Access denied to {random.choice(['Restricted System', 'Admin Panel', 'Sensitive Data'])}",
            ActivityTypeEnum.POLICY_VIOLATION: f"Policy violation detected: {random.choice(['Weak Password', 'Unencrypted Device', 'Unauthorized Software'])}",
            ActivityTypeEnum.DEVICE_CONNECTED: f"Device {device.name if device else 'Unknown'} connected to network",
            ActivityTypeEnum.DEVICE_DISCONNECTED: f"Device {device.name if device else 'Unknown'} disconnected from network",
            ActivityTypeEnum.COMPLIANCE_SCAN: f"Compliance scan completed - {random.choice(['Passed', 'Failed', 'Warning'])}",
            ActivityTypeEnum.DATA_ACCESS: f"Data accessed from {random.choice(['Database', 'File Share', 'Cloud Storage'])}",
            ActivityTypeEnum.CONFIGURATION_CHANGE: f"Configuration changed: {random.choice(['Password Policy', 'Access Rights', 'Device Settings'])}"
        }
        
        activity = ActivityHistory(
            user_cid=user.cid,
            device_id=device.id if device else None,
            activity_type=activity_type,
            source_system=source_system,
            source_ip=fake.ipv4(),
            user_agent=fake.user_agent(),
            description=descriptions.get(activity_type, f"Activity: {activity_type.value}"),
            timestamp=fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.utc),
            activity_metadata=json.dumps({
                "session_id": fake.uuid4(),
                "request_id": fake.uuid4(),
                "additional_context": "Generated by seeding script"
            }),
            risk_score=random.choice(["Low", "Medium", "High", "Critical"])
        )
        db.add(activity)
    
    print(f"✓ Created {count} activity history records")

def create_config_history(db: Session, users: List[CanonicalIdentity], devices: List[Device], policies: List[Policy], count: int = 150):
    """Create configuration change history."""
    print(f"Creating {count} configuration history records...")
    
    change_types = list(ConfigChangeTypeEnum)
    entities = []
    
    # Add some devices and policies to track changes
    for device in devices[:20]:  # Track changes for first 20 devices
        entities.append(("device", device.id))
    for policy in policies:
        entities.append(("policy", policy.id))
    
    for i in range(count):
        entity_type, entity_id = random.choice(entities)
        change_type = random.choice(change_types)
        user = random.choice(users)
        
        # Generate realistic field changes
        field_changes = {
            "device": [
                ("name", "Old Device Name", "New Device Name"),
                ("compliant", "false", "true"),
                ("vlan", "VLAN_100_CORPORATE", "VLAN_300_SECURE"),
                ("status", "DISCONNECTED", "CONNECTED")
            ],
            "policy": [
                ("enabled", "false", "true"),
                ("severity", "Medium", "High"),
                ("configuration", "old_config", "new_config")
            ]
        }
        
        field_name, old_value, new_value = random.choice(field_changes.get(entity_type, [("field", "old", "new")]))
        
        config_change = ConfigHistory(
            entity_type=entity_type,
            entity_id=entity_id,
            change_type=change_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_by=user.full_name,
            description=f"{change_type.value} {entity_type}: {field_name} changed from '{old_value}' to '{new_value}'"
        )
        db.add(config_change)
    
    print(f"✓ Created {count} configuration history records")

def create_api_sync_logs(db: Session, connections: List[APIConnection], count: int = 50):
    """Create API sync logs."""
    print(f"Creating {count} API sync logs...")
    
    sync_types = ["full", "incremental", "manual"]
    statuses = ["success", "error", "partial"]
    
    for i in range(count):
        connection = random.choice(connections)
        sync_type = random.choice(sync_types)
        status = random.choice(statuses)
        
        started_at = fake.date_time_between(start_date='-7d', end_date='now', tzinfo=timezone.utc)
        completed_at = started_at + timedelta(minutes=random.randint(1, 30))
        duration = (completed_at - started_at).total_seconds()
        
        sync_log = APISyncLog(
            connection_id=connection.id,
            sync_type=sync_type,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=str(int(duration)),
            status=status,
            records_processed=str(random.randint(10, 1000)),
            records_created=str(random.randint(0, 100)),
            records_updated=str(random.randint(0, 50)),
            records_failed=str(random.randint(0, 10)) if status in ["error", "partial"] else "0",
            error_message=fake.sentence() if status == "error" else None
        )
        db.add(sync_log)
    
    print(f"✓ Created {count} API sync logs")

def seed_database():
    """Main seeding function."""
    print("🌱 Starting modern database seeding...")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Clear existing data (in dependency order)
        print("🧹 Clearing existing data...")
        db.query(APISyncLog).delete()
        db.query(APIConnectionTag).delete()
        db.query(APIConnection).delete()
        db.query(AccessPattern).delete()
        db.query(AccessReview).delete()
        db.query(AccessAuditLog).delete()
        db.query(AccessGrant).delete()
        db.query(ActivityHistory).delete()
        db.query(ConfigHistory).delete()
        db.query(DeviceTag).delete()
        db.query(Device).delete()
        db.query(GroupMembership).delete()
        db.query(Account).delete()
        db.query(Policy).delete()
        db.query(CanonicalIdentity).delete()
        db.commit()
        print("✓ Existing data cleared")
        
        # Create data in dependency order
        print("\n👥 Creating enterprise users...")
        users = create_enterprise_users(db, count=100)
        db.commit()
        
        print("\n💻 Creating modern devices...")
        devices = create_modern_devices(db, users, count=150)
        db.commit()
        
        print("\n🏷️ Creating device tags...")
        create_device_tags(db, devices)
        db.commit()
        
        print("\n👥 Creating enterprise groups...")
        create_enterprise_groups(db, users)
        db.commit()
        
        print("\n📋 Creating enterprise policies...")
        policies = create_enterprise_policies(db)
        db.commit()
        
        print("\n🔌 Creating API connections...")
        connections = create_api_connections(db)
        db.commit()
        
        print("\n🔐 Creating access grants...")
        create_access_grants(db, users, count=200)
        db.commit()
        
        print("\n📊 Creating activity history...")
        create_activity_history(db, users, devices, count=300)
        db.commit()
        
        print("\n📝 Creating configuration history...")
        create_config_history(db, users, devices, policies, count=150)
        db.commit()
        
        print("\n🔄 Creating API sync logs...")
        create_api_sync_logs(db, connections, count=50)
        db.commit()
        
        print("\n" + "=" * 60)
        print("🎉 Modern database seeding completed successfully!")
        print(f"📊 Summary:")
        print(f"   • {len(users)} enterprise users")
        print(f"   • {len(devices)} modern devices")
        print(f"   • {len(policies)} enterprise policies")
        print(f"   • {len(connections)} API connections")
        print(f"   • 200+ access grants")
        print(f"   • 300+ activity records")
        print(f"   • 150+ configuration changes")
        print(f"   • 50+ API sync logs")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
