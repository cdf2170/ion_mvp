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
    DeviceStatusEnum, DeviceTagEnum, DeviceTag, GroupTypeEnum,
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
        
        # Realistic corporate device naming patterns
        device_naming_patterns = [
            # Corporate asset tag style
            {"pattern": "CORP-LAP-{:06d}", "types": ["MacBook Pro", "MacBook Air", "ThinkPad X1", "Surface Laptop"]},
            {"pattern": "CORP-DT-{:06d}", "types": ["Dell OptiPlex", "HP EliteDesk", "Mac Studio", "Workstation PC"]},
            {"pattern": "CORP-MOB-{:06d}", "types": ["iPhone 15 Pro", "iPhone 14", "Samsung Galaxy S24", "iPad Pro"]},
            
            # Location-based naming
            {"pattern": "SF-ENG-{:04d}", "types": ["MacBook Pro", "ThinkPad X1", "Surface Laptop"]},
            {"pattern": "NYC-FIN-{:04d}", "types": ["Dell Latitude", "Surface Pro", "MacBook Air"]},
            {"pattern": "LA-MKT-{:04d}", "types": ["MacBook Pro", "iMac", "Surface Studio"]},
            
            # Department-based naming
            {"pattern": "DEV-WS-{:03d}", "types": ["MacBook Pro 16\"", "ThinkPad P1", "Mac Studio", "Gaming PC"]},
            {"pattern": "EXEC-{:03d}", "types": ["MacBook Pro", "iPad Pro", "iPhone 15 Pro"]},
            {"pattern": "HR-LAPTOP-{:03d}", "types": ["MacBook Air", "Surface Laptop", "ThinkPad T14"]},
            
            # Generic asset tags
            {"pattern": "ASSET-{:08d}", "types": ["Various Models"]},
            {"pattern": "IT-{:05d}", "types": ["MacBook Pro", "ThinkPad", "Surface Laptop", "Desktop PC"]},
            {"pattern": "WS-{:06d}", "types": ["Workstation", "Desktop PC", "Mac Pro"]},
        ]
        
        # Enhanced groups with types and context
        groups_data = [
            # Department groups
            {"name": "Engineering Department", "type": "DEPARTMENT", "description": "All engineering staff", "source": "HR System"},
            {"name": "Marketing Department", "type": "DEPARTMENT", "description": "Marketing and communications team", "source": "HR System"},
            {"name": "Sales Department", "type": "DEPARTMENT", "description": "Sales and business development", "source": "HR System"},
            {"name": "Finance Department", "type": "DEPARTMENT", "description": "Finance and accounting team", "source": "HR System"},
            {"name": "IT Department", "type": "DEPARTMENT", "description": "Information technology team", "source": "HR System"},
            
            # Role-based groups
            {"name": "Senior Engineers", "type": "ROLE", "description": "Senior level engineering roles", "source": "Okta"},
            {"name": "Engineering Managers", "type": "ROLE", "description": "Engineering management roles", "source": "Okta"},
            {"name": "Directors", "type": "ROLE", "description": "Director level positions", "source": "Okta"},
            {"name": "VPs", "type": "ROLE", "description": "Vice President level positions", "source": "Okta"},
            
            # Access level groups
            {"name": "Admin Access", "type": "ACCESS_LEVEL", "description": "Administrative system access", "source": "Active Directory"},
            {"name": "Developer Access", "type": "ACCESS_LEVEL", "description": "Development environment access", "source": "Active Directory"},
            {"name": "Production Access", "type": "ACCESS_LEVEL", "description": "Production system access", "source": "Active Directory"},
            {"name": "Financial Data Access", "type": "ACCESS_LEVEL", "description": "Access to financial systems", "source": "Active Directory"},
            
            # Location groups
            {"name": "San Francisco Office", "type": "LOCATION", "description": "SF office employees", "source": "HR System"},
            {"name": "New York Office", "type": "LOCATION", "description": "NYC office employees", "source": "HR System"},
            {"name": "Remote Workers", "type": "LOCATION", "description": "Fully remote employees", "source": "HR System"},
            {"name": "Hybrid Workers", "type": "LOCATION", "description": "Hybrid work arrangement", "source": "HR System"},
            
            # Project groups
            {"name": "Project Alpha", "type": "PROJECT", "description": "Alpha project team members", "source": "Jira"},
            {"name": "Project Beta", "type": "PROJECT", "description": "Beta project team members", "source": "Jira"},
            {"name": "Infrastructure Team", "type": "PROJECT", "description": "Infrastructure and DevOps", "source": "Jira"},
            
            # Security clearance
            {"name": "Security Cleared", "type": "SECURITY_CLEARANCE", "description": "Employees with security clearance", "source": "Security System"},
            {"name": "PCI Compliance", "type": "SECURITY_CLEARANCE", "description": "PCI compliance training completed", "source": "Security System"},
            
            # Employment type
            {"name": "Full-time Employees", "type": "EMPLOYMENT_TYPE", "description": "Full-time permanent staff", "source": "HR System"},
            {"name": "Contractors", "type": "EMPLOYMENT_TYPE", "description": "Contract workers", "source": "HR System"},
            {"name": "Interns", "type": "EMPLOYMENT_TYPE", "description": "Intern positions", "source": "HR System"},
            
            # Team groups
            {"name": "Frontend Team", "type": "TEAM", "description": "Frontend development team", "source": "Slack"},
            {"name": "Backend Team", "type": "TEAM", "description": "Backend development team", "source": "Slack"},
            {"name": "DevOps Team", "type": "TEAM", "description": "DevOps and infrastructure team", "source": "Slack"},
            {"name": "Design Team", "type": "TEAM", "description": "UX/UI design team", "source": "Slack"},
            {"name": "QA Team", "type": "TEAM", "description": "Quality assurance team", "source": "Slack"},
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
            
            # Create 1-4 devices per user with realistic corporate naming
            num_devices = random.randint(1, 4)
            for device_num in range(num_devices):
                # Choose a random naming pattern
                naming_pattern = random.choice(device_naming_patterns)
                
                # Generate realistic corporate device name
                asset_number = random.randint(1, 999999)
                device_name = naming_pattern["pattern"].format(asset_number)
                
                # Choose device type based on naming pattern
                device_type = random.choice(naming_pattern["types"])
                
                # More realistic OS versions based on device type
                if "MacBook" in device_type or "Mac" in device_type or "iMac" in device_type:
                    os_options = ["macOS 14.2 Sonoma", "macOS 13.6 Ventura", "macOS 14.1 Sonoma"]
                elif "iPhone" in device_type:
                    os_options = ["iOS 17.2", "iOS 17.1", "iOS 16.7"]
                elif "iPad" in device_type:
                    os_options = ["iPadOS 17.2", "iPadOS 17.1", "iPadOS 16.7"]
                elif "Samsung" in device_type:
                    os_options = ["Android 14", "Android 13", "Android 12"]
                else:
                    os_options = ["Windows 11 Pro 23H2", "Windows 11 Enterprise", "Windows 10 Enterprise LTSC", "Ubuntu 22.04 LTS"]
                
                device = Device(
                    name=device_name,
                    last_seen=fake.date_time_between(start_date='-7d', end_date='now'),
                    compliant=random.choice([True, False]) if random.random() > 0.15 else True,  # Most devices compliant
                    owner_cid=user.cid,
                    ip_address=fake.ipv4_private(),
                    mac_address=fake.mac_address(),
                    vlan=random.choice([
                        "VLAN_100_CORPORATE", "VLAN_200_GUEST", "VLAN_300_SECURE", 
                        "VLAN_400_BYOD", "DMZ_ZONE", "QUARANTINE_VLAN"
                    ]),
                    os_version=random.choice(os_options),
                    last_check_in=fake.date_time_between(start_date='-24h', end_date='now'),
                    status=random.choice([
                        DeviceStatusEnum.CONNECTED, DeviceStatusEnum.CONNECTED, DeviceStatusEnum.CONNECTED,  # More likely to be connected
                        DeviceStatusEnum.DISCONNECTED, DeviceStatusEnum.UNKNOWN
                    ])
                )
                db.add(device)
                db.flush()  # Get device ID
                
                # Add contextual tags based on device name and user
                tags_to_add = []
                
                # Location-based tags
                if "SF-" in device_name or "San Francisco" in user.location:
                    tags_to_add.append(DeviceTagEnum.ON_SITE)
                elif "NYC-" in device_name or "Remote" in user.location:
                    tags_to_add.append(DeviceTagEnum.REMOTE)
                else:
                    tags_to_add.append(random.choice([DeviceTagEnum.REMOTE, DeviceTagEnum.ON_SITE]))
                
                # Role-based tags
                if "Executive" in user.role or "VP" in user.role or "Director" in user.role:
                    tags_to_add.append(DeviceTagEnum.EXECUTIVE)
                elif "Senior" in user.role or "Manager" in user.role:
                    tags_to_add.append(DeviceTagEnum.SLT)
                
                # Device type tags
                if "EXEC-" in device_name or "Executive" in user.role:
                    tags_to_add.append(DeviceTagEnum.VIP)
                elif "DEV-" in device_name or "Engineer" in user.role:
                    tags_to_add.append(DeviceTagEnum.PRODUCTION)
                elif "CORP-" in device_name:
                    tags_to_add.append(DeviceTagEnum.CORPORATE)
                else:
                    tags_to_add.append(random.choice([DeviceTagEnum.CORPORATE, DeviceTagEnum.BYOD]))
                
                # Employment type tags
                if "Contractor" in user.role or "Contract" in user.role:
                    tags_to_add.append(DeviceTagEnum.CONTRACT)
                else:
                    tags_to_add.append(DeviceTagEnum.FULL_TIME)
                
                # Add some random variation
                if random.random() > 0.7:  # 30% chance
                    tags_to_add.append(random.choice([DeviceTagEnum.TESTING, DeviceTagEnum.PRODUCTION]))
                
                # Remove duplicates and add tags
                unique_tags = list(set(tags_to_add))
                for tag_enum in unique_tags:
                    tag = DeviceTag(device_id=device.id, tag=tag_enum)
                    db.add(tag)
            
            # Create 3-7 group memberships per user with enhanced context
            num_groups = random.randint(3, 7)
            selected_groups = random.sample(groups_data, num_groups)
            for group_data in selected_groups:
                membership = GroupMembership(
                    cid=user.cid,
                    group_name=group_data["name"],
                    group_type=GroupTypeEnum[group_data["type"]],
                    description=group_data["description"],
                    source_system=group_data["source"]
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
