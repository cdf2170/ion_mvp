# Railway Database Seeding Guide

## Issue: Railway Production Database is Empty

**Problem**: Railway production has 0 devices while local has 139 devices. The Railway database needs to be seeded.

## Solution Options

### Option 1: Manual Seeding (Recommended)

Since Railway doesn't automatically run seeding scripts, you need to seed manually:

1. **Create a seeding endpoint** (temporary):

Add this to `backend/app/main.py`:

```python
@app.post("/v1/admin/seed-database")
def seed_database_endpoint(_: str = Depends(verify_token)):
    """Temporary endpoint to seed Railway database"""
    try:
        from seed_db import seed_database
        seed_database()
        return {"message": "Database seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
```

2. **Deploy to Railway** (push changes)

3. **Call the seeding endpoint**:
```bash
curl -X POST -H "Authorization: Bearer token 21700" https://api.privion.tech/v1/admin/seed-database
```

4. **Remove the endpoint** after seeding (for security)

### Option 2: Railway CLI Seeding

If you have Railway CLI installed:

```bash
# Connect to Railway project
railway login
railway link [your-project-id]

# Run seeding script
railway run python seed_db.py
```

### Option 3: Railway Shell Access

```bash
# Get shell access to Railway container
railway shell

# Run seeding script inside container
python seed_db.py
```

### Option 4: Database Migration with Seeding

Add seeding to Alembic migrations (more complex but automated).

## Quick Fix Implementation

Let me add the temporary seeding endpoint for you:

```python
# Add to main.py (temporary)
@app.post("/v1/admin/seed-database")
def seed_database_admin(credentials: HTTPAuthorizationCredentials = Security(security)):
    """TEMPORARY: Seed Railway database with sample data"""
    # Verify admin token
    if credentials.credentials != settings.demo_api_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Import and run seeding
        import subprocess
        import sys
        
        # Run seed script
        result = subprocess.run([sys.executable, "seed_db.py"], 
                              capture_output=True, text=True, cwd="/app")
        
        if result.returncode == 0:
            return {
                "message": "Database seeded successfully",
                "output": result.stdout
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Seeding failed: {result.stderr}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Seeding error: {str(e)}"
        )
```

## Expected Results After Seeding

Once seeded, Railway should have:
- ✅ **50 users** 
- ✅ **100-200 devices** (1-4 per user)
- ✅ **5 API connections**
- ✅ **5 policies**
- ✅ **Group memberships, accounts, activity history**

## Verification Commands

After seeding:

```bash
# Check users count
curl -H "Authorization: Bearer token 21700" https://api.privion.tech/v1/users | jq '.total'

# Check devices count  
curl -H "Authorization: Bearer token 21700" https://api.privion.tech/v1/devices | jq '.total'

# Check APIs count
curl -H "Authorization: Bearer token 21700" https://api.privion.tech/v1/apis | jq '.total'
```

## Security Note

**IMPORTANT**: Remove the seeding endpoint after use for security reasons.

## Why Railway Wasn't Seeded

Railway doesn't automatically run seeding scripts like the local `start_backend.sh` does. The local script has:

```bash
# Check if database has data
if ! python -c "from backend.app.db.session import SessionLocal; ..."; then
    echo "Seeding database with sample data..."
    python seed_db.py
fi
```

But Railway just runs the FastAPI app directly without this check.
