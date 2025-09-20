# Frontend Relational Data Guide

## Overview

This guide shows all the relational data available through our APIs. Your frontend can access fully populated objects with all related data in single API calls - no need for multiple requests to build complete views.

## 🎯 Key Concept: "Copy & Paste" Development

Each API endpoint returns complete objects with all related data included. You can literally copy the response structure and use it directly in your frontend components.

---

## 👥 User Management - Complete Relational Data

### Get User with All Related Data
```http
GET /users/{cid}
```

**Response includes EVERYTHING:**
```json
{
  "cid": "123e4567-e89b-12d3-a456-426614174000",
  "email": "john.doe@company.com",
  "full_name": "John Doe",
  "department": "Engineering",
  "role": "Senior Developer",
  "manager": "Jane Smith",
  "location": "San Francisco",
  "status": "Active",
  "last_seen": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  
  // 🔗 ALL USER'S DEVICES with realistic corporate naming (no separate API call needed)
  "devices": [
    {
      "id": "device-uuid-1",
      "name": "CORP-LAP-001234",              // Corporate asset tag
      "status": "Connected",
      "compliant": true,
      "ip_address": "192.168.1.100",
      "mac_address": "00:1B:44:11:3A:B7",
      "vlan": "VLAN_100_CORPORATE",
      "os_version": "macOS 14.2 Sonoma",
      "last_check_in": "2024-01-15T10:25:00Z",
      "tags": [
        {"id": "tag-1", "tag": "Corporate"},
        {"id": "tag-2", "tag": "Executive"},
        {"id": "tag-3", "tag": "On-Site"}
      ]
    },
    {
      "id": "device-uuid-2", 
      "name": "SF-ENG-0042",                  // Location + department naming
      "status": "Connected",
      "compliant": true,
      "ip_address": "10.0.1.50",
      "mac_address": "A4:C3:F0:85:AC:2D",
      "vlan": "VLAN_300_SECURE",
      "os_version": "Windows 11 Pro 23H2",
      "last_check_in": "2024-01-15T09:15:00Z",
      "tags": [
        {"id": "tag-4", "tag": "Production"},
        {"id": "tag-5", "tag": "Full-Time"},
        {"id": "tag-6", "tag": "On-Site"}
      ]
    }
  ],
  
  // 🔗 ALL GROUP MEMBERSHIPS with enhanced context (no separate API call needed)
  "groups": [
    {
      "id": "group-1", 
      "group_name": "Engineering Department",
      "group_type": "Department",
      "description": "All engineering staff",
      "source_system": "HR System"
    },
    {
      "id": "group-2", 
      "group_name": "Senior Engineers",
      "group_type": "Role",
      "description": "Senior level engineering roles",
      "source_system": "Okta"
    },
    {
      "id": "group-3", 
      "group_name": "Production Access",
      "group_type": "Access Level",
      "description": "Production system access",
      "source_system": "Active Directory"
    },
    {
      "id": "group-4", 
      "group_name": "San Francisco Office",
      "group_type": "Location",
      "description": "SF office employees",
      "source_system": "HR System"
    }
  ],
  
  // 🔗 ALL EXTERNAL ACCOUNTS (no separate API call needed)
  "accounts": [
    {"id": "account-1", "service": "Slack", "status": "Active", "user_email": "john.doe@company.com"},
    {"id": "account-2", "service": "AWS", "status": "Active", "user_email": "john.doe@company.com"}
  ]
}
```

### List Users (Paginated)
```http
GET /users?page=1&page_size=50&department=Engineering&status=Active
```

