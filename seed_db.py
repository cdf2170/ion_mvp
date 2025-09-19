#!/usr/bin/env python3
"""
Database seeding script for MVP backend.
Populates the database with 50 fake users and their associated data.
"""

import sys
import os
from pathlib import Path
import random
from datetime import datetime, timedelta
from faker import Faker

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from backend.app.db.session import SessionLocal, create_tables
from backend.app.db.models import (
    CanonicalIdentity, Device, GroupMembership, Account, StatusEnum,
    DeviceStatusEnum, DeviceTagEnum, DeviceTag,
    Policy, PolicyTypeEnum, PolicySeverityEnum,
    ConfigHistory, ConfigChangeTypeEnum,
    ActivityHistory, ActivityTypeEnum,
    APIConnection, APIConnectionTag, APIProviderEnum, APIConnectionStatusEnum, APIConnectionTagEnum,
    APISyncLog
)


def seed_database():
    """Seed the database with fake data"""
    
    print("Creating database tables...")
    create_tables()
    
    print("Seeding database with fake data...")
    
    fake = Faker()
    db = SessionLocal()
    
    try:
        # Clear existing data (in dependency order)
        db.query(APISyncLog).delete()
        db.query(APIConnectionTag).delete()
        db.query(APIConnection).delete()
        db.query(ActivityHistory).delete()
        db.query(ConfigHistory).delete()
        db.query(Policy).delete()
        db.query(DeviceTag).delete()
        db.query(Account).delete()
        db.query(GroupMembership).delete()
        db.query(Device).delete()
        db.query(CanonicalIdentity).delete()
        db.commit()
        
        # Define some realistic departments and roles
        departments = [
            "Engineering", "Marketing", "Sales", "Human Resources", 
            "Finance", "Operations", "Legal", "IT", "Design", "Customer Support"
        ]
        
        roles = [
            "Software Engineer", "Senior Engineer", "Engineering Manager", "Director",
            "Marketing Manager", "Sales Representative", "Account Manager", "VP Sales",
            "HR Business Partner", "Recruiter", "Financial Analyst", "Controller",
            "Operations Manager", "Legal Counsel", "IT Administrator", "Security Engineer",
            "UX Designer", "Product Designer", "Customer Success Manager", "Support Specialist"
        ]
        
        device_types = [
            "MacBook Pro", "MacBook Air", "ThinkPad", "Surface Laptop", 
            "iPhone", "iPad", "Samsung Galaxy", "Desktop PC"
        ]
        
        group_names = [
            "Developers", "Managers", "Sales Team", "Marketing Team", "Finance Team",
            "HR Team", "IT Team", "Executive", "Remote Workers", "Full-time",
            "Part-time", "Contractors", "Security Team", "Design Team", "Support Team"
        ]
        
        services = [
            "Slack", "Microsoft 365", "Google Workspace", "Zoom", "Jira", "Confluence",
            "GitHub", "GitLab", "AWS", "Azure", "Salesforce", "HubSpot", "Notion",
            "Figma", "Adobe Creative Suite", "Dropbox", "Box", "Okta", "Auth0"
        ]
        
        print("Creating 50 users...")
        users = []
        
        for i in range(50):
            # Create user
            user = CanonicalIdentity(
                email=fake.email(),
                department=random.choice(departments),
                last_seen=fake.date_time_between(start_date='-30d', end_date='now'),
                status=random.choice([StatusEnum.ACTIVE, StatusEnum.DISABLED]) if i % 10 == 0 else StatusEnum.ACTIVE,
                full_name=fake.name(),
                role=random.choice(roles),
                manager=fake.name() if random.random() > 0.3 else None,
                location=fake.city() + ", " + fake.state(),
                created_at=fake.date_time_between(start_date='-2y', end_date='-30d')
            )
            
            db.add(user)
            db.flush()  # Get the CID
            users.append(user)
            
            # Create 1-4 devices per user
            num_devices = random.randint(1, 4)
            for _ in range(num_devices):
                # Use first name only to demonstrate the improvement feature
                device = Device(
                    name=f"{user.full_name.split()[0] if user.full_name else fake.first_name()}'s {random.choice(device_types)}",
                    last_seen=fake.date_time_between(start_date='-7d', end_date='now'),
                    compliant=random.choice([True, False]) if random.random() > 0.8 else True,
                    owner_cid=user.cid,
                    ip_address=fake.ipv4_private(),
                    mac_address=fake.mac_address(),
                    vlan=random.choice(["VLAN_100", "VLAN_200", "VLAN_300", "DMZ", "GUEST"]),
                    os_version=random.choice([
                        "Windows 11 Pro", "Windows 10 Enterprise", "macOS 14.1", "macOS 13.6",
                        "Ubuntu 22.04", "iOS 17.1", "Android 14", "iPadOS 17.1"
                    ]),
                    last_check_in=fake.date_time_between(start_date='-24h', end_date='now'),
                    status=random.choice([DeviceStatusEnum.CONNECTED, DeviceStatusEnum.DISCONNECTED, DeviceStatusEnum.UNKNOWN])
                )
                db.add(device)
                db.flush()  # Get device ID
                
                # Add 1-3 random tags to each device
                num_tags = random.randint(1, 3)
                available_tags = list(DeviceTagEnum)
                selected_tags = random.sample(available_tags, min(num_tags, len(available_tags)))
                for tag_enum in selected_tags:
                    tag = DeviceTag(device_id=device.id, tag=tag_enum)
                    db.add(tag)
            
            # Create 2-5 group memberships per user
            num_groups = random.randint(2, 5)
            selected_groups = random.sample(group_names, num_groups)
            for group_name in selected_groups:
                membership = GroupMembership(
                    cid=user.cid,
                    group_name=group_name
                )
                db.add(membership)
            
            # Create 3-8 accounts per user
            num_accounts = random.randint(3, 8)
            selected_services = random.sample(services, min(num_accounts, len(services)))
            for service in selected_services:
                account = Account(
                    service=service,
                    status=random.choice([StatusEnum.ACTIVE, StatusEnum.DISABLED]) if random.random() > 0.9 else StatusEnum.ACTIVE,
                    user_email=user.email,
                    cid=user.cid
                )
                db.add(account)
        
        # Create sample policies
        print("Creating sample policies...")
        policies_data = [
            {
                "name": "Password Complexity Policy",
                "description": "Enforces strong password requirements across all systems",
                "policy_type": PolicyTypeEnum.PASSWORD_POLICY,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"min_length": 12, "require_special_chars": true, "require_numbers": true}'
            },
            {
                "name": "Device Encryption Requirement",
                "description": "All company devices must have full disk encryption enabled",
                "policy_type": PolicyTypeEnum.DEVICE_COMPLIANCE,
                "severity": PolicySeverityEnum.CRITICAL,
                "enabled": True,
                "configuration": '{"encryption_algorithm": "AES-256", "tpm_required": true}'
            },
            {
                "name": "Network Access Control",
                "description": "Controls access to network resources based on user roles",
                "policy_type": PolicyTypeEnum.ACCESS_CONTROL,
                "severity": PolicySeverityEnum.MEDIUM,
                "enabled": True,
                "configuration": '{"default_action": "deny", "require_mfa": true}'
            },
            {
                "name": "Data Classification Standard",
                "description": "Guidelines for classifying and handling sensitive data",
                "policy_type": PolicyTypeEnum.DATA_CLASSIFICATION,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"levels": ["public", "internal", "confidential", "restricted"]}'
            },
            {
                "name": "Network Security Baseline",
                "description": "Basic network security requirements for all environments",
                "policy_type": PolicyTypeEnum.NETWORK_SECURITY,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": False,
                "configuration": '{"firewall_required": true, "intrusion_detection": true}'
            }
        ]
        
        for policy_data in policies_data:
            policy = Policy(
                name=policy_data["name"],
                description=policy_data["description"],
                policy_type=policy_data["policy_type"],
                severity=policy_data["severity"],
                enabled=policy_data["enabled"],
                configuration=policy_data["configuration"],
                created_by="System Administrator",
                created_at=fake.date_time_between(start_date='-6m', end_date='-1m'),
                updated_at=fake.date_time_between(start_date='-1m', end_date='now')
            )
            db.add(policy)
        
        # Create sample API connections
        print("Creating sample API connections...")
        api_connections_data = [
            {
                "name": "Okta Production",
                "provider": APIProviderEnum.OKTA,
                "description": "Main Okta instance for user authentication and SSO",
                "base_url": "https://company.okta.com",
                "api_version": "v1",
                "authentication_type": "api_key",
                "status": APIConnectionStatusEnum.CONNECTED,
                "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.CRITICAL, APIConnectionTagEnum.IDENTITY_SOURCE]
            },
            {
                "name": "Workday HR System",
                "provider": APIProviderEnum.WORKDAY,
                "description": "Employee data and organizational structure",
                "base_url": "https://impl.workday.com/company",
                "api_version": "v1",
                "authentication_type": "oauth2",
                "status": APIConnectionStatusEnum.CONNECTED,
                "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.HR_SYSTEM, APIConnectionTagEnum.BATCH_ONLY]
            },
            {
                "name": "CrowdStrike Endpoint Protection",
                "provider": APIProviderEnum.CROWDSTRIKE,
                "description": "Endpoint detection and response platform",
                "base_url": "https://api.crowdstrike.com",
                "api_version": "v1",
                "authentication_type": "oauth2",
                "status": APIConnectionStatusEnum.CONNECTED,
                "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.SECURITY_TOOL, APIConnectionTagEnum.DEVICE_SOURCE]
            },
            {
                "name": "Microsoft 365 Staging",
                "provider": APIProviderEnum.MICROSOFT_365,
                "description": "Testing environment for M365 integration",
                "base_url": "https://graph.microsoft.com",
                "api_version": "v1.0",
                "authentication_type": "oauth2",
                "status": APIConnectionStatusEnum.TESTING,
                "tags": [APIConnectionTagEnum.STAGING, APIConnectionTagEnum.NON_CRITICAL, APIConnectionTagEnum.IT_SYSTEM]
            },
            {
                "name": "Splunk Security Analytics",
                "provider": APIProviderEnum.SPLUNK,
                "description": "Security event monitoring and analytics",
                "base_url": "https://company.splunkcloud.com",
                "api_version": "v2",
                "authentication_type": "bearer_token",
                "status": APIConnectionStatusEnum.ERROR,
                "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.SECURITY_TOOL, APIConnectionTagEnum.HIGH_VOLUME]
            }
        ]
        
        for conn_data in api_connections_data:
            connection = APIConnection(
                name=conn_data["name"],
                provider=conn_data["provider"],
                description=conn_data["description"],
                base_url=conn_data["base_url"],
                api_version=conn_data["api_version"],
                authentication_type=conn_data["authentication_type"],
                credentials="encrypted_credentials_placeholder",
                sync_enabled=True,
                sync_interval_minutes="60",
                status=conn_data["status"],
                last_health_check=fake.date_time_between(start_date='-1d', end_date='now'),
                health_check_message="Connection successful" if conn_data["status"] == APIConnectionStatusEnum.CONNECTED else "Authentication failed",
                created_by="System Administrator",
                created_at=fake.date_time_between(start_date='-3m', end_date='-1m'),
                supports_users=True,
                supports_devices=conn_data["provider"] in [APIProviderEnum.CROWDSTRIKE],
                supports_groups=True,
                supports_realtime=False
            )
            db.add(connection)
            db.flush()  # Get connection ID
            
            # Add tags
            for tag_enum in conn_data["tags"]:
                tag = APIConnectionTag(connection_id=connection.id, tag=tag_enum)
                db.add(tag)
            
            # Create some sync logs for connected APIs
            if conn_data["status"] == APIConnectionStatusEnum.CONNECTED:
                for _ in range(random.randint(3, 8)):
                    sync_log = APISyncLog(
                        connection_id=connection.id,
                        sync_type=random.choice(["full", "incremental", "manual"]),
                        started_at=fake.date_time_between(start_date='-30d', end_date='now'),
                        completed_at=fake.date_time_between(start_date='-30d', end_date='now'),
                        status=random.choice(["success", "error", "partial"]),
                        records_processed=str(random.randint(10, 1000)),
                        records_created=str(random.randint(0, 50)),
                        records_updated=str(random.randint(5, 200)),
                        records_failed=str(random.randint(0, 5)),
                        duration_seconds=str(random.uniform(1.0, 30.0))
                    )
                    db.add(sync_log)
        
        # Create sample activity history
        print("Creating sample activity history...")
        devices = db.query(Device).all()
        for _ in range(200):  # Create 200 activity records
            user = random.choice(users)
            device = random.choice(user.devices) if user.devices else None
            
            activity = ActivityHistory(
                user_cid=user.cid,
                device_id=device.id if device else None,
                activity_type=random.choice(list(ActivityTypeEnum)),
                source_system=random.choice(["Okta", "Active Directory", "CrowdStrike", "VPN", "Firewall"]),
                source_ip=fake.ipv4(),
                user_agent=fake.user_agent(),
                description=f"User {user.full_name} performed {random.choice(['login', 'logout', 'file access', 'policy check'])}",
                timestamp=fake.date_time_between(start_date='-30d', end_date='now'),
                activity_metadata='{"browser": "Chrome", "os": "Windows", "location": "Office"}',
                risk_score=random.choice(["Low", "Medium", "High", "Critical"])
            )
            db.add(activity)
        
        # Create sample config history
        print("Creating sample configuration history...")
        for _ in range(100):  # Create 100 config change records
            user = random.choice(users)
            entity_type = random.choice(["user", "device", "policy"])
            
            if entity_type == "user":
                entity_id = user.cid
                field_name = random.choice(["department", "role", "status", "manager"])
                old_value = "Engineering" if field_name == "department" else "Active"
                new_value = "Marketing" if field_name == "department" else "Disabled"
            elif entity_type == "device":
                device = random.choice(devices)
                entity_id = device.id
                field_name = random.choice(["name", "compliant", "status", "vlan"])
                old_value = "VLAN_100" if field_name == "vlan" else "true"
                new_value = "VLAN_200" if field_name == "vlan" else "false"
            else:  # policy
                entity_id = random.choice(db.query(Policy).all()).id
                field_name = random.choice(["enabled", "severity", "configuration"])
                old_value = "true" if field_name == "enabled" else "Medium"
                new_value = "false" if field_name == "enabled" else "High"
            
            config_change = ConfigHistory(
                entity_type=entity_type,
                entity_id=entity_id,
                change_type=random.choice(list(ConfigChangeTypeEnum)),
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                changed_by=random.choice(["admin@company.com", "system", "automation"]),
                changed_at=fake.date_time_between(start_date='-30d', end_date='now'),
                description=f"Updated {field_name} from {old_value} to {new_value}"
            )
            db.add(config_change)
        
        # Commit all changes
        db.commit()
        print(f"Successfully seeded database with:")
        print(f"   - 50 users")
        print(f"   - {db.query(Device).count()} devices")
        print(f"   - {db.query(DeviceTag).count()} device tags")
        print(f"   - {db.query(GroupMembership).count()} group memberships")
        print(f"   - {db.query(Account).count()} accounts")
        print(f"   - {db.query(Policy).count()} policies")
        print(f"   - {db.query(APIConnection).count()} API connections")
        print(f"   - {db.query(APISyncLog).count()} sync logs")
        print(f"   - {db.query(ActivityHistory).count()} activity records")
        print(f"   - {db.query(ConfigHistory).count()} config changes")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
