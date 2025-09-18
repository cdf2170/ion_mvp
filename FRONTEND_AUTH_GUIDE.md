# Frontend Authentication Guide - Bearer Tokens Required

## The Issue: "Not authenticated" Error

Your frontend developer is getting "Not authenticated" because **ALL API endpoints require Bearer token authentication**.

## Which Endpoints Need Auth?

### NO AUTH REQUIRED:
- `GET /` (root)
- `GET /health` (legacy Railway health check)  
- `GET /v1/health` (versioned health check)
- `GET /oauth/*` (OAuth endpoints)

### AUTH REQUIRED (Bearer Token):
- `GET /v1/users`
- `GET /v1/devices` 
- `GET /v1/apis`
- `GET /v1/policies`
- `GET /v1/history`
- `POST /v1/apis`
- `PUT /v1/apis/{id}`
- `DELETE /v1/apis/{id}`
- **ALL other v1 endpoints**

## Authentication Methods

### Option 1: Demo Token (Quick Testing)
```javascript
const headers = {
  'Authorization': 'Bearer token 21700',
  'Content-Type': 'application/json'
};

fetch('https://api.privion.tech/v1/users', { headers })
  .then(r => r.json())
  .then(console.log);
```

### Option 2: OAuth Token (Production)
```javascript
// After OAuth flow (see frontend_oauth_example.html)
const oauthToken = localStorage.getItem('oauth_access_token');
const headers = {
  'Authorization': `Bearer ${oauthToken}`,
  'Content-Type': 'application/json'
};

fetch('https://api.privion.tech/v1/users', { headers })
  .then(r => r.json())
  .then(console.log);
```

## Common Mistakes

### WRONG - No Authorization Header:
```javascript
fetch('https://api.privion.tech/v1/users')  // Returns: {"detail":"Not authenticated"}
```

### WRONG - Missing "Bearer ":
```javascript
headers: { 'Authorization': 'token 21700' }  // Missing "Bearer " prefix
```

### WRONG - Wrong Header Name:
```javascript
headers: { 'Auth': 'Bearer token 21700' }     // Should be "Authorization"
headers: { 'X-API-Key': 'token 21700' }       // Wrong header type
```

### CORRECT - Proper Bearer Token:
```javascript
headers: { 'Authorization': 'Bearer token 21700' }  // ✅ Works!
```

## Testing Commands

### Test Without Auth (Will Fail):
```bash
curl https://api.privion.tech/v1/users
# Returns: {"detail":"Not authenticated"}
```

### Test With Auth (Will Work):
```bash
curl -H "Authorization: Bearer token 21700" https://api.privion.tech/v1/users
# Returns: {"users": [...], "total": 50, ...}
```

## Frontend Implementation Examples

### Fetch API:
```javascript
const API_BASE_URL = 'https://api.privion.tech';
const AUTH_TOKEN = 'token 21700'; // or OAuth token

async function apiCall(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${AUTH_TOKEN}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} - ${response.statusText}`);
  }
  
  return response.json();
}

// Usage:
const users = await apiCall('/v1/users');
const devices = await apiCall('/v1/devices');
```

### Axios:
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.privion.tech',
  headers: {
    'Authorization': 'Bearer token 21700',
    'Content-Type': 'application/json'
  }
});

// Usage:
const users = await api.get('/v1/users');
const devices = await api.get('/v1/devices');
```

### React Hook:
```javascript
import { useState, useEffect } from 'react';

function useAPI(endpoint) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`https://api.privion.tech${endpoint}`, {
      headers: {
        'Authorization': 'Bearer token 21700',
        'Content-Type': 'application/json'
      }
    })
    .then(r => r.json())
    .then(setData)
    .catch(setError)
    .finally(() => setLoading(false));
  }, [endpoint]);

  return { data, loading, error };
}

// Usage:
const { data: users } = useAPI('/v1/users');
```

## Quick Fix for Testing

**Tell your frontend developer to add this to EVERY API request:**

```javascript
headers: {
  'Authorization': 'Bearer token 21700'
}
```

## Summary

1. **ALL `/v1/*` endpoints require Bearer tokens**
2. **Use exact format**: `Authorization: Bearer token 21700`
3. **Health check works without auth**: `/v1/health` (no Bearer token needed)
4. **OAuth available**: Use `frontend_oauth_example.html` for OAuth flow

The "Not authenticated" error will disappear once Bearer tokens are added to requests!

**Environment Variable**: You can change the token by setting `DEMO_API_TOKEN=your-custom-token` in your environment.
