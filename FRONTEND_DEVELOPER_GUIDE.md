# Frontend Developer Guide - CORS & Authentication Fix

## 🚨 **CORS Issue Identified & Fixed**

**Problem**: Railway production was filtering out `localhost:3001` origins due to production environment settings.

**Solution**: Updated CORS configuration to allow localhost origins in production for development workflow.

---

## ✅ **Correct API Configuration**

### **API Base URLs**
```javascript
// For development (local backend)
const API_BASE_URL = "http://localhost:8000";

// For production (Railway backend)  
const API_BASE_URL = "https://api.privion.tech";
```

### **Endpoint Structure** 
```javascript
// Health check (no auth)
GET ${API_BASE_URL}/health

// All other endpoints (auth required)
GET ${API_BASE_URL}/v1/users
GET ${API_BASE_URL}/v1/devices  
GET ${API_BASE_URL}/v1/apis
POST ${API_BASE_URL}/v1/apis
PUT ${API_BASE_URL}/v1/apis/{id}
DELETE ${API_BASE_URL}/v1/apis/{id}
```

---

## 🔐 **Authentication Format**

**CRITICAL**: Use exact format `Authorization: Bearer demo-token-12345`

```javascript
const headers = {
  'Authorization': 'Bearer demo-token-12345',
  'Content-Type': 'application/json'
};
```

**❌ Wrong formats that will fail:**
- `'Authorization': 'demo-token-12345'` (missing "Bearer ")
- `'X-API-Key': 'demo-token-12345'` (wrong header name)
- `'Auth': 'Bearer demo-token-12345'` (wrong header name)

---

## 🌐 **CORS Headers**

Your frontend requests from `http://localhost:3001` are now allowed. Make sure you're including:

```javascript
fetch(`${API_BASE_URL}/v1/users`, {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer demo-token-12345',
    'Content-Type': 'application/json'
  },
  credentials: 'include' // Important for CORS
});
```

---

## 🔧 **Common Issues & Solutions**

### **1. "Unauthenticated" Response**
- ✅ Check: Are you using `Authorization: Bearer demo-token-12345`?
- ✅ Check: Is the header spelled correctly? 
- ✅ Check: Are you sending the request to the right endpoint?

### **2. CORS Errors**
- ✅ Wait 2-3 minutes for Railway to deploy the fix
- ✅ Check: Are you using the correct origin `http://localhost:3001`?
- ✅ Check: Are you including `credentials: 'include'`?

### **3. 404 Not Found**
- ✅ Check: Are you using `/v1/users` (not `/api/v1/users`)?
- ✅ Check: Is your base URL correct?

---

## 📝 **Example Working Code**

### **Fetch API**
```javascript
const API_BASE_URL = "https://api.privion.tech";

async function getUsers() {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/users`, {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer demo-token-12345',
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.users;
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
}
```

### **Axios**
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.privion.tech',
  headers: {
    'Authorization': 'Bearer demo-token-12345',
    'Content-Type': 'application/json'
  },
  withCredentials: true
});

// Usage
const users = await api.get('/v1/users');
```

---

## 🧪 **Testing the Fix**

### **1. Test Health Endpoint (No Auth)**
```bash
curl https://api.privion.tech/health
# Should return: {"status": "healthy", ...}
```

### **2. Test CORS Preflight**
```bash
curl -H "Origin: http://localhost:3001" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Authorization" \
     -X OPTIONS https://api.privion.tech/v1/users
# Should return 200 OK with CORS headers
```

### **3. Test Authenticated Request**
```bash
curl -H "Origin: http://localhost:3001" \
     -H "Authorization: Bearer demo-token-12345" \
     https://api.privion.tech/v1/users
# Should return user data
```

---

## ⏰ **Timeline**

1. **Fixed & Pushed**: ✅ CORS fix committed and pushed to GitHub
2. **Railway Deploy**: 🔄 Auto-deploy in progress (2-3 minutes)
3. **Ready to Test**: ⏳ After Railway deployment completes

---

## 📞 **If Still Having Issues**

Try these debugging steps:

1. **Check Railway deployment status** - Wait for latest deploy
2. **Verify endpoint URL** - Use `/v1/users` not `/api/v1/users`
3. **Check browser network tab** - Look for exact error messages
4. **Test with curl first** - Use the test commands above
5. **Check browser console** - Look for specific CORS or auth errors

**Share these details if problems persist:**
- Exact error message from browser console
- Network tab showing request/response headers
- Code snippet of your fetch/axios request
- Which API endpoint you're trying to access

---

The CORS issue should be resolved once Railway finishes deploying the update! 🎉
