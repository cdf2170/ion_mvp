# API Endpoints Updated - Clean Versioned Routes

## ✅ Fixed Issues

1. **CORS for localhost:3001** - Now working properly
2. **Clean API versioning** - Removed redundant `/api` prefix while keeping `/v1` for version control
3. **Railway deployment configuration verified** - Working correctly

## 🚀 New API Endpoints Structure

### Production (Railway)
- **Base URL**: `https://api.privion.tech`
- **Health Check**: `https://api.privion.tech/v1/health`
- **Users**: `https://api.privion.tech/v1/users`
- **Devices**: `https://api.privion.tech/v1/devices`
- **API Management**: `https://api.privion.tech/v1/apis`
- **Policies**: `https://api.privion.tech/v1/policies`
- **History**: `https://api.privion.tech/v1/history`

### Local Development
- **Base URL**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/v1/health`
- **Users**: `http://localhost:8000/v1/users`
- **Devices**: `http://localhost:8000/v1/devices`
- **API Management**: `http://localhost:8000/v1/apis`
- **Policies**: `http://localhost:8000/v1/policies`
- **History**: `http://localhost:8000/v1/history`

## 🔐 Authentication

All endpoints (except `/v1/health` and `/`) require Bearer token authentication:

```bash
curl -H "Authorization: Bearer demo-token-12345" https://api.privion.tech/v1/users
```

## 🌐 CORS Configuration

The following origins are allowed:
- `http://localhost:3000`
- `http://localhost:3001` ✅ **Fixed**
- `http://localhost:5173`
- `https://ion-app-rose.vercel.app`
- `https://app.privion.tech`
- `https://api.privion.tech`

## 📝 Frontend Configuration

Update your frontend API base URLs to:

### For Production
```javascript
const API_BASE_URL = "https://api.privion.tech";
```

### For Development
```javascript
const API_BASE_URL = "http://localhost:8000";
```

### Example Usage
```javascript
// Old (redundant): https://api.privion.tech/api/v1/users
// New (clean + versioned): https://api.privion.tech/v1/users

fetch(`${API_BASE_URL}/v1/users`, {
  headers: {
    'Authorization': 'Bearer demo-token-12345'
  }
});
```

## 🔄 Deployment

The changes are ready to deploy to Railway. The Railway configuration in `railway.json` and `nixpacks.toml` is already correctly set up.

## ✅ Verification Commands

```bash
# Test health endpoint
curl https://api.privion.tech/v1/health

# Test users endpoint with auth
curl -H "Authorization: Bearer demo-token-12345" https://api.privion.tech/v1/users

# Test CORS from localhost:3001
curl -H "Origin: http://localhost:3001" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Authorization" \
     -X OPTIONS https://api.privion.tech/v1/users
```
