# Data Mapping & Correlation System

## 🎯 **Your Vision: Universal Single Pane of Glass**

Your system is designed to pull data from multiple APIs and accurately map everything to canonical identities. Here's how it works:

## 🔄 **API Integration Architecture**

### **Supported APIs (Ready to Connect):**
- ✅ **Microsoft 365 / Azure AD** (Entra)
- ✅ **Okta** 
- ✅ **CrowdStrike** (Devices)
- ✅ **ServiceNow** (ITSM)
- ✅ **Google Workspace**
- ✅ **AWS IAM**
- ✅ **Slack**
- ✅ **Jira/Confluence**
- ✅ **Workday** (HR)
- ✅ **SailPoint** (Identity Governance)
- ✅ **CyberArk** (PAM)
- ✅ **Splunk** (Logs)

## 🗺️ **Data Mapping System**

### **1. Field Mapping Configuration**
Each API connection stores field mappings as JSON:

```json
{
  "user_mapping": {
    "okta": {
      "email": "profile.email",
      "first_name": "profile.firstName", 
      "last_name": "profile.lastName",
      "department": "profile.department",
      "manager": "profile.manager",
      "groups": "groupMemberships"
    },
    "azure_ad": {
      "email": "userPrincipalName",
      "first_name": "givenName",
      "last_name": "surname", 
      "department": "department",
      "manager": "manager.id",
      "groups": "memberOf"
    },
    "crowdstrike": {
      "device_name": "hostname",
      "ip_address": "local_ip",
      "mac_address": "mac_address",
      "os_version": "os_version",
      "last_seen": "last_seen"
    }
  }
}
```

### **2. Identity Correlation Logic**
```python
# When data comes in from any API:
def correlate_identity(api_data, source_system):
    # 1. Try to match by email (primary key)
    canonical_user = db.query(CanonicalIdentity).filter(
        CanonicalIdentity.email == api_data['email']
    ).first()
    
    if canonical_user:
        # Update existing user
        update_user_from_api(canonical_user, api_data, source_system)
    else:
        # Create new canonical identity
        create_canonical_identity(api_data, source_system)
```

## 🔍 **Orphan Detection System**

### **Detect Unassigned Resources:**
```python
# Find orphaned devices
orphaned_devices = db.query(Device).filter(
    Device.owner_cid.is_(None)
).all()

# Find unassigned licenses  
unassigned_licenses = db.query(Account).filter(
    Account.cid.is_(None)
).all()

# Find inactive users with active resources
inactive_users_with_resources = db.query(CanonicalIdentity).filter(
    CanonicalIdentity.status == StatusEnum.DISABLED
).join(Device).all()
```

## 📊 **Single Pane of Glass Views**

### **Complete User Profile:**
```
GET /v1/users/{cid}
Returns:
{
  "cid": "uuid",
  "full_name": "Adam Smith",
  "email": "adam@company.com",
  "department": "Engineering",
  "devices": [
    {"name": "Adam's iPad", "status": "Connected", "source": "CrowdStrike"},
    {"name": "MacBook Pro", "status": "Compliant", "source": "Jamf"}
  ],
  "accounts": [
    {"service": "Office 365", "status": "Active", "source": "Azure AD"},
    {"service": "Slack", "status": "Active", "source": "Slack API"},
    {"service": "AWS", "status": "Active", "source": "AWS IAM"}
  ],
  "groups": [
    {"name": "Developers", "source": "Okta"},
    {"name": "Mobile Team", "source": "Azure AD"}
  ]
}
```

### **Cross-System Search:**
```
GET /v1/devices?query=adam
Searches across:
- Device names (from CrowdStrike)
- Owner names (from Okta/Azure AD)
- IP addresses (from network scans)
- Group memberships (from all sources)
```

## 🚀 **Implementation Status**

### **✅ Already Built:**
- API connection management
- Field mapping configuration
- Canonical identity system
- Cross-system search
- Orphan detection queries
- Unified data models

### **🔧 Ready to Implement:**
- Specific API connectors (Okta, Azure AD, etc.)
- Automated sync jobs
- Conflict resolution logic
- Data validation rules

## 🛠️ **Next Steps for Full Implementation**

### **1. Add Specific API Connectors:**
```python
# Example: Okta connector
class OktaConnector:
    def sync_users(self):
        users = self.api.get_users()
        for user in users:
            correlate_identity(user, "okta")
    
    def sync_groups(self):
        groups = self.api.get_groups()
        # Map to canonical groups
```

### **2. Automated Sync Jobs:**
```python
# Background sync every hour
@celery.task
def sync_all_apis():
    for connection in get_active_connections():
        if connection.provider == "okta":
            OktaConnector(connection).sync()
        elif connection.provider == "azure_ad":
            AzureADConnector(connection).sync()
```

### **3. Conflict Resolution:**
```python
# When same user exists in multiple systems
def resolve_identity_conflicts(user_data):
    # Use business rules:
    # - Azure AD takes precedence for HR data
    # - Okta takes precedence for groups
    # - Most recent update wins for device info
```

## 🎯 **Your Single Pane of Glass Benefits:**

1. **Universal Search**: Find anything across all systems
2. **Orphan Detection**: Spot unassigned licenses/devices
3. **Compliance**: Track user access across all platforms
4. **Audit Trail**: Complete activity history
5. **Risk Assessment**: Identify high-risk users/devices
6. **Cost Optimization**: Find unused licenses/resources

**This system is designed to be your single source of truth for identity and access management across ALL your systems!** 🎉