**Perfect for data tables:**
```json
{
  "users": [
    {
      "cid": "123e4567-e89b-12d3-a456-426614174000",
      "email": "john.doe@company.com",
      "department": "Engineering",
      "last_seen": "2024-01-15T10:30:00Z",
      "status": "Active"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

---

## 👥 Enhanced Group System - No More Generic "Groups"!

**PROBLEM SOLVED**: Instead of generic "group" names, we now have **contextual, categorized groups** with full metadata:

### Group Types Available:
- **Department** - Engineering Department, Marketing Department, etc.
- **Role** - Senior Engineers, Engineering Managers, Directors, etc.
- **Access Level** - Admin Access, Production Access, Financial Data Access, etc.
- **Location** - San Francisco Office, Remote Workers, Hybrid Workers, etc.
- **Project** - Project Alpha, Infrastructure Team, etc.
- **Security Clearance** - Security Cleared, PCI Compliance, etc.
- **Employment Type** - Full-time Employees, Contractors, Interns, etc.
- **Team** - Frontend Team, Backend Team, DevOps Team, etc.

### Each Group Includes:
```json
{
  "id": "group-uuid",
  "group_name": "Production Access",           // Descriptive name
  "group_type": "Access Level",               // Category/type
  "description": "Production system access",   // What this group is for
  "source_system": "Active Directory"         // Where it came from
}
```

### Frontend Benefits:
- **Filter by group type**: Show only "Department" groups, or only "Access Level" groups
- **Group by category**: Organize groups in UI by type (Departments, Roles, Access, etc.)
- **Show context**: Display descriptions so users understand what each group means
- **Track sources**: Know which system each group came from for troubleshooting

---

## 💻 Device Management - Complete Relational Data

### Get Device with Owner Information
```http
GET /devices/{device_id}
```

**Response includes OWNER DATA (showing why owner info is crucial):**
```json
{
  "id": "device-uuid-1",
  "name": "ASSET-00847291",                    // Cryptic corporate name
  "status": "Connected",
  "compliant": false,
  "last_seen": "2024-01-15T10:30:00Z",
  
  // 🔗 OWNER INFORMATION (no separate user lookup needed)
  // This is WHY owner info matters - you'd never know who owns "ASSET-00847291"!
  "owner_cid": "123e4567-e89b-12d3-a456-426614174000",
  "owner_name": "Sarah Johnson",               // Who actually uses this device
  "owner_email": "sarah.j@company.com",       // How to contact them
  "owner_department": "Marketing",             // Which team for compliance
  
  // Network & System Info
  "ip_address": "192.168.1.100",
  "mac_address": "00:1B:44:11:3A:B7",
  "vlan": "VLAN_400_BYOD",                     // More descriptive VLAN names
  "os_version": "Windows 11 Pro 23H2",        // Detailed OS versions
  "last_check_in": "2024-01-15T10:25:00Z",
  
  // 🔗 ALL DEVICE TAGS with context (no separate API call needed)
  "tags": [
    {"id": "tag-1", "tag": "BYOD"},            // Bring Your Own Device
    {"id": "tag-2", "tag": "Remote"},          // Location-based
    {"id": "tag-3", "tag": "Full-Time"}       // Employment type
  ]
}
```

### List Devices (Paginated with Filters)
```http
GET /devices?page=1&page_size=50&compliant=false&status=Connected&owner_department=Engineering
```

**Perfect for device management dashboards:**
```json
{
  "devices": [
    {
      "id": "device-uuid-1",
      "name": "John's MacBook Pro",
      "owner_name": "John Doe",
      "owner_email": "john.doe@company.com",
      "owner_department": "Engineering",
      "status": "Connected",
      "compliant": false,
      "last_seen": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### 🏢 Realistic Corporate Device Naming

**Why Owner Info Matters**: Our seed data now generates realistic corporate device names that demonstrate why owner information is crucial:

#### Corporate Asset Tag Style:
- `CORP-LAP-001234` - Corporate laptop #001234
- `CORP-DT-005678` - Corporate desktop #005678  
- `CORP-MOB-009876` - Corporate mobile device #009876

#### Location-Based Naming:
- `SF-ENG-0042` - San Francisco Engineering device #42
- `NYC-FIN-0123` - New York Finance device #123
- `LA-MKT-0789` - Los Angeles Marketing device #789

#### Department-Based Naming:
- `DEV-WS-001` - Development workstation #001
- `EXEC-042` - Executive device #042
- `HR-LAPTOP-007` - HR laptop #007

#### Generic Asset Tags:
- `ASSET-00847291` - Generic asset tag
- `IT-12345` - IT department device
- `WS-098765` - Workstation #098765

**Without owner information, you'd never know:**
- Who to contact about `ASSET-00847291`
- Which department `CORP-LAP-001234` belongs to
- Whether `DEV-WS-001` is compliant with Finance policies

**With owner information, you get:**
- `"owner_name": "Sarah Johnson"` - Contact person
- `"owner_email": "sarah.j@company.com"` - How to reach them
- `"owner_department": "Marketing"` - Which policies apply

---

## 📋 Policy Management - Complete CRUD

### List All Policies
```http
GET /policies?page=1&page_size=50&policy_type=Device_Compliance&enabled=true
```

```json
{
  "policies": [
    {
      "id": "policy-uuid-1",
      "name": "MacBook Encryption Required",
      "description": "All MacBooks must have FileVault enabled",
      "policy_type": "Device Compliance",
      "severity": "High",
      "enabled": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-10T15:30:00Z",
      "created_by": "admin@company.com",
      "configuration": "{\"encryption_required\": true, \"os_types\": [\"macOS\"]}"
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### Create/Update Policies
```http
POST /policies
PUT /policies/{policy_id}
```

**Full policy management with configuration tracking.**

---

## 📊 History & Activity - Complete Context

### Configuration History
```http
GET /history/config?page=1&page_size=50&entity_type=user&entity_id={cid}
```

**See all changes with full context:**
```json
{
  "changes": [
    {
      "id": "change-uuid-1",
      "entity_type": "user",
      "entity_id": "123e4567-e89b-12d3-a456-426614174000",
      "change_type": "Updated",
      "field_name": "department",
      "old_value": "Marketing",
      "new_value": "Engineering",
      "changed_by": "hr@company.com",
      "changed_at": "2024-01-15T09:00:00Z",
      "description": "User transferred to Engineering department"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### Activity History
```http
GET /history/activity?page=1&page_size=50&user_cid={cid}&activity_type=Login
```

**Complete activity tracking:**
```json
{
  "activities": [
    {
      "id": "activity-uuid-1",
      "user_cid": "123e4567-e89b-12d3-a456-426614174000",
      "device_id": "device-uuid-1",
      "activity_type": "Login",
      "source_system": "Okta",
      "source_ip": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "description": "User logged in successfully",
      "timestamp": "2024-01-15T10:30:00Z",
      "risk_score": "Low",
      "activity_metadata": "{\"location\": \"San Francisco\", \"device_trusted\": true}"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

---

## 🔌 API Management - External System Integration

### List API Connections
```http
GET /apis?page=1&page_size=50&status=Connected&provider=Okta
```

**Manage all external integrations:**
```json
{
  "connections": [
    {
      "id": "connection-uuid-1",
      "name": "Production Okta",
      "provider": "Okta",
      "description": "Main identity provider",
      "base_url": "https://company.okta.com",
      "status": "Connected",
      "last_sync": "2024-01-15T10:00:00Z",
      "next_sync": "2024-01-15T11:00:00Z",
      "sync_enabled": true,
      "supports_users": true,
      "supports_devices": false,
      "supports_groups": true,
      "tags": [
        {"id": "tag-1", "tag": "Production"},
        {"id": "tag-2", "tag": "Critical"}
      ]
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

---

## 🎯 Frontend Development Patterns

### 1. **User Dashboard Component**
```javascript
// Single API call gets everything you need
const userData = await fetch(`/api/users/${userId}`);
// userData now contains: user info + devices + groups + accounts
```

### 2. **Device Management Table**
```javascript
// Single API call gets devices with owner info
const devicesData = await fetch(`/api/devices?page=1&page_size=50`);
// Each device includes owner_name, owner_email, owner_department
```

### 3. **Policy Management**
```javascript
// Full CRUD operations available
const policies = await fetch(`/api/policies`);
const newPolicy = await fetch(`/api/policies`, {method: 'POST', body: policyData});
```

### 4. **Activity Timeline**
```javascript
// Get activity with full context
const activities = await fetch(`/api/history/activity?user_cid=${userId}`);
// Each activity includes user info, device info, full context
```

---

## 🔍 Available Filters & Search

### User Endpoints
- Filter by: `department`, `status`, `role`, `location`
- Search by: `email`, `full_name`
- Sort by: `last_seen`, `created_at`, `email`

### Device Endpoints  
- Filter by: `compliant`, `status`, `owner_department`, `vlan`, `os_version`
- Search by: `name`, `ip_address`, `mac_address`, `owner_email`
- Sort by: `last_seen`, `name`, `owner_name`

### Policy Endpoints
- Filter by: `policy_type`, `severity`, `enabled`
- Search by: `name`, `description`
- Sort by: `created_at`, `updated_at`, `name`

### History Endpoints
- Filter by: `entity_type`, `change_type`, `activity_type`, `risk_score`
- Date range: `start_date`, `end_date`
- Sort by: `timestamp`, `changed_at`

---

## ✅ Summary: What Your Frontend Developer Can Do

**YES, we have comprehensive relational data!** Your frontend developer can:

1. ✅ **Copy & Paste User Management** - Get users with all devices, groups, accounts
2. ✅ **Copy & Paste Device Management** - Get devices with full owner information  
3. ✅ **Copy & Paste Policy Management** - Full CRUD with history tracking
4. ✅ **Copy & Paste History Views** - Activity and config history with full context
5. ✅ **Copy & Paste API Management** - Manage external system integrations

**All data is relational and returned in single API calls - no need for multiple requests to build complete views.**

The backend is ready for frontend development! 🚀
