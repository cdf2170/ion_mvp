# Group & Department Management API Guide

## Overview

The Groups API provides comprehensive management of departments, teams, and group memberships within your enterprise IAM system. This is perfect for the "Department" tab in your frontend, showing which department each device belongs to through user group memberships.

## Key Features

- **Department Management**: View all departments with member counts
- **Group Hierarchy**: Supports departments, teams, roles, access levels, and more
- **Source System Tracking**: Shows which system each group comes from (Workday, Okta, etc.)
- **User Membership Views**: See all groups a user belongs to
- **Advanced Filtering**: Filter by group type, source system, and search

## API Endpoints

### 1. Get All Groups/Departments
```http
GET /v1/groups
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `sort_by`: Sort column (group_name, group_type, member_count, etc.)
- `sort_direction`: asc/desc
- `group_type`: Filter by type (DEPARTMENT, TEAM, ROLE, ACCESS_LEVEL, etc.)
- `source_system`: Filter by source (Workday, Okta, Active Directory, etc.)
- `query`: Search in group name, description, and source system

**Example Response:**
```json
{
  "groups": [
    {
      "group_name": "Engineering",
      "group_type": "DEPARTMENT",
      "description": "Software development, DevOps, and technical infrastructure teams",
      "source_system": "Workday",
      "member_count": 45
    },
    {
      "group_name": "Frontend Engineering",
      "group_type": "TEAM",
      "description": "Web and mobile application development",
      "source_system": "Okta",
      "member_count": 12
    }
  ],
  "total": 87,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### 2. Get Group Members
```http
GET /v1/groups/{group_name}/members
```

**Query Parameters:**
- `group_type`: Optional filter if multiple groups have same name
- `page`: Page number for pagination
- `page_size`: Members per page

**Example:**
```http
GET /v1/groups/Engineering/members?group_type=DEPARTMENT
```

**Response:**
```json
{
  "group_name": "Engineering",
  "group_type": "DEPARTMENT",
  "description": "Software development, DevOps, and technical infrastructure teams",
  "members": [
    {
      "cid": "123e4567-e89b-12d3-a456-426614174000",
      "email": "sarah.chen@techcorp.com",
      "full_name": "Sarah Chen",
      "department": "Engineering",
      "role": "VP Engineering",
      "manager": null,
      "location": "San Francisco, CA",
      "status": "Active",
      "last_seen": "2025-09-22T10:30:00Z"
    }
  ],
  "total_members": 45
}
```

### 3. Get Department Summary
```http
GET /v1/groups/departments
```

**Perfect for frontend department views:**
```json
{
  "departments": [
    {
      "name": "Engineering",
      "description": "Software development, DevOps, and technical infrastructure teams",
      "member_count": 45
    },
    {
      "name": "Sales",
      "description": "Revenue generation, business development, and customer acquisition",
      "member_count": 32
    }
  ],
  "total_departments": 10
}
```

### 4. Get User's Group Memberships
```http
GET /v1/groups/user/{cid}/memberships
```

**Shows all groups a user belongs to:**
```json
{
  "user": {
    "cid": "123e4567-e89b-12d3-a456-426614174000",
    "email": "sarah.chen@techcorp.com",
    "full_name": "Sarah Chen",
    "department": "Engineering"
  },
  "memberships_by_type": {
    "DEPARTMENT": [
      {
        "group_name": "Engineering",
        "description": "Software development, DevOps, and technical infrastructure teams",
        "source_system": "Workday"
      }
    ],
    "ROLE": [
      {
        "group_name": "Vice Presidents",
        "description": "VP-level executives and department heads",
        "source_system": "Okta"
      }
    ],
    "ACCESS_LEVEL": [
      {
        "group_name": "Production Access",
        "description": "Production system access with SOX compliance",
        "source_system": "Active Directory"
      }
    ]
  },
  "total_memberships": 8
}
```

### 5. Group Summary Statistics
```http
GET /v1/groups/summary/by-type
```

**Dashboard statistics:**
```json
{
  "total_groups": 87,
  "total_memberships": 432,
  "by_type": {
    "DEPARTMENT": {
      "group_count": 10,
      "total_memberships": 250
    },
    "TEAM": {
      "group_count": 25,
      "total_memberships": 125
    },
    "ACCESS_LEVEL": {
      "group_count": 15,
      "total_memberships": 57
    }
  }
}
```

## Group Types Available

The system supports these group types:

### **DEPARTMENT** 
Core organizational departments from HR systems (Workday):
- Engineering, Sales, Marketing, Finance, etc.

### **TEAM**
Sub-teams within departments:
- Frontend Engineering, Backend Engineering, Enterprise Sales, etc.

### **ROLE**
Hierarchical roles and experience levels:
- C-Suite, Vice Presidents, Directors, Senior Level (L5+), etc.

### **ACCESS_LEVEL**
Security and system access groups:
- System Administrators, Production Access, Financial Systems Access, etc.

### **SECURITY_CLEARANCE**
Compliance and security clearances:
- SOX Compliance Required, PCI DSS Authorized, GDPR Data Handlers, etc.

### **LOCATION**
Geographic and work arrangement groups:
- San Francisco HQ, Remote - US, Hybrid Workers, etc.

### **PROJECT**
Temporary project and initiative teams:
- Project Phoenix, AI/ML Initiative, Cloud Migration Team, etc.

### **EMPLOYMENT_TYPE**
Employment classification:
- Full-Time Employees, Contractors, Interns, etc.

## Frontend Integration Examples

### Department Tab Implementation
```javascript
// Get all departments for dropdown/filter
const getDepartments = async () => {
  const response = await fetch('/v1/groups/departments');
  return response.json();
};

// Get devices and show department info
const getDevicesWithDepartments = async (search = '') => {
  const response = await fetch(`/v1/devices?query=${search}&page_size=50`);
  const data = await response.json();
  
  // Each device has owner_department which shows the department
  return data.devices.map(device => ({
    ...device,
    department: device.owner_department
  }));
};

// Get all members of a department
const getDepartmentMembers = async (departmentName) => {
  const response = await fetch(`/v1/groups/${departmentName}/members?group_type=DEPARTMENT`);
  return response.json();
};
```

### Search and Filtering
```javascript
// Search groups
const searchGroups = async (searchTerm, groupType = null) => {
  let url = `/v1/groups?query=${encodeURIComponent(searchTerm)}`;
  if (groupType) {
    url += `&group_type=${groupType}`;
  }
  const response = await fetch(url);
  return response.json();
};

// Filter by source system
const getGroupsBySource = async (sourceSystem) => {
  const response = await fetch(`/v1/groups?source_system=${sourceSystem}`);
  return response.json();
};
```

## Enhanced Policies Available

The system now includes 20+ realistic enterprise policies covering:

### **Password Policies**
- Corporate Password Policy (HIGH severity)
- Privileged Account Password Policy (CRITICAL severity)

### **Device Compliance Policies**
- Corporate Device Encryption (CRITICAL)
- Mobile Device Management (HIGH) 
- Endpoint Detection and Response (CRITICAL)
- Software Update Policy (HIGH)

### **Access Control Policies**
- Multi-Factor Authentication (CRITICAL)
- Remote Access Policy (HIGH)
- Privileged Access Management (CRITICAL)
- Guest Network Access (MEDIUM)

### **Data Classification Policies**
- Data Classification Standard (HIGH)
- Customer Data Protection GDPR/CCPA (CRITICAL)
- Financial Data Security SOX (CRITICAL)

### **Network Security Policies**
- Network Segmentation Policy (HIGH)
- Wireless Security Policy (HIGH)
- Firewall and IDS Policy (CRITICAL)
- DNS Security Policy (MEDIUM)

### **Backup and Retention Policies**
- Data Backup and Recovery (HIGH)
- Email Retention Policy (MEDIUM)
- Log Retention Policy (HIGH)

## Benefits for Your Demo

1. **Realistic Enterprise Structure**: Shows authentic department hierarchies
2. **Multiple Source Systems**: Demonstrates real-world integration scenarios
3. **Comprehensive Policies**: Covers all major security and compliance areas
4. **Logical Relationships**: Groups and policies connect logically to users and devices
5. **Scalable Design**: Supports enterprise-scale organizations

## Next Steps

1. Update your frontend "Groups" tab to "Department"
2. Use `/v1/groups/departments` for department listings
3. Show device departments via `owner_department` field
4. Use group search for finding specific departments/teams
5. Implement department-based filtering for devices and users

The seeded data creates logical relationships where users belong to appropriate departments, access levels, and roles that make sense for their job function, creating a realistic demo environment.
