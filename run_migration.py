#!/usr/bin/env python3
"""
Railway migration script - runs Alembic migrations and seeds data if needed.
This script can be run manually on Railway or triggered via API.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        return False

def main():
    print("🚀 Starting Railway Migration Process")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.executable}")
    
    # Set environment for Railway
    os.environ["PYTHONPATH"] = "/app"
    
    # Run Alembic migration
    migration_success = run_command(
        "alembic upgrade head",
        "Running Alembic database migration"
    )
    
    if not migration_success:
        print("❌ Migration failed, stopping here")
        sys.exit(1)
    
    # Check if we need to seed data (if access_grants table is empty)
    check_data = run_command(
        'python3 -c "from backend.app.db.session import SessionLocal; from backend.app.db.models import AccessGrant; db = SessionLocal(); count = db.query(AccessGrant).count(); print(f\'Access grants count: {count}\'); db.close(); exit(0 if count > 0 else 1)"',
        "Checking if access data exists"
    )
    
    if not check_data:
        print("📊 No access data found, running database seeding...")
        seed_success = run_command(
            "python3 seed_db.py",
            "Seeding database with access management data"
        )
        
        if seed_success:
            print("✅ Database migration and seeding completed successfully!")
        else:
            print("⚠️ Migration succeeded but seeding failed")
    else:
        print("📊 Access data already exists, skipping seeding")
        print("✅ Database migration completed successfully!")

if __name__ == "__main__":
    main()
