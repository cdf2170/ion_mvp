# Microsoft E5 Tenant Secure Integration Guide

## 🔐 **ZERO HARDCODED SECRETS APPROACH**

This guide shows you how to securely integrate your Microsoft E5 tenant without any credentials in your code or repository.

## **Step 1: Azure AD App Registration**

### 1.1 Create App Registration
```bash
# Go to Azure Portal > Azure Active Directory > App registrations > New registration
Name: "Identity Platform Connector"
Supported account types: "Accounts in this organizational directory only"
Redirect URI: Not needed for client credentials flow
```

### 1.2 Configure API Permissions
Add these **Application permissions** (not delegated):
```
Microsoft Graph:
- User.Read.All
- Group.Read.All  
- Device.Read.All
- Directory.Read.All
- DeviceManagementManagedDevices.Read.All
- AuditLog.Read.All (optional)
```

### 1.3 Grant Admin Consent
```bash
# In Azure Portal > Your App > API permissions
Click "Grant admin consent for [Your Organization]"
```

### 1.4 Create Client Secret
```bash
# In Azure Portal > Your App > Certificates & secrets > New client secret
Description: "Production API Secret"
Expires: 24 months (recommended)
# COPY THE SECRET VALUE - you won't see it again!
```

## **Step 2: Generate Encryption Key**

```bash
# Generate a secure encryption key for production
cd /home/chris/MVP
python backend/app/services/connectors/encryption.py generate-key
```

**Output example:**
```
Generated encryption key:
gAAAAABhZ1234567890abcdefghijklmnopqrstuvwxyz1234567890ABCDEFG=

Set this as CREDENTIAL_ENCRYPTION_KEY environment variable in production
```

## **Step 3: Railway Environment Variables**

### 3.1 Set Production Secrets
```bash
# Set the encryption key (from Step 2)
railway variables set CREDENTIAL_ENCRYPTION_KEY="gAAAAABhZ1234567890abcdefghijklmnopqrstuvwxyz1234567890ABCDEFG="

# Set Microsoft credentials (from Step 1)
railway variables set MICROSOFT_TENANT_ID="12345678-1234-1234-1234-123456789012"
railway variables set MICROSOFT_CLIENT_ID="87654321-4321-4321-4321-210987654321"
railway variables set MICROSOFT_CLIENT_SECRET="your-secret-from-azure"

# Optional: Set custom encryption password (more secure than default)
railway variables set MASTER_ENCRYPTION_PASSWORD="your-super-secure-master-password-here"
railway variables set ENCRYPTION_SALT="your-unique-salt-value-here"
```

### 3.2 Verify Environment Variables
```bash
railway variables
```

## **Step 4: Local Development Setup**

### 4.1 Create Local Environment File
```bash
# Create .env file (NEVER commit this)
cat > .env << 'EOF'
# Microsoft E5 Tenant (Development)
MICROSOFT_TENANT_ID=12345678-1234-1234-1234-123456789012
MICROSOFT_CLIENT_ID=87654321-4321-4321-4321-210987654321
MICROSOFT_CLIENT_SECRET=your-dev-secret-here

# Encryption (Development)
CREDENTIAL_ENCRYPTION_KEY=gAAAAABhZ1234567890abcdefghijklmnopqrstuvwxyz1234567890ABCDEFG=
MASTER_ENCRYPTION_PASSWORD=dev-password-change-in-prod
ENCRYPTION_SALT=dev-salt-change-in-prod

# Database (Development)
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5435/mvp_db
DEMO_API_TOKEN=token 21700
DEBUG=true
EOF

# Add .env to .gitignore
echo ".env" >> .gitignore
```

### 4.2 Install Dependencies
```bash
pip install -r requirements.txt
```

## **Step 5: Test the Integration**

### 5.1 Test Encryption
```bash
python backend/app/services/connectors/encryption.py test
```

### 5.2 Start the Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.3 Setup Microsoft Connection
```bash
# Use the API to setup your tenant (credentials will be encrypted)
curl -X POST "http://localhost:8000/v1/microsoft/setup" \
  -H "Authorization: Bearer token 21700" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "12345678-1234-1234-1234-123456789012",
    "client_id": "87654321-4321-4321-4321-210987654321", 
    "client_secret": "your-secret-here"
  }'
```

### 5.4 Test Connection Status
```bash
curl -H "Authorization: Bearer token 21700" \
  "http://localhost:8000/v1/microsoft/status"
```

### 5.5 Sync Data
```bash
curl -X POST "http://localhost:8000/v1/microsoft/sync" \
  -H "Authorization: Bearer token 21700" \
  -H "Content-Type: application/json" \
  -d '{"sync_type": "users_only"}'
```

## **Step 6: Deploy to Production**

### 6.1 Deploy Code
```bash
git add .
git commit -m "Add secure Microsoft E5 tenant integration

- Encrypted credential storage
- OAuth2 client credentials flow
- Secure environment variable management
- No hardcoded secrets in code"

git push
```

### 6.2 Setup Production Connection
```bash
# After Railway deployment, use production API
curl -X POST "https://your-app.railway.app/v1/microsoft/setup" \
  -H "Authorization: Bearer token 21700" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret"
  }'
```

## **🔒 Security Features**

### **1. Credential Encryption**
- All credentials encrypted with Fernet (AES 128)
- Encryption keys stored in environment variables
- PBKDF2 key derivation with 100,000 iterations

### **2. Zero Code Secrets**
- No hardcoded credentials anywhere in code
- Environment variables only in production
- Local .env files excluded from git

### **3. Token Management**
- OAuth2 access tokens cached securely
- Automatic token refresh
- 5-minute buffer before expiration

### **4. Audit Trail**
- All API calls logged
- Connection status monitoring
- Sync operation tracking

## **🚀 Available Endpoints**

```
POST /v1/microsoft/setup       # Setup E5 tenant connection
GET  /v1/microsoft/status      # Check connection status  
POST /v1/microsoft/sync        # Trigger data sync
DELETE /v1/microsoft/disconnect # Remove connection
```

## **📊 Data Sync Capabilities**

- **Users**: Full profile, department, manager, status
- **Groups**: Security groups, distribution lists, M365 groups
- **Devices**: Intune managed devices, compliance status
- **Audit Logs**: Sign-in events, security events (optional)

## **🔧 Troubleshooting**

### Connection Issues
```bash
# Check environment variables
railway variables

# Test encryption
python backend/app/services/connectors/encryption.py test

# Check logs
railway logs
```

### Permission Issues
- Ensure admin consent granted in Azure AD
- Verify application permissions are "Application" not "Delegated"
- Check tenant ID matches your organization

### Token Issues
- Client secret may have expired (check Azure AD)
- Tenant ID format should be GUID
- Client ID should be from your app registration

## **🎯 Production Checklist**

- [ ] App registration created in Azure AD
- [ ] Application permissions granted and admin consent given
- [ ] Client secret created and copied
- [ ] Encryption key generated
- [ ] Railway environment variables set
- [ ] Local .env file created and added to .gitignore
- [ ] Dependencies installed
- [ ] Connection tested locally
- [ ] Code deployed to Railway
- [ ] Production connection established
- [ ] Data sync tested

Your Microsoft E5 tenant is now securely integrated with zero hardcoded secrets! 🎉
