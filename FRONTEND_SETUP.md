# Frontend Developer Setup Guide

## Quick Start for Frontend Development

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd MVP
```

### 2. Start the Backend API
```bash
# Install Python dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL
docker run -d --name mvp-postgres \
  -e POSTGRES_DB=mvp_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5435:5432 postgres:15

# Run database migrations
alembic upgrade head

# Seed with sample data (50 users, 110+ devices)
python seed_db.py

# Start the API server
python -m backend.app.main
```

### 3. API is Ready! 🚀
- **Base URL:** `http://localhost:8006`
- **API Docs:** `http://localhost:8006/docs` (interactive Swagger UI)
- **Health Check:** `http://localhost:8006/health`

### 4. Authentication
All API calls need this header:
```javascript
const headers = {
  'Authorization': 'Bearer demo-token-12345',
  'Content-Type': 'application/json'
}
```

## Frontend Integration

### Key API Endpoints for Your Dashboard

**Users (Identity Management):**
```javascript
// Get paginated user list with search/filters
GET /api/v1/users?page=1&page_size=20&query=john&department=Engineering

// Get complete user profile with devices/accounts
GET /api/v1/users/{cid}

// Update user info (rename, change dept, etc.)
PUT /api/v1/users/{cid}
// Body: {"department": "Security", "role": "CISO"}

// Merge duplicate users
POST /api/v1/users/merge
// Body: {"source_cid": "...", "target_cid": "...", "merge_devices": true}
```

**Devices & Compliance:**
```javascript
// Get devices with compliance filtering  
GET /api/v1/devices?compliant=false&owner_cid={cid}

// Get compliance dashboard data
GET /api/v1/devices/non-compliant/summary

// Update device (rename, reassign, fix compliance)
PUT /api/v1/devices/{device_id}
// Body: {"name": "John's New Laptop", "compliant": true}
```

### TypeScript Interfaces
All response schemas are documented in the main README.md. Key ones:

```typescript
interface UserListItem {
  cid: string;           // Canonical Identity UUID
  email: string;
  department: string;
  last_seen: string;     // ISO datetime
  status: "Active" | "Disabled";
}

interface UserDetail extends UserListItem {
  full_name: string;
  role: string;
  manager?: string;
  location?: string;
  created_at: string;
  devices: Device[];
  groups: GroupMembership[];
  accounts: Account[];
}

interface Device {
  id: string;
  name: string;
  last_seen: string;
  compliant: boolean;
}
```

### Sample Data Available
- 50 realistic users across 10 departments
- 110+ devices with mixed compliance status
- 168 group memberships (teams, roles)
- 283 external service accounts (Slack, AWS, etc.)

### Error Handling
Standard HTTP codes:
- `200`: Success
- `401`: Invalid/missing auth token
- `404`: Resource not found
- `422`: Validation error

## Perfect for Building...

✅ **User Dashboard** - List/search users with their devices and accounts  
✅ **Compliance Reports** - Show non-compliant devices by user/department  
✅ **Identity Management** - Merge duplicates, update user info  
✅ **Device Management** - Track and update device compliance  
✅ **Multi-Service View** - See all accounts per user across services  

The API is production-ready with pagination, filtering, search, and comprehensive error handling. Start building your IAM dashboard right away!

## Deploying to Production

### Frontend Deployment (Vercel)
Deploy your React/Next.js app to Vercel as usual:
```bash
npm run build
vercel deploy
```

### Backend Deployment Options

#### Option 1: Railway (Recommended)
```bash
npm install -g @railway/cli
railway login
railway init
railway add postgresql
railway deploy
```
Then update your frontend environment variables:
```env
NEXT_PUBLIC_API_URL=https://your-app.railway.app
NEXT_PUBLIC_API_TOKEN=demo-token-12345
```

#### Option 2: Docker (Any Platform)
```bash
# Build image
docker build -t mvp-backend .

# Deploy to your platform of choice
# (DigitalOcean, AWS, GCP, etc.)
```

#### Option 3: Render
- Connect GitHub repo to Render
- Auto-detects FastAPI
- Add PostgreSQL addon
- Set environment variables

### Environment Variables for Production
```env
DATABASE_URL=postgresql://user:password@host:port/db
DEMO_API_TOKEN=your-secure-token
ALLOWED_ORIGINS=https://your-frontend.vercel.app
DEBUG=false
```

### CORS Configuration
Backend is already configured for Vercel! Update `ALLOWED_ORIGINS` environment variable for your production domain.

## Need Help?
- Check `http://localhost:8006/docs` for interactive API documentation
- All schemas and examples are in the main README.md
- The API has comprehensive docstrings for every endpoint
