#!/usr/bin/env python3
"""
Simple database seeding script that creates just users without devices
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from backend.app.db.session import SessionLocal, create_tables
from backend.app.db.models import CanonicalIdentity, StatusEnum
from faker import Faker

def simple_seed():
    """Seed just basic users without devices"""
    
    print("Creating database tables...")
    create_tables()
    
    print("Seeding with simple user data...")
    
    fake = Faker()
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(CanonicalIdentity).delete()
        db.commit()
        
        # Create 10 simple users
        for i in range(10):
            user = CanonicalIdentity(
                email=f"user{i+1}@techcorp.com",
                full_name=fake.name(),
                department=fake.random_element(["Engineering", "Sales", "Marketing", "IT"]),
                role=fake.job(),
                manager=fake.name() if i > 2 else None,
                location=fake.city(),
                status=StatusEnum.ACTIVE
            )
            db.add(user)
        
        db.commit()
        print(f"✅ Successfully seeded {10} users")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    simple_seed()
