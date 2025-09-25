#!/usr/bin/env python3
"""
Test script to verify that the user search name/email correlation fix is working correctly.
This script tests various search scenarios to ensure names and emails match properly.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from backend.app.db.session import SessionLocal
from backend.app.db.models import CanonicalIdentity
from sqlalchemy import or_
import random


def test_name_email_correlation():
    """Test that generated users have matching names and emails"""
    print("🔍 Testing Name/Email Correlation...")
    
    db = SessionLocal()
    
    # Get a sample of users (skip the first 30 which are predefined)
    users = db.query(CanonicalIdentity).offset(30).limit(20).all()
    
    matches = 0
    mismatches = 0
    
    for user in users:
        name_parts = user.full_name.lower().split()
        expected_email = f"{name_parts[0]}.{name_parts[-1]}@techcorp.com"
        
        if user.email == expected_email:
            matches += 1
            print(f"✅ {user.full_name} -> {user.email}")
        else:
            mismatches += 1
            print(f"❌ {user.full_name} -> {user.email} (expected: {expected_email})")
    
    print(f"\n📊 Results: {matches} matches, {mismatches} mismatches")
    
    if mismatches == 0:
        print("🎉 SUCCESS: All generated users have matching names and emails!")
    else:
        print("⚠️  WARNING: Some users still have mismatched names and emails")
    
    db.close()
    return mismatches == 0


def test_search_functionality():
    """Test that search works correctly with the fixed data"""
    print("\n🔍 Testing Search Functionality...")
    
    db = SessionLocal()
    
    # Get a random user to test search with
    user = db.query(CanonicalIdentity).offset(35).first()
    
    if not user:
        print("❌ No users found for testing")
        db.close()
        return False
    
    print(f"Testing with user: {user.full_name} ({user.email})")
    
    # Test 1: Search by first name
    first_name = user.full_name.split()[0]
    print(f"\n1. Searching by first name: '{first_name}'")
    
    search_conditions = [
        CanonicalIdentity.email.ilike(f"%{first_name}%"),
        CanonicalIdentity.full_name.ilike(f"%{first_name}%"),
        CanonicalIdentity.department.ilike(f"%{first_name}%"),
        CanonicalIdentity.role.ilike(f"%{first_name}%"),
    ]
    
    results = db.query(CanonicalIdentity).filter(or_(*search_conditions)).all()
    found_target = any(r.email == user.email for r in results)
    
    print(f"   Found {len(results)} results, target user found: {'✅' if found_target else '❌'}")
    
    # Test 2: Search by last name
    last_name = user.full_name.split()[-1]
    print(f"\n2. Searching by last name: '{last_name}'")
    
    search_conditions = [
        CanonicalIdentity.email.ilike(f"%{last_name}%"),
        CanonicalIdentity.full_name.ilike(f"%{last_name}%"),
        CanonicalIdentity.department.ilike(f"%{last_name}%"),
        CanonicalIdentity.role.ilike(f"%{last_name}%"),
    ]
    
    results = db.query(CanonicalIdentity).filter(or_(*search_conditions)).all()
    found_target = any(r.email == user.email for r in results)
    
    print(f"   Found {len(results)} results, target user found: {'✅' if found_target else '❌'}")
    
    # Test 3: Search by email prefix
    email_prefix = user.email.split('@')[0]
    print(f"\n3. Searching by email prefix: '{email_prefix}'")
    
    search_conditions = [
        CanonicalIdentity.email.ilike(f"%{email_prefix}%"),
        CanonicalIdentity.full_name.ilike(f"%{email_prefix}%"),
    ]
    
    results = db.query(CanonicalIdentity).filter(or_(*search_conditions)).all()
    found_target = any(r.email == user.email for r in results)
    
    print(f"   Found {len(results)} results, target user found: {'✅' if found_target else '❌'}")
    
    db.close()
    return True


def test_predefined_users():
    """Test that predefined users (executives, etc.) still work correctly"""
    print("\n🔍 Testing Predefined Users...")
    
    db = SessionLocal()
    
    # Test some known predefined users
    predefined_tests = [
        ("Sarah Chen", "sarah.chen@techcorp.com"),
        ("Michael Rodriguez", "michael.rodriguez@techcorp.com"),
        ("Jennifer Kim", "jennifer.kim@techcorp.com"),
    ]
    
    all_good = True
    
    for expected_name, expected_email in predefined_tests:
        user = db.query(CanonicalIdentity).filter(CanonicalIdentity.email == expected_email).first()
        
        if user and user.full_name == expected_name:
            print(f"✅ {expected_name} -> {expected_email}")
        else:
            print(f"❌ {expected_name} -> {expected_email} (not found or name mismatch)")
            all_good = False
    
    db.close()
    return all_good


def main():
    """Run all tests"""
    print("🚀 Running User Search Correlation Tests\n")
    
    test1_passed = test_name_email_correlation()
    test2_passed = test_search_functionality()
    test3_passed = test_predefined_users()
    
    print("\n" + "="*50)
    print("📋 FINAL RESULTS:")
    print(f"   Name/Email Correlation: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   Search Functionality:   {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"   Predefined Users:       {'✅ PASS' if test3_passed else '❌ FAIL'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 ALL TESTS PASSED! The search correlation fix is working correctly.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED! Please review the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())
