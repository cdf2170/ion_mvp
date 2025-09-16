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
from backend.app.db.models import CanonicalIdentity, Device, GroupMembership, Account, StatusEnum


def seed_database():
    """Seed the database with fake data"""
    
    print("Creating database tables...")
    create_tables()
    
    print("Seeding database with fake data...")
    
    fake = Faker()
    db = SessionLocal()
    
    try:
        # Clear existing data
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
                device = Device(
                    name=f"{fake.first_name()}'s {random.choice(device_types)}",
                    last_seen=fake.date_time_between(start_date='-7d', end_date='now'),
                    compliant=random.choice([True, False]) if random.random() > 0.8 else True,
                    owner_cid=user.cid
                )
                db.add(device)
            
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
        
        # Commit all changes
        db.commit()
        print(f"✅ Successfully seeded database with:")
        print(f"   - 50 users")
        print(f"   - {db.query(Device).count()} devices")
        print(f"   - {db.query(GroupMembership).count()} group memberships")
        print(f"   - {db.query(Account).count()} accounts")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
