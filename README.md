# MVP Backend

Production-ready FastAPI backend with PostgreSQL for user and device management.

## Features

- **FastAPI** with automatic API documentation
- **PostgreSQL** database with SQLAlchemy 2.x ORM
- **Alembic** database migrations
- **Bearer token authentication** for API security
- **CORS** configured for frontend integration
- **Pagination, filtering, and search** on user endpoints
- **Database seeding** with realistic fake data

## API Endpoints

### Users (Identity Management)
- `GET /api/v1/users` - List users with pagination, filtering, and search
  - Query params: `page`, `page_size`, `status`, `department`, `query`
- `GET /api/v1/users/{cid}` - Get detailed user information with devices, groups, accounts
- `PUT /api/v1/users/{cid}` - Update user identity information (rename, change dept, etc.)
- `POST /api/v1/users/merge` - Merge two user identities (consolidate duplicates)
- `POST /api/v1/users/scan/{cid}` - Simulate compliance scan

### Devices
- `GET /api/v1/devices` - List devices with pagination, filtering, and search
  - Query params: `page`, `page_size`, `compliant`, `owner_cid`, `query`
- `GET /api/v1/devices/{device_id}` - Get detailed device information
- `PUT /api/v1/devices/{device_id}` - Update device (rename, change compliance, reassign owner)
- `DELETE /api/v1/devices/{device_id}` - Delete device
- `GET /api/v1/devices/non-compliant/summary` - Get compliance summary by user

### System
- `GET /` - API information
- `GET /health` - Health check endpoint

## Frontend Integration Guide

### Authentication
All API endpoints require Bearer token authentication:
```javascript
const headers = {
  'Authorization': 'Bearer demo-token-12345',
  'Content-Type': 'application/json'
}
```

### Key Data Types for Frontend

#### UserListItemSchema (for user tables)
```typescript
interface UserListItem {
  cid: string;           // Canonical Identity UUID
  email: string;         // Primary email
  department: string;    // Department name
  last_seen: string;     // ISO datetime
  status: "Active" | "Disabled";
}
```

#### UserDetailSchema (for user detail views)
```typescript
interface UserDetail {
  cid: string;
  email: string;
  full_name: string;
  department: string;
  role: string;
  manager?: string;
  location?: string;
  last_seen: string;
  status: "Active" | "Disabled";
  created_at: string;
  devices: Device[];
  groups: GroupMembership[];
  accounts: Account[];
}
```

#### DeviceSchema
```typescript
interface Device {
  id: string;            // Device UUID
  name: string;          // Human-readable name
  last_seen: string;     // ISO datetime
  compliant: boolean;    // Compliance status
}
```

### Common API Patterns

#### Pagination
All list endpoints return:
```typescript
interface PaginatedResponse<T> {
  items: T[];           // users/devices for current page
  total: number;        // total matching items
  page: number;         // current page (1-based)
  page_size: number;    // items per page
  total_pages: number;  // total pages
}
```

#### Error Handling
API returns standard HTTP status codes:
- `200`: Success
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (invalid/missing token)
- `404`: Not Found
- `422`: Validation Error

#### Example API Calls

**Get users with search:**
```javascript
const response = await fetch('/api/v1/users?page=1&page_size=20&query=john&department=Engineering', {
  headers
});
const data = await response.json();
```

**Update user information:**
```javascript
const response = await fetch(`/api/v1/users/${cid}`, {
  method: 'PUT',
  headers,
  body: JSON.stringify({
    department: 'Marketing',
    role: 'Senior Manager'
  })
});
```

**Merge duplicate users:**
```javascript
const response = await fetch('/api/v1/users/merge', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    source_cid: 'uuid-to-merge-from',
    target_cid: 'uuid-to-merge-into',
    merge_devices: true,
    merge_accounts: true,
    merge_groups: true
  })
});
```

**Get compliance summary:**
```javascript
const response = await fetch('/api/v1/devices/non-compliant/summary', {
  headers
});
// Returns users with non-compliant device counts
```

## Quick Start

> **👨‍💻 Frontend Developer?** See [FRONTEND_SETUP.md](FRONTEND_SETUP.md) for a streamlined setup guide!

### 1. Set up the environment

```bash
# Clone or navigate to the project
cd /home/chris/MVP

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure environment

```bash
# Copy example environment file
cp env.example .env

# Edit .env with your settings (optional, defaults work for local development)
```

### 3. Start PostgreSQL

```bash
# Start PostgreSQL with Docker Compose
docker-compose up -d

# Wait for PostgreSQL to be ready
docker-compose logs postgres
```

### 4. Run database migrations

```bash
# Run Alembic migrations
alembic upgrade head
```

### 5. Seed the database

```bash
# Populate with fake data (50 users)
python seed_db.py
```

### 6. Start the API server

```bash
# Start the FastAPI server
python -m backend.app.main

# Server will be available at: http://localhost:8006
# API documentation at: http://localhost:8006/docs
```

## Authentication

All `/api/v1/users/*` endpoints require Bearer token authentication.

**Default token:** `demo-token-12345`

Example request:
```bash
curl -H "Authorization: Bearer demo-token-12345" http://localhost:8006/api/v1/users
```

## Database Schema

### CanonicalIdentity
- Primary user identity with personal information
- Fields: cid, email, department, full_name, role, status, etc.

### Device
- User devices with compliance tracking
- Fields: id, name, last_seen, compliant, owner_cid

### GroupMembership
- User group assignments
- Fields: id, cid, group_name

### Account
- External service accounts
- Fields: id, service, status, user_email, cid

## Development

### Running migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Database operations

```bash
# Reset database and reseed
docker-compose down -v
docker-compose up -d
alembic upgrade head
python seed_db.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:password@localhost:5432/mvp_db` | PostgreSQL connection string |
| `DEMO_API_TOKEN` | `demo-token-12345` | Bearer token for API authentication |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS allowed origins (comma-separated) |
| `APP_NAME` | `MVP Backend` | Application name |
| `DEBUG` | `true` | Enable debug mode |

## Project Structure

```
MVP/
├── backend/
│   └── app/
│       ├── db/
│       │   ├── models.py      # SQLAlchemy models
│       │   └── session.py     # Database session management
│       ├── routers/
│       │   └── users.py       # User API endpoints
│       ├── security/
│       │   └── auth.py        # Authentication logic
│       ├── config.py          # Configuration management
│       ├── main.py           # FastAPI application
│       └── schemas.py        # Pydantic response models
├── alembic/                  # Database migrations
├── docker-compose.yml        # PostgreSQL setup
├── requirements.txt          # Python dependencies
├── seed_db.py               # Database seeding script
└── env.example              # Environment template
```

## Production Deployment

### Railway (Recommended)
See [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) for complete Railway deployment guide.

**Quick Railway Setup:**
```bash
npm install -g @railway/cli
railway login
railway init
railway add postgresql
railway up
```

### Manual Deployment
For other platforms:

1. Set `DEBUG=false` in environment variables
2. Use a secure `DEMO_API_TOKEN`
3. Configure proper `DATABASE_URL` for your PostgreSQL instance
4. Set appropriate `ALLOWED_ORIGINS` for your frontend domain
5. Use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app.main:app --bind 0.0.0.0:8006
```
