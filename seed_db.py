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
    APISyncLog,
    # Access management models
    AccessGrant, AccessAuditLog, AccessReview, AccessPattern,
    AccessTypeEnum, AccessStatusEnum, AccessReasonEnum, AuditActionEnum
)


def seed_database():
    """Seed the database with fake data"""
    
    print("Creating database tables...")
    create_tables()
    
    print("Seeding database with fake data...")
    
    fake = Faker()
    db = SessionLocal()
    
    # Realistic demo company data
    company_domain = "techcorp.com"
    
    # Real-looking executive team and employees
    demo_employees = [
        {"name": "Sarah Chen", "email": "sarah.chen", "department": "Engineering", "role": "VP Engineering", "manager": None, "location": "San Francisco, CA"},
        {"name": "Michael Rodriguez", "email": "michael.rodriguez", "department": "Engineering", "role": "Senior Engineering Manager", "manager": "Sarah Chen", "location": "San Francisco, CA"},
        {"name": "Jennifer Kim", "email": "jennifer.kim", "department": "Engineering", "role": "Senior Software Engineer", "manager": "Michael Rodriguez", "location": "San Francisco, CA"},
        {"name": "David Thompson", "email": "david.thompson", "department": "Engineering", "role": "Software Engineer", "manager": "Michael Rodriguez", "location": "Austin, TX"},
        {"name": "Lisa Wang", "email": "lisa.wang", "department": "Engineering", "role": "DevOps Engineer", "manager": "Michael Rodriguez", "location": "Remote"},
        
        {"name": "Robert Johnson", "email": "robert.johnson", "department": "Sales", "role": "VP Sales", "manager": None, "location": "New York, NY"},
        {"name": "Amanda Foster", "email": "amanda.foster", "department": "Sales", "role": "Senior Account Executive", "manager": "Robert Johnson", "location": "New York, NY"},
        {"name": "Carlos Martinez", "email": "carlos.martinez", "department": "Sales", "role": "Account Executive", "manager": "Robert Johnson", "location": "Los Angeles, CA"},
        {"name": "Nicole Brown", "email": "nicole.brown", "department": "Sales", "role": "Sales Development Rep", "manager": "Amanda Foster", "location": "Chicago, IL"},
        
        {"name": "Emily Davis", "email": "emily.davis", "department": "Marketing", "role": "VP Marketing", "manager": None, "location": "Austin, TX"},
        {"name": "James Wilson", "email": "james.wilson", "department": "Marketing", "role": "Digital Marketing Manager", "manager": "Emily Davis", "location": "Austin, TX"},
        {"name": "Rachel Green", "email": "rachel.green", "department": "Marketing", "role": "Content Marketing Manager", "manager": "Emily Davis", "location": "Remote"},
        {"name": "Alex Turner", "email": "alex.turner", "department": "Marketing", "role": "Marketing Specialist", "manager": "James Wilson", "location": "Seattle, WA"},
        
        {"name": "Thomas Anderson", "email": "thomas.anderson", "department": "Finance", "role": "CFO", "manager": None, "location": "New York, NY"},
        {"name": "Maria Gonzalez", "email": "maria.gonzalez", "department": "Finance", "role": "Finance Manager", "manager": "Thomas Anderson", "location": "New York, NY"},
        {"name": "Kevin Lee", "email": "kevin.lee", "department": "Finance", "role": "Financial Analyst", "manager": "Maria Gonzalez", "location": "New York, NY"},
        
        {"name": "Susan Taylor", "email": "susan.taylor", "department": "Human Resources", "role": "VP People", "manager": None, "location": "San Francisco, CA"},
        {"name": "Brian Miller", "email": "brian.miller", "department": "Human Resources", "role": "HR Business Partner", "manager": "Susan Taylor", "location": "San Francisco, CA"},
        {"name": "Jessica Chen", "email": "jessica.chen", "department": "Human Resources", "role": "Recruiter", "manager": "Susan Taylor", "location": "Austin, TX"},
        
        {"name": "Mark Williams", "email": "mark.williams", "department": "IT", "role": "IT Director", "manager": None, "location": "San Francisco, CA"},
        {"name": "Jennifer Lopez", "email": "jennifer.lopez", "department": "IT", "role": "Senior IT Administrator", "manager": "Mark Williams", "location": "San Francisco, CA"},
        {"name": "Christopher Moore", "email": "christopher.moore", "department": "IT", "role": "Security Engineer", "manager": "Mark Williams", "location": "Remote"},
        
        {"name": "Ashley White", "email": "ashley.white", "department": "Design", "role": "Design Director", "manager": None, "location": "Los Angeles, CA"},
        {"name": "Daniel Kim", "email": "daniel.kim", "department": "Design", "role": "Senior UX Designer", "manager": "Ashley White", "location": "Los Angeles, CA"},
        {"name": "Samantha Jones", "email": "samantha.jones", "department": "Design", "role": "UI Designer", "manager": "Ashley White", "location": "Remote"},
        
        {"name": "Ryan Clark", "email": "ryan.clark", "department": "Customer Support", "role": "Support Manager", "manager": None, "location": "Austin, TX"},
        {"name": "Michelle Adams", "email": "michelle.adams", "department": "Customer Support", "role": "Senior Support Specialist", "manager": "Ryan Clark", "location": "Austin, TX"},
        {"name": "Jason Taylor", "email": "jason.taylor", "department": "Customer Support", "role": "Support Specialist", "manager": "Ryan Clark", "location": "Denver, CO"},
        
        {"name": "Laura Bennett", "email": "laura.bennett", "department": "Operations", "role": "Operations Director", "manager": None, "location": "Chicago, IL"},
        {"name": "Andrew Garcia", "email": "andrew.garcia", "department": "Operations", "role": "Operations Manager", "manager": "Laura Bennett", "location": "Chicago, IL"},
        {"name": "Stephanie Wright", "email": "stephanie.wright", "department": "Operations", "role": "Operations Specialist", "manager": "Andrew Garcia", "location": "Denver, CO"},
    ]
    
    # Fill out the remaining spots with realistic but generated data
    remaining_spots = 50 - len(demo_employees)
    for i in range(remaining_spots):
        # Generate consistent name and email - CRITICAL FIX for search functionality
        full_name = fake.name()
        name_parts = full_name.split()
        first_name = name_parts[0].lower()
        last_name = name_parts[-1].lower() if len(name_parts) > 1 else "user"

        # Create email that matches the generated name
        email_prefix = f"{first_name}.{last_name}"

        fake_employee = {
            "name": full_name,
            "email": email_prefix,  # This will match the name when @techcorp.com is added
            "department": fake.random_element(["Engineering", "Sales", "Marketing", "Finance", "IT", "Design", "Customer Support", "Operations"]),
            "role": fake.random_element([
                "Software Engineer", "Senior Engineer", "Marketing Specialist", "Sales Representative",
                "Financial Analyst", "IT Specialist", "Designer", "Support Specialist", "Operations Coordinator"
            ]),
            "manager": fake.name(),
            "location": fake.random_element([
                "San Francisco, CA", "New York, NY", "Austin, TX", "Los Angeles, CA",
                "Chicago, IL", "Seattle, WA", "Denver, CO", "Remote"
            ])
        }
        demo_employees.append(fake_employee)
    
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
        # Access management cleanup
        db.query(AccessPattern).delete()
        db.query(AccessReview).delete()
        db.query(AccessAuditLog).delete()
        db.query(AccessGrant).delete()
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
        
        # Professional corporate device naming patterns
        device_naming_patterns = [
            # Executive devices - clean naming
            {"pattern": "TC-EXEC-{:03d}", "types": ["MacBook Pro 16\"", "iPad Pro 12.9\"", "iPhone 15 Pro"]},
            
            # Engineering team devices
            {"pattern": "TC-DEV-{:03d}", "types": ["MacBook Pro 16\"", "Mac Studio", "ThinkPad P1 Gen 6"]},
            {"pattern": "TC-ENG-{:03d}", "types": ["MacBook Pro 14\"", "Dell XPS 15", "ThinkPad X1 Carbon"]},
            
            # Sales and Marketing devices
            {"pattern": "TC-SALES-{:03d}", "types": ["MacBook Air M2", "Surface Laptop 5", "ThinkPad T14s"]},
            {"pattern": "TC-MKT-{:03d}", "types": ["MacBook Pro 14\"", "iMac 24\"", "Surface Studio 2"]},
            
            # Finance and Operations
            {"pattern": "TC-FIN-{:03d}", "types": ["ThinkPad T14", "Dell Latitude 7430", "Surface Laptop 5"]},
            {"pattern": "TC-OPS-{:03d}", "types": ["Dell OptiPlex 7090", "HP EliteDesk 800", "MacBook Air"]},
            
            # IT and Security
            {"pattern": "TC-IT-{:03d}", "types": ["ThinkPad P15v", "MacBook Pro 16\"", "Dell Precision 5570"]},
            {"pattern": "TC-SEC-{:03d}", "types": ["ThinkPad X1 Extreme", "MacBook Pro 16\"", "Surface Laptop Studio"]},
            
            # Location-based for remote workers
            {"pattern": "TC-SF-{:03d}", "types": ["MacBook Pro 14\"", "iMac 24\"", "ThinkPad X1"]},
            {"pattern": "TC-NYC-{:03d}", "types": ["Surface Laptop 5", "ThinkPad T14", "MacBook Air"]},
            {"pattern": "TC-REMOTE-{:03d}", "types": ["MacBook Air M2", "ThinkPad T14s", "Surface Laptop 5"]},
            
            # Mobile devices
            {"pattern": "TC-MOBILE-{:03d}", "types": ["iPhone 15 Pro", "iPhone 14", "iPad Pro 11\"", "Samsung Galaxy S24"]}
        ]
        
        # Comprehensive enterprise groups and departments structure
        groups_data = [
            # Core Department Structure (from HR/Workday)
            {"name": "Engineering", "type": "DEPARTMENT", "description": "Software development, DevOps, and technical infrastructure teams", "source": "Workday"},
            {"name": "Sales", "type": "DEPARTMENT", "description": "Revenue generation, business development, and customer acquisition", "source": "Workday"},
            {"name": "Marketing", "type": "DEPARTMENT", "description": "Brand, demand generation, product marketing, and growth", "source": "Workday"},
            {"name": "Finance", "type": "DEPARTMENT", "description": "Financial planning, accounting, and business operations", "source": "Workday"},
            {"name": "Human Resources", "type": "DEPARTMENT", "description": "People operations, talent acquisition, and employee experience", "source": "Workday"},
            {"name": "IT", "type": "DEPARTMENT", "description": "Information technology and corporate systems", "source": "Workday"},
            {"name": "Operations", "type": "DEPARTMENT", "description": "Business operations, facilities, and administrative functions", "source": "Workday"},
            {"name": "Customer Support", "type": "DEPARTMENT", "description": "Customer success, technical support, and service delivery", "source": "Workday"},
            {"name": "Design", "type": "DEPARTMENT", "description": "Product design, user experience, and creative services", "source": "Workday"},
            {"name": "Legal", "type": "DEPARTMENT", "description": "Legal counsel, compliance, and risk management", "source": "Workday"},
            
            # Sub-Departments and Teams
            {"name": "Frontend Engineering", "type": "TEAM", "description": "Web and mobile application development", "source": "Okta"},
            {"name": "Backend Engineering", "type": "TEAM", "description": "API, microservices, and server-side development", "source": "Okta"},
            {"name": "Platform Engineering", "type": "TEAM", "description": "Infrastructure, CI/CD, and developer tools", "source": "Okta"},
            {"name": "Data Engineering", "type": "TEAM", "description": "Data pipelines, analytics, and ML infrastructure", "source": "Okta"},
            {"name": "Security Engineering", "type": "TEAM", "description": "Application security, infrastructure security, and compliance", "source": "Okta"},
            {"name": "QA Engineering", "type": "TEAM", "description": "Quality assurance, testing, and release validation", "source": "Okta"},
            
            # Sales Teams
            {"name": "Enterprise Sales", "type": "TEAM", "description": "Large enterprise customer sales", "source": "Salesforce"},
            {"name": "Mid-Market Sales", "type": "TEAM", "description": "Mid-market customer acquisition", "source": "Salesforce"},
            {"name": "SMB Sales", "type": "TEAM", "description": "Small and medium business sales", "source": "Salesforce"},
            {"name": "Sales Development", "type": "TEAM", "description": "Lead generation and qualification", "source": "Salesforce"},
            {"name": "Customer Success", "type": "TEAM", "description": "Customer retention and expansion", "source": "Salesforce"},
            
            # Executive and Leadership Roles
            {"name": "C-Suite", "type": "ROLE", "description": "Chief executive officers and company leadership", "source": "Okta"},
            {"name": "Vice Presidents", "type": "ROLE", "description": "VP-level executives and department heads", "source": "Okta"},
            {"name": "Directors", "type": "ROLE", "description": "Director-level management", "source": "Okta"},
            {"name": "Senior Managers", "type": "ROLE", "description": "Senior management and team leads", "source": "Okta"},
            {"name": "People Managers", "type": "ROLE", "description": "All employees with direct reports", "source": "Okta"},
            {"name": "Individual Contributors", "type": "ROLE", "description": "Non-management staff", "source": "Okta"},
            
            # Experience Levels
            {"name": "Senior Level (L5+)", "type": "ROLE", "description": "Senior and staff level employees", "source": "Okta"},
            {"name": "Mid Level (L3-L4)", "type": "ROLE", "description": "Experienced individual contributors", "source": "Okta"},
            {"name": "Junior Level (L1-L2)", "type": "ROLE", "description": "Entry-level and junior employees", "source": "Okta"},
            {"name": "Interns and Contractors", "type": "EMPLOYMENT_TYPE", "description": "Temporary and contract workers", "source": "Okta"},
            
            # Security and Access Levels
            {"name": "System Administrators", "type": "ACCESS_LEVEL", "description": "Full administrative access to corporate systems", "source": "Active Directory"},
            {"name": "Database Administrators", "type": "ACCESS_LEVEL", "description": "Database management and administrative access", "source": "Active Directory"},
            {"name": "Network Administrators", "type": "ACCESS_LEVEL", "description": "Network infrastructure management access", "source": "Active Directory"},
            {"name": "Security Administrators", "type": "ACCESS_LEVEL", "description": "Security tools and incident response access", "source": "Active Directory"},
            {"name": "Developer Access", "type": "ACCESS_LEVEL", "description": "Development tools and non-production environments", "source": "Active Directory"},
            {"name": "Production Access", "type": "ACCESS_LEVEL", "description": "Production system access with SOX compliance", "source": "Active Directory"},
            {"name": "Financial Systems Access", "type": "ACCESS_LEVEL", "description": "ERP, billing, and financial system access", "source": "Active Directory"},
            {"name": "HR Systems Access", "type": "ACCESS_LEVEL", "description": "HRIS and payroll system access", "source": "Active Directory"},
            {"name": "Customer Data Access", "type": "ACCESS_LEVEL", "description": "Customer database and CRM access", "source": "Active Directory"},
            
            # Security Clearance and Compliance
            {"name": "SOX Compliance Required", "type": "SECURITY_CLEARANCE", "description": "Roles requiring SOX compliance training and access", "source": "Compliance System"},
            {"name": "PCI DSS Authorized", "type": "SECURITY_CLEARANCE", "description": "Payment card industry data access", "source": "Compliance System"},
            {"name": "GDPR Data Handlers", "type": "SECURITY_CLEARANCE", "description": "European customer data access authorization", "source": "Compliance System"},
            {"name": "HIPAA Cleared", "type": "SECURITY_CLEARANCE", "description": "Healthcare data access clearance", "source": "Compliance System"},
            {"name": "Security Incident Response", "type": "SECURITY_CLEARANCE", "description": "Security incident response team members", "source": "Security Tools"},
            
            # Geographic and Location Groups
            {"name": "San Francisco HQ", "type": "LOCATION", "description": "San Francisco headquarters office", "source": "HR System"},
            {"name": "New York Office", "type": "LOCATION", "description": "New York City office location", "source": "HR System"},
            {"name": "Austin Office", "type": "LOCATION", "description": "Austin, Texas office location", "source": "HR System"},
            {"name": "Los Angeles Office", "type": "LOCATION", "description": "Los Angeles office location", "source": "HR System"},
            {"name": "Chicago Office", "type": "LOCATION", "description": "Chicago office location", "source": "HR System"},
            {"name": "Seattle Office", "type": "LOCATION", "description": "Seattle office location", "source": "HR System"},
            {"name": "Denver Office", "type": "LOCATION", "description": "Denver office location", "source": "HR System"},
            {"name": "Remote - US", "type": "LOCATION", "description": "US-based remote employees", "source": "HR System"},
            {"name": "Remote - International", "type": "LOCATION", "description": "International remote employees", "source": "HR System"},
            {"name": "Hybrid Workers", "type": "LOCATION", "description": "Employees with hybrid work arrangements", "source": "HR System"},
            
            # Project and Initiative Groups
            {"name": "Project Phoenix", "type": "PROJECT", "description": "Next-generation platform development", "source": "Jira"},
            {"name": "Project Modernization", "type": "PROJECT", "description": "Legacy system modernization initiative", "source": "Jira"},
            {"name": "AI/ML Initiative", "type": "PROJECT", "description": "Artificial intelligence and machine learning projects", "source": "Jira"},
            {"name": "Security Enhancement Program", "type": "PROJECT", "description": "Comprehensive security improvement initiative", "source": "Jira"},
            {"name": "Cloud Migration Team", "type": "PROJECT", "description": "Infrastructure cloud migration project", "source": "Jira"},
            {"name": "Mobile App Development", "type": "PROJECT", "description": "Mobile application development initiative", "source": "Jira"},
            {"name": "API Modernization", "type": "PROJECT", "description": "API architecture improvement project", "source": "Jira"},
            
            # Employment Types and Status
            {"name": "Full-Time Employees", "type": "EMPLOYMENT_TYPE", "description": "Regular full-time staff", "source": "Workday"},
            {"name": "Part-Time Employees", "type": "EMPLOYMENT_TYPE", "description": "Part-time staff members", "source": "Workday"},
            {"name": "Contractors", "type": "EMPLOYMENT_TYPE", "description": "External contractors and consultants", "source": "Workday"},
            {"name": "Interns", "type": "EMPLOYMENT_TYPE", "description": "Internship program participants", "source": "Workday"},
            {"name": "Temporary Staff", "type": "EMPLOYMENT_TYPE", "description": "Temporary and seasonal workers", "source": "Workday"},
            
            # Specialized Groups
            {"name": "On-Call Engineers", "type": "TEAM", "description": "Engineers participating in on-call rotation", "source": "PagerDuty"},
            {"name": "Open Source Contributors", "type": "TEAM", "description": "Employees contributing to open source projects", "source": "GitHub"},
            {"name": "Patent Committee", "type": "TEAM", "description": "Intellectual property and patent review team", "source": "Legal System"},
            {"name": "Diversity & Inclusion Council", "type": "TEAM", "description": "D&I initiatives and programming", "source": "HR System"},
            {"name": "Emergency Response Team", "type": "TEAM", "description": "Business continuity and emergency response", "source": "Security Tools"},
            {"name": "Ethics Committee", "type": "TEAM", "description": "Business ethics and compliance oversight", "source": "Compliance System"},
            
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
        
        for i, employee_data in enumerate(demo_employees):
            # Create user with realistic company email
            email = f"{employee_data['email']}@{company_domain}"
            
            user = CanonicalIdentity(
                email=email,
                department=employee_data['department'],
                last_seen=fake.date_time_between(start_date='-7d', end_date='now'),
                status=StatusEnum.ACTIVE if i < 45 else random.choice([StatusEnum.ACTIVE, StatusEnum.DISABLED]),  # Only 5 disabled users
                full_name=employee_data['name'],
                role=employee_data['role'],
                manager=employee_data['manager'],
                location=employee_data['location'],
                created_at=fake.date_time_between(start_date='-2y', end_date='-30d')
            )
            
            db.add(user)
            db.flush()  # Get the CID
            users.append(user)
            
            # Create 1-3 devices per user with smart assignment based on role
            if "VP" in user.role or "Director" in user.role or "CFO" in user.role:
                # Executives get premium devices
                num_devices = random.randint(2, 3)
                preferred_patterns = [p for p in device_naming_patterns if "EXEC" in p["pattern"]]
            elif "Engineer" in user.role or "Dev" in user.role:
                # Engineers get development workstations
                num_devices = random.randint(1, 2)
                preferred_patterns = [p for p in device_naming_patterns if "DEV" in p["pattern"] or "ENG" in p["pattern"]]
            elif user.department == "Sales":
                num_devices = random.randint(1, 2)
                preferred_patterns = [p for p in device_naming_patterns if "SALES" in p["pattern"]]
            elif user.department == "Marketing":
                num_devices = random.randint(1, 2)
                preferred_patterns = [p for p in device_naming_patterns if "MKT" in p["pattern"]]
            elif user.department == "Finance":
                num_devices = random.randint(1, 2)
                preferred_patterns = [p for p in device_naming_patterns if "FIN" in p["pattern"]]
            elif user.department == "IT":
                num_devices = random.randint(1, 3)
                preferred_patterns = [p for p in device_naming_patterns if "IT" in p["pattern"] or "SEC" in p["pattern"]]
            elif "Remote" in user.location:
                num_devices = random.randint(1, 2)
                preferred_patterns = [p for p in device_naming_patterns if "REMOTE" in p["pattern"]]
            else:
                num_devices = random.randint(1, 2)
                preferred_patterns = device_naming_patterns
            
            for device_num in range(num_devices):
                # Choose appropriate naming pattern for user
                if preferred_patterns:
                    naming_pattern = random.choice(preferred_patterns)
                else:
                    naming_pattern = random.choice(device_naming_patterns)
                
                # Generate realistic corporate device name with smaller numbers
                asset_number = random.randint(1, 999)
                device_name = naming_pattern["pattern"].format(asset_number)
                
                # Choose device type based on naming pattern
                device_type = random.choice(naming_pattern["types"])
                
                # Combine device type with OS version for frontend "Device Info"
                if "MacBook" in device_type or "Mac" in device_type or "iMac" in device_type:
                    os_base_options = ["macOS 14.2 Sonoma", "macOS 13.6 Ventura", "macOS 14.1 Sonoma"]
                    os_options = [f"{device_type} - {os}" for os in os_base_options]
                elif "iPhone" in device_type:
                    os_base_options = ["iOS 17.2", "iOS 17.1", "iOS 16.7"]
                    os_options = [f"{device_type} - {os}" for os in os_base_options]
                elif "iPad" in device_type:
                    os_base_options = ["iPadOS 17.2", "iPadOS 17.1", "iPadOS 16.7"]
                    os_options = [f"{device_type} - {os}" for os in os_base_options]
                elif "Samsung" in device_type:
                    os_base_options = ["Android 14", "Android 13", "Android 12"]
                    os_options = [f"{device_type} - {os}" for os in os_base_options]
                else:
                    # For ThinkPad, Dell, Surface, HP devices
                    os_base_options = ["Windows 11 Pro 23H2", "Windows 11 Enterprise", "Windows 10 Enterprise LTSC", "Ubuntu 22.04 LTS"]
                    os_options = [f"{device_type} - {os}" for os in os_base_options]
                
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
        
        # Create comprehensive enterprise policies
        print("Creating enterprise policies...")
        policies_data = [
            # Password Policies
            {
                "name": "Corporate Password Policy",
                "description": "Enterprise-wide password complexity and rotation requirements",
                "policy_type": PolicyTypeEnum.PASSWORD_POLICY,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"min_length": 12, "require_special_chars": true, "require_numbers": true, "require_uppercase": true, "max_age_days": 90, "history_count": 12}'
            },
            {
                "name": "Privileged Account Password Policy",
                "description": "Enhanced password requirements for administrative accounts",
                "policy_type": PolicyTypeEnum.PASSWORD_POLICY,
                "severity": PolicySeverityEnum.CRITICAL,
                "enabled": True,
                "configuration": '{"min_length": 16, "require_special_chars": true, "require_numbers": true, "max_age_days": 30, "require_mfa": true}'
            },
            
            # Device Compliance Policies
            {
                "name": "Corporate Device Encryption",
                "description": "Full disk encryption mandatory for all corporate devices",
                "policy_type": PolicyTypeEnum.DEVICE_COMPLIANCE,
                "severity": PolicySeverityEnum.CRITICAL,
                "enabled": True,
                "configuration": '{"encryption_algorithm": "AES-256", "tpm_required": true, "bitlocker_required": true, "filevault_required": true}'
            },
            {
                "name": "Mobile Device Management (MDM)",
                "description": "Security controls for mobile devices accessing corporate resources",
                "policy_type": PolicyTypeEnum.DEVICE_COMPLIANCE,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"require_pin": true, "allow_jailbreak": false, "require_remote_wipe": true, "min_os_version": "iOS 15.0"}'
            },
            {
                "name": "Endpoint Detection and Response (EDR)",
                "description": "Required security agents for all workstations and servers",
                "policy_type": PolicyTypeEnum.DEVICE_COMPLIANCE,
                "severity": PolicySeverityEnum.CRITICAL,
                "enabled": True,
                "configuration": '{"required_agents": ["CrowdStrike", "Windows Defender"], "real_time_monitoring": true, "auto_quarantine": true}'
            },
            {
                "name": "Software Update Policy",
                "description": "Mandatory security patches and software updates",
                "policy_type": PolicyTypeEnum.DEVICE_COMPLIANCE,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"critical_patches_days": 7, "security_patches_days": 30, "auto_update_enabled": true}'
            },
            
            # Access Control Policies
            {
                "name": "Multi-Factor Authentication (MFA)",
                "description": "MFA required for all corporate applications and VPN access",
                "policy_type": PolicyTypeEnum.ACCESS_CONTROL,
                "severity": PolicySeverityEnum.CRITICAL,
                "enabled": True,
                "configuration": '{"required_for": ["VPN", "Email", "Cloud Apps"], "allowed_methods": ["TOTP", "SMS", "Hardware Token"], "grace_period_hours": 0}'
            },
            {
                "name": "Remote Access Policy",
                "description": "Security controls for remote work and VPN access",
                "policy_type": PolicyTypeEnum.ACCESS_CONTROL,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"vpn_required": true, "split_tunnel_allowed": false, "session_timeout_hours": 8, "geo_blocking": ["CN", "RU", "IR"]}'
            },
            {
                "name": "Privileged Access Management (PAM)",
                "description": "Enhanced controls for administrative and privileged accounts",
                "policy_type": PolicyTypeEnum.ACCESS_CONTROL,
                "severity": PolicySeverityEnum.CRITICAL,
                "enabled": True,
                "configuration": '{"just_in_time_access": true, "session_recording": true, "approval_required": true, "max_session_hours": 4}'
            },
            {
                "name": "Guest Network Access",
                "description": "Security controls for visitor and contractor network access",
                "policy_type": PolicyTypeEnum.ACCESS_CONTROL,
                "severity": PolicySeverityEnum.MEDIUM,
                "enabled": True,
                "configuration": '{"network_isolation": true, "bandwidth_limit_mbps": 10, "session_duration_hours": 24, "sponsor_approval": true}'
            },
            
            # Data Classification Policies
            {
                "name": "Data Classification Standard",
                "description": "Corporate data classification levels and handling requirements",
                "policy_type": PolicyTypeEnum.DATA_CLASSIFICATION,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"levels": ["Public", "Internal", "Confidential", "Restricted"], "auto_classification": true, "dlp_enabled": true}'
            },
            {
                "name": "Customer Data Protection (GDPR/CCPA)",
                "description": "Privacy protection controls for customer personal information",
                "policy_type": PolicyTypeEnum.DATA_CLASSIFICATION,
                "severity": PolicySeverityEnum.CRITICAL,
                "enabled": True,
                "configuration": '{"pii_detection": true, "encryption_at_rest": true, "access_logging": true, "retention_days": 2555}'
            },
            {
                "name": "Financial Data Security (SOX)",
                "description": "Controls for financial data integrity and access",
                "policy_type": PolicyTypeEnum.DATA_CLASSIFICATION,
                "severity": PolicySeverityEnum.CRITICAL,
                "enabled": True,
                "configuration": '{"segregation_of_duties": true, "approval_workflow": true, "audit_trail": true, "encryption_required": true}'
            },
            
            # Network Security Policies
            {
                "name": "Network Segmentation Policy",
                "description": "VLAN segmentation and network isolation controls",
                "policy_type": PolicyTypeEnum.NETWORK_SECURITY,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"vlan_isolation": true, "inter_vlan_routing": false, "firewall_required": true, "default_deny": true}'
            },
            {
                "name": "Wireless Security Policy",
                "description": "Corporate WiFi security standards and guest network controls",
                "policy_type": PolicyTypeEnum.NETWORK_SECURITY,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"encryption": "WPA3-Enterprise", "certificate_auth": true, "guest_isolation": true, "psk_disabled": true}'
            },
            {
                "name": "Firewall and IDS Policy",
                "description": "Network perimeter security and intrusion detection requirements",
                "policy_type": PolicyTypeEnum.NETWORK_SECURITY,
                "severity": PolicySeverityEnum.CRITICAL,
                "enabled": True,
                "configuration": '{"next_gen_firewall": true, "ids_enabled": true, "log_retention_days": 365, "threat_intelligence": true}'
            },
            {
                "name": "DNS Security Policy",
                "description": "DNS filtering and security controls",
                "policy_type": PolicyTypeEnum.NETWORK_SECURITY,
                "severity": PolicySeverityEnum.MEDIUM,
                "enabled": True,
                "configuration": '{"dns_filtering": true, "malware_blocking": true, "category_blocking": ["gambling", "adult", "malware"], "dns_over_https": true}'
            },
            
            # Backup and Retention Policies
            {
                "name": "Data Backup and Recovery",
                "description": "Enterprise backup schedules and recovery procedures",
                "policy_type": PolicyTypeEnum.BACKUP_RETENTION,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"daily_backup": true, "offsite_backup": true, "retention_years": 7, "rto_hours": 4, "rpo_hours": 1}'
            },
            {
                "name": "Email Retention Policy",
                "description": "Email archiving and retention for compliance",
                "policy_type": PolicyTypeEnum.BACKUP_RETENTION,
                "severity": PolicySeverityEnum.MEDIUM,
                "enabled": True,
                "configuration": '{"retention_years": 7, "auto_archive_days": 365, "legal_hold_enabled": true, "search_enabled": true}'
            },
            {
                "name": "Log Retention Policy",
                "description": "Security and audit log retention requirements",
                "policy_type": PolicyTypeEnum.BACKUP_RETENTION,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": True,
                "configuration": '{"security_logs_years": 2, "audit_logs_years": 7, "siem_integration": true, "immutable_storage": true}'
            },
            
            # Draft/Development Policies
            {
                "name": "Cloud Security Framework (Draft)",
                "description": "Security controls for cloud infrastructure and SaaS applications",
                "policy_type": PolicyTypeEnum.ACCESS_CONTROL,
                "severity": PolicySeverityEnum.HIGH,
                "enabled": False,
                "configuration": '{"cspm_required": true, "sso_integration": true, "shadow_it_monitoring": true, "cloud_access_security_broker": true}'
            },
            {
                "name": "AI/ML Governance Policy (Under Review)",
                "description": "Governance framework for artificial intelligence and machine learning systems",
                "policy_type": PolicyTypeEnum.DATA_CLASSIFICATION,
                "severity": PolicySeverityEnum.MEDIUM,
                "enabled": False,
                "configuration": '{"model_validation": true, "bias_testing": true, "data_lineage": true, "explainability_required": true}'
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
                "name": "TechCorp Okta Production",
                "provider": APIProviderEnum.OKTA,
                "description": "Primary identity provider for SSO and user management",
                "base_url": "https://techcorp.okta.com",
                "api_version": "v1",
                "authentication_type": "api_key",
                "status": APIConnectionStatusEnum.CONNECTED,
                "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.CRITICAL, APIConnectionTagEnum.IDENTITY_SOURCE]
            },
            {
                "name": "TechCorp Workday HRIS",
                "provider": APIProviderEnum.WORKDAY,
                "description": "Human resources information system and employee directory",
                "base_url": "https://impl.workday.com/techcorp",
                "api_version": "v1",
                "authentication_type": "oauth2",
                "status": APIConnectionStatusEnum.CONNECTED,
                "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.HR_SYSTEM, APIConnectionTagEnum.BATCH_ONLY]
            },
            {
                "name": "TechCorp CrowdStrike Falcon",
                "provider": APIProviderEnum.CROWDSTRIKE,
                "description": "Endpoint detection and response for device security monitoring",
                "base_url": "https://api.crowdstrike.com",
                "api_version": "v1",
                "authentication_type": "oauth2",
                "status": APIConnectionStatusEnum.CONNECTED,
                "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.SECURITY_TOOL, APIConnectionTagEnum.DEVICE_SOURCE]
            },
            {
                "name": "TechCorp Microsoft 365",
                "provider": APIProviderEnum.MICROSOFT_365,
                "description": "Office 365 environment for email, SharePoint, and Teams",
                "base_url": "https://graph.microsoft.com",
                "api_version": "v1.0",
                "authentication_type": "oauth2",
                "status": APIConnectionStatusEnum.CONNECTED,
                "tags": [APIConnectionTagEnum.PRODUCTION, APIConnectionTagEnum.CRITICAL, APIConnectionTagEnum.IT_SYSTEM]
            },
            {
                "name": "TechCorp AWS Security Hub",
                "provider": APIProviderEnum.SPLUNK,
                "description": "Cloud security monitoring and compliance reporting",
                "base_url": "https://securityhub.us-west-2.amazonaws.com",
                "api_version": "v2",
                "authentication_type": "bearer_token",
                "status": APIConnectionStatusEnum.CONNECTED,
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
        
        # Create comprehensive access grants and audit logs
        print("Creating access grants and audit trails...")
        
        # Get all users for access assignment
        all_users = db.query(CanonicalIdentity).all()
        
        # Define enterprise resources and systems
        enterprise_resources = [
            # Production Systems
            {"name": "Production Database", "type": AccessTypeEnum.DATABASE_ACCESS, "risk": "Critical"},
            {"name": "AWS Production Console", "type": AccessTypeEnum.SYSTEM_ACCESS, "risk": "Critical"},
            {"name": "Kubernetes Production", "type": AccessTypeEnum.SYSTEM_ACCESS, "risk": "Critical"},
            {"name": "Production Deployment Pipeline", "type": AccessTypeEnum.SYSTEM_ACCESS, "risk": "High"},
            
            # Development Systems
            {"name": "Development Database", "type": AccessTypeEnum.DATABASE_ACCESS, "risk": "Medium"},
            {"name": "AWS Development Console", "type": AccessTypeEnum.SYSTEM_ACCESS, "risk": "Medium"},
            {"name": "GitHub Organization", "type": AccessTypeEnum.SYSTEM_ACCESS, "risk": "Medium"},
            {"name": "Docker Registry", "type": AccessTypeEnum.SYSTEM_ACCESS, "risk": "Low"},
            
            # Business Applications
            {"name": "Salesforce Admin", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "High"},
            {"name": "Slack Admin", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "Medium"},
            {"name": "Google Workspace Admin", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "High"},
            {"name": "Jira Project Admin", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "Medium"},
            {"name": "Confluence Space Admin", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "Low"},
            
            # Financial Systems
            {"name": "QuickBooks Admin", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "Critical"},
            {"name": "Stripe Dashboard", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "High"},
            {"name": "Banking Portal", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "Critical"},
            {"name": "Expense Management", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "Medium"},
            
            # HR Systems
            {"name": "Workday Admin", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "High"},
            {"name": "BambooHR Admin", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "High"},
            {"name": "Payroll System", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "Critical"},
            
            # Network and Infrastructure
            {"name": "VPN Server Admin", "type": AccessTypeEnum.NETWORK_ACCESS, "risk": "High"},
            {"name": "Office WiFi Admin", "type": AccessTypeEnum.NETWORK_ACCESS, "risk": "Medium"},
            {"name": "Firewall Management", "type": AccessTypeEnum.NETWORK_ACCESS, "risk": "Critical"},
            {"name": "Domain Controller", "type": AccessTypeEnum.SYSTEM_ACCESS, "risk": "Critical"},
            
            # Data and Analytics
            {"name": "Customer Data Warehouse", "type": AccessTypeEnum.DATA_ACCESS, "risk": "Critical"},
            {"name": "Analytics Platform", "type": AccessTypeEnum.DATA_ACCESS, "risk": "Medium"},
            {"name": "Business Intelligence Tools", "type": AccessTypeEnum.APPLICATION_ACCESS, "risk": "Medium"},
            
            # Physical Access
            {"name": "Server Room", "type": AccessTypeEnum.PHYSICAL_ACCESS, "risk": "Critical"},
            {"name": "Office Building", "type": AccessTypeEnum.PHYSICAL_ACCESS, "risk": "Low"},
            {"name": "Executive Floor", "type": AccessTypeEnum.PHYSICAL_ACCESS, "risk": "Medium"},
        ]
        
        # Create access grants with realistic patterns
        access_grants_created = []
        audit_logs_created = []
        
        for user in all_users:
            # Determine access based on user role and department
            user_resources = []
            
            # Base access for all users
            user_resources.extend([
                {"resource": "Office Building", "level": "Badge Access", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                {"resource": "Google Workspace Admin", "level": "User", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                {"resource": "Slack Admin", "level": "User", "reason": AccessReasonEnum.JOB_REQUIREMENT},
            ])
            
            # Department-specific access
            if user.department == "Engineering":
                user_resources.extend([
                    {"resource": "GitHub Organization", "level": "Developer", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "Development Database", "level": "Read/Write", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "AWS Development Console", "level": "Developer", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "Docker Registry", "level": "Push/Pull", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "Jira Project Admin", "level": "User", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                ])
                
                # Senior engineers get production access
                if "Senior" in user.role or "Lead" in user.role or "Principal" in user.role:
                    user_resources.extend([
                        {"resource": "Production Database", "level": "Read Only", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                        {"resource": "Production Deployment Pipeline", "level": "Deploy", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    ])
                
                # Engineering management gets admin access
                if "Manager" in user.role or "Director" in user.role or "VP" in user.role:
                    user_resources.extend([
                        {"resource": "AWS Production Console", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                        {"resource": "Kubernetes Production", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                        {"resource": "Server Room", "level": "Full Access", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    ])
            
            elif user.department == "Sales":
                user_resources.extend([
                    {"resource": "Salesforce Admin", "level": "User", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "Customer Data Warehouse", "level": "Read Only", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                ])
                
                if "Manager" in user.role or "Director" in user.role or "VP" in user.role:
                    user_resources.append(
                        {"resource": "Salesforce Admin", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT}
                    )
            
            elif user.department == "Finance":
                user_resources.extend([
                    {"resource": "QuickBooks Admin", "level": "User", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "Expense Management", "level": "User", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                ])
                
                if "Manager" in user.role or "Controller" in user.role or "CFO" in user.role:
                    user_resources.extend([
                        {"resource": "Banking Portal", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                        {"resource": "Stripe Dashboard", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    ])
            
            elif user.department == "Human Resources":
                user_resources.extend([
                    {"resource": "Workday Admin", "level": "User", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "BambooHR Admin", "level": "User", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                ])
                
                if "Manager" in user.role or "Director" in user.role:
                    user_resources.append(
                        {"resource": "Payroll System", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT}
                    )
            
            elif user.department == "IT":
                user_resources.extend([
                    {"resource": "Domain Controller", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "VPN Server Admin", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "Office WiFi Admin", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "Server Room", "level": "Full Access", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                ])
                
                if "Security" in user.role:
                    user_resources.append(
                        {"resource": "Firewall Management", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT}
                    )
            
            # Executive access
            if "VP" in user.role or "Chief" in user.role or "President" in user.role:
                user_resources.extend([
                    {"resource": "Executive Floor", "level": "Full Access", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "Business Intelligence Tools", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                    {"resource": "Analytics Platform", "level": "Admin", "reason": AccessReasonEnum.JOB_REQUIREMENT},
                ])
            
            # Create access grants for this user
            for access_info in user_resources:
                # Find the resource definition
                resource_def = next((r for r in enterprise_resources if r["name"] == access_info["resource"]), None)
                if not resource_def:
                    continue
                
                # Create the access grant
                granted_date = fake.date_time_between(start_date='-2y', end_date='-30d')
                
                # Determine if access expires (some permanent, some temporary)
                expires_at = None
                if random.random() < 0.3:  # 30% of access has expiration
                    expires_at = fake.date_time_between(start_date='now', end_date='+1y')
                
                # Determine compliance tags based on resource
                compliance_tags = []
                if resource_def["risk"] == "Critical":
                    compliance_tags = ["SOX", "PCI_DSS"]
                elif "Customer" in access_info["resource"] or "Data" in access_info["resource"]:
                    compliance_tags = ["GDPR", "CCPA"]
                elif "Financial" in access_info["resource"] or "Banking" in access_info["resource"]:
                    compliance_tags = ["SOX"]
                
                access_grant = AccessGrant(
                    user_cid=user.cid,
                    access_type=resource_def["type"],
                    resource_name=access_info["resource"],
                    resource_identifier=f"{access_info['resource'].lower().replace(' ', '_')}_{random.randint(100, 999)}",
                    access_level=access_info["level"],
                    permissions={"read": True, "write": "Admin" in access_info["level"], "admin": "Admin" in access_info["level"]},
                    reason=access_info["reason"],
                    justification=f"Required for {user.role} in {user.department} department",
                    business_justification=f"Essential access for job function and department responsibilities",
                    granted_at=granted_date,
                    expires_at=expires_at,
                    granted_by=random.choice(["IT Admin", "Department Manager", "System Automation"]),
                    approved_by=user.manager if user.manager else "Department Head",
                    source_system=random.choice(["Active Directory", "Manual Request", "Okta", "Workday"]),
                    status=random.choices(
                        [AccessStatusEnum.ACTIVE, AccessStatusEnum.EXPIRED, AccessStatusEnum.REVOKED],
                        weights=[85, 10, 5]
                    )[0],
                    risk_level=resource_def["risk"],
                    compliance_tags=compliance_tags,
                    is_emergency_access=random.random() < 0.05,  # 5% emergency access
                    next_review_due=fake.date_time_between(start_date='now', end_date='+6m'),
                )
                
                if access_grant.is_emergency_access:
                    access_grant.emergency_ticket = f"EMRG-{random.randint(1000, 9999)}"
                    access_grant.emergency_approver = "Security Team"
                
                db.add(access_grant)
                db.flush()  # Get the ID
                access_grants_created.append(access_grant)
                
                # Create initial audit log for the grant
                initial_audit = AccessAuditLog(
                    access_grant_id=access_grant.id,
                    user_cid=user.cid,
                    action=AuditActionEnum.ACCESS_GRANTED,
                    timestamp=granted_date,
                    resource_name=access_info["resource"],
                    resource_identifier=access_grant.resource_identifier,
                    access_type=resource_def["type"],
                    access_level=access_info["level"],
                    performed_by=access_grant.granted_by,
                    reason=access_info["reason"],
                    justification=access_grant.justification,
                    new_state={
                        "access_level": access_info["level"],
                        "permissions": access_grant.permissions,
                        "status": "ACTIVE"
                    },
                    source_system=access_grant.source_system,
                    ip_address="192.168.1.100",
                    is_emergency=access_grant.is_emergency_access,
                    compliance_tags=compliance_tags,
                    risk_assessment=resource_def["risk"],
                    record_hash="",  # Will be generated
                )
                
                # Generate cryptographic hash
                initial_audit.record_hash = initial_audit.generate_record_hash()
                initial_audit.signature = initial_audit.generate_signature("demo_secret_key_2024")
                initial_audit.is_sealed = True
                initial_audit.sealed_at = granted_date
                initial_audit.sealed_by = "System"
                
                db.add(initial_audit)
                audit_logs_created.append(initial_audit)
                
                # Add some historical audit events for this access
                if random.random() < 0.4:  # 40% chance of additional history
                    # Access review event
                    review_date = fake.date_time_between(start_date=granted_date, end_date='now')
                    review_audit = AccessAuditLog(
                        access_grant_id=access_grant.id,
                        user_cid=user.cid,
                        action=AuditActionEnum.ACCESS_REVIEWED,
                        timestamp=review_date,
                        resource_name=access_info["resource"],
                        access_type=resource_def["type"],
                        performed_by=random.choice(["Security Team", "Department Manager", "Compliance Officer"]),
                        reason=AccessReasonEnum.JOB_REQUIREMENT,
                        justification="Quarterly access review completed",
                        source_system="Manual Review",
                        compliance_tags=compliance_tags,
                        record_hash="",
                    )
                    review_audit.record_hash = review_audit.generate_record_hash()
                    review_audit.signature = review_audit.generate_signature("demo_secret_key_2024")
                    review_audit.is_sealed = True
                    
                    access_grant.last_reviewed_at = review_date
                    access_grant.last_reviewed_by = review_audit.performed_by
                    
                    db.add(review_audit)
                    audit_logs_created.append(review_audit)
                
                # Some access gets revoked
                if access_grant.status == AccessStatusEnum.REVOKED:
                    revoked_date = fake.date_time_between(start_date=granted_date, end_date='now')
                    revocation_audit = AccessAuditLog(
                        access_grant_id=access_grant.id,
                        user_cid=user.cid,
                        action=AuditActionEnum.ACCESS_REVOKED,
                        timestamp=revoked_date,
                        resource_name=access_info["resource"],
                        access_type=resource_def["type"],
                        performed_by=random.choice(["IT Admin", "Security Team", "HR"]),
                        reason=random.choice([
                            AccessReasonEnum.ROLE_CHANGED,
                            AccessReasonEnum.ACCESS_NO_LONGER_NEEDED,
                            AccessReasonEnum.POLICY_VIOLATION
                        ]),
                        justification="Access revoked per security policy",
                        previous_state={"status": "ACTIVE", "access_level": access_info["level"]},
                        new_state={"status": "REVOKED", "access_level": None},
                        source_system="Manual",
                        compliance_tags=compliance_tags,
                        record_hash="",
                    )
                    revocation_audit.record_hash = revocation_audit.generate_record_hash()
                    revocation_audit.signature = revocation_audit.generate_signature("demo_secret_key_2024")
                    revocation_audit.is_sealed = True
                    
                    access_grant.revoked_at = revoked_date
                    access_grant.revoked_by = revocation_audit.performed_by
                    access_grant.revocation_reason = revocation_audit.reason
                    access_grant.revocation_justification = revocation_audit.justification
                    
                    db.add(revocation_audit)
                    audit_logs_created.append(revocation_audit)
        
        # Create some access reviews
        print("Creating access reviews...")
        
        # Quarterly review
        quarterly_review = AccessReview(
            review_period_start=fake.date_time_between(start_date='-3m', end_date='-2m'),
            review_period_end=fake.date_time_between(start_date='-1m', end_date='now'),
            review_type="Quarterly",
            scope_description="Quarterly access review for all critical systems",
            users_in_scope=[str(user.cid) for user in all_users[:30]],
            systems_in_scope=["Production Database", "AWS Production Console", "Banking Portal"],
            status="Completed",
            completion_percentage=100,
            primary_reviewer="compliance@company.com",
            secondary_reviewers=["security@company.com", "audit@company.com"],
            total_access_reviewed=len(access_grants_created),
            access_certified=int(len(access_grants_created) * 0.9),
            access_revoked=int(len(access_grants_created) * 0.05),
            access_flagged=int(len(access_grants_created) * 0.05),
            compliance_framework="SOX",
            created_by="compliance@company.com",
            completed_at=fake.date_time_between(start_date='-1m', end_date='now')
        )
        db.add(quarterly_review)
        
        # Annual review (in progress)
        annual_review = AccessReview(
            review_period_start=fake.date_time_between(start_date='-1m', end_date='now'),
            review_period_end=fake.date_time_between(start_date='now', end_date='+1m'),
            review_type="Annual",
            scope_description="Annual comprehensive access review - all users and systems",
            users_in_scope=[str(user.cid) for user in all_users],
            systems_in_scope=[resource["name"] for resource in enterprise_resources],
            status="In Progress",
            completion_percentage=65,
            primary_reviewer="audit@company.com",
            secondary_reviewers=["compliance@company.com", "ciso@company.com"],
            total_access_reviewed=int(len(access_grants_created) * 0.65),
            access_certified=int(len(access_grants_created) * 0.6),
            access_revoked=int(len(access_grants_created) * 0.03),
            access_flagged=int(len(access_grants_created) * 0.02),
            compliance_framework="SOX",
            created_by="audit@company.com",
            due_date=fake.date_time_between(start_date='now', end_date='+1m')
        )
        db.add(annual_review)
        
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
        print(f"   - {db.query(AccessGrant).count()} access grants")
        print(f"   - {db.query(AccessAuditLog).count()} audit log entries")
        print(f"   - {db.query(AccessReview).count()} access reviews")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
