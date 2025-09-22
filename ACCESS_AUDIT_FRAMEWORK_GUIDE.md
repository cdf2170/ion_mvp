# Access Management & Audit Framework Guide

## Overview

The Access Management API provides a comprehensive enterprise-grade access control and audit framework designed for compliance, security, and forensic analysis. This system tracks **who has access**, **why they have access**, **how long they have access**, and provides **cryptographically immutable proof** of all access changes.

## 🔑 Key Features

### **Complete Access Lifecycle Tracking**
- **Access Grants**: Current and historical access permissions
- **Justifications**: Business reasons and approvals for every access grant
- **Expiration Management**: Time-limited access with automatic tracking
- **Revocation Proof**: Immutable records of access removal

### **Cryptographic Audit Trail**
- **SHA-256 Hashing**: Every audit record is cryptographically hashed
- **HMAC Signatures**: Tamper-evident digital signatures
- **Immutable Records**: Once sealed, records cannot be modified
- **Chain of Custody**: Audit logs link to previous records for integrity

### **Compliance Ready**
- **SOX Compliance**: Segregation of duties and financial system access
- **PCI DSS**: Payment card industry data access controls
- **GDPR/CCPA**: Customer data access tracking and privacy
- **HIPAA**: Healthcare data access management

### **On-Demand User Audits**
- **Complete User Profile**: All access for any user instantly
- **Historical Timeline**: Full access history with timestamps
- **Direct Integration**: Connects seamlessly to user management

## 📊 API Endpoints

### 1. **Access Grants Management**

#### Get All Access Grants
```http
GET /v1/access
```

**Query Parameters:**
- `user_cid`: Filter by specific user
- `access_type`: Filter by type (System, Application, Data, Network, Physical, etc.)
- `status`: Filter by status (Active, Revoked, Expired, Suspended)
- `resource_name`: Filter by resource (partial match)
- `risk_level`: Filter by risk (Low, Medium, High, Critical)
- `expires_within_days`: Show access expiring within N days
- `granted_by`: Filter by who granted access
- `is_emergency`: Filter emergency access grants
- `needs_review`: Filter access needing review
- `compliance_tag`: Filter by compliance requirement (SOX, PCI, GDPR)
- `query`: Search across user, resource, and justification text

**Example Response:**
```json
{
  "access_grants": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "user_cid": "987fcdeb-51d3-47a8-9c6d-8b4f7a2e1d9c",
      "user_email": "sarah.chen@company.com",
      "user_name": "Sarah Chen",
      "user_department": "Engineering",
      
      "access_type": "DATABASE_ACCESS",
      "resource_name": "Production Database",
      "resource_identifier": "prod_db_cluster_001",
      "access_level": "Read Only",
      "permissions": {
        "read": true,
        "write": false,
        "admin": false
      },
      
      "granted_at": "2024-01-15T09:30:00Z",
      "expires_at": "2025-01-15T09:30:00Z",
      "granted_by": "IT Admin",
      "approved_by": "Engineering Manager",
      "source_system": "Active Directory",
      
      "reason": "JOB_REQUIREMENT",
      "justification": "Required for Senior Engineer role in Engineering department",
      "business_justification": "Essential access for production support and debugging",
      
      "status": "ACTIVE",
      "risk_level": "Critical",
      "compliance_tags": ["SOX", "PCI_DSS"],
      
      "last_reviewed_at": "2024-07-15T14:20:00Z",
      "last_reviewed_by": "Security Team",
      "next_review_due": "2024-12-15T09:30:00Z",
      
      "is_emergency_access": false,
      "days_until_expiry": 45,
      "days_since_granted": 320,
      "days_since_review": 68
    }
  ],
  "total": 1247,
  "page": 1,
  "page_size": 20,
  "total_pages": 63,
  "summary": {
    "total_access_grants": 1247,
    "active_access": 1089,
    "expired_access": 98,
    "revoked_access": 60,
    "emergency_access": 12,
    "expiring_within_30_days": 23
  }
}
```

### 2. **Audit Logs - Immutable Trail**

#### Get Audit Logs
```http
GET /v1/access/audit
```

**Query Parameters:**
- `user_cid`: Filter by specific user
- `action`: Filter by action (Access Granted, Access Revoked, Access Modified, etc.)
- `resource_name`: Filter by resource
- `performed_by`: Filter by who performed the action
- `access_type`: Filter by access type
- `date_from`: Filter from date (ISO format)
- `date_to`: Filter to date (ISO format)
- `is_emergency`: Filter emergency actions
- `compliance_tag`: Filter by compliance framework

**Example Response:**
```json
{
  "audit_logs": [
    {
      "id": "456e7890-e89b-12d3-a456-426614174001",
      "user_cid": "987fcdeb-51d3-47a8-9c6d-8b4f7a2e1d9c",
      "user_email": "sarah.chen@company.com",
      "user_name": "Sarah Chen",
      
      "action": "ACCESS_GRANTED",
      "timestamp": "2024-01-15T09:30:00Z",
      
      "resource_name": "Production Database",
      "resource_identifier": "prod_db_cluster_001",
      "access_type": "DATABASE_ACCESS",
      "access_level": "Read Only",
      
      "performed_by": "IT Admin",
      "reason": "JOB_REQUIREMENT",
      "justification": "Required for Senior Engineer role",
      
      "previous_state": null,
      "new_state": {
        "access_level": "Read Only",
        "permissions": {"read": true, "write": false, "admin": false},
        "status": "ACTIVE"
      },
      
      "source_system": "Active Directory",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      
      "is_emergency": false,
      "compliance_tags": ["SOX", "PCI_DSS"],
      "risk_assessment": "Critical",
      
      "record_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
      "signature": "hmac_sha256_signature_here",
      "is_sealed": true
    }
  ],
  "total": 3456,
  "page": 1,
  "page_size": 50,
  "total_pages": 70,
  "integrity_status": {
    "total_records": 3456,
    "sealed_records": 3456,
    "signed_records": 3456,
    "integrity_verified": true,
    "last_integrity_check": "2024-09-22T15:30:00Z"
  }
}
```

### 3. **User-Specific Access (On-Demand Audit)**

#### Get User's Complete Access Profile
```http
GET /v1/access/user/{cid}
```

**Perfect for user detail views and compliance investigations.**

**Query Parameters:**
- `include_revoked`: Include revoked access in results
- `include_expired`: Include expired access in results

**Example:**
```http
GET /v1/access/user/987fcdeb-51d3-47a8-9c6d-8b4f7a2e1d9c?include_revoked=true
```

#### Get User's Complete Audit History
```http
GET /v1/access/user/{cid}/audit
```

**Shows every access change for the user with full cryptographic verification.**

### 4. **Dashboard & Analytics**

#### Access Summary Statistics
```http
GET /v1/access/summary
```

```json
{
  "total_access_grants": 1247,
  "active_access_grants": 1089,
  "emergency_access_grants": 12,
  "expiring_within_30_days": 23,
  "recent_audit_events_24h": 156,
  "risk_distribution": {
    "Critical": 234,
    "High": 445,
    "Medium": 398,
    "Low": 170
  },
  "access_type_distribution": {
    "System Access": 456,
    "Application Access": 389,
    "Database Access": 234,
    "Network Access": 89,
    "Physical Access": 79
  }
}
```

#### Compliance Reports
```http
GET /v1/access/compliance/{framework}
```

**Generate compliance reports for specific frameworks:**
```http
GET /v1/access/compliance/SOX?include_details=true
GET /v1/access/compliance/PCI_DSS
GET /v1/access/compliance/GDPR
```

## 🛡️ Cryptographic Integrity

### **How It Works**

1. **Record Hashing**: Every audit log generates a SHA-256 hash of its core data
2. **Digital Signatures**: HMAC signatures provide tamper evidence
3. **Immutable Sealing**: Once sealed, records cannot be modified
4. **Chain Verification**: Records link to previous hashes for continuity

### **Hash Generation**
```python
# Each audit record includes:
{
  "record_hash": "sha256_of_record_data",
  "signature": "hmac_sha256_signature", 
  "is_sealed": true,
  "sealed_at": "2024-09-22T15:30:00Z",
  "sealed_by": "System"
}
```

### **Integrity Verification**
Every API response includes integrity status showing:
- Total records vs. sealed records
- Signature verification status
- Last integrity check timestamp

## 📋 Enterprise Access Types

### **System Access**
- Production servers and environments
- Cloud console access (AWS, Azure, GCP)
- Kubernetes clusters
- CI/CD pipelines

### **Application Access**
- Business applications (Salesforce, Slack, etc.)
- Admin panels and dashboards
- Development tools
- Customer support systems

### **Database Access**
- Production databases
- Data warehouses
- Analytics platforms
- Backup systems

### **Network Access**
- VPN access
- WiFi administration
- Firewall management
- Network monitoring

### **Physical Access**
- Server rooms
- Office buildings
- Secure facilities
- Executive areas

### **Data Access**
- Customer data systems
- Financial records
- HR information
- Intellectual property

## 🎯 Frontend Integration Examples

### **Access Tab Dashboard**
```javascript
// Get all access grants for dashboard
const getAccessDashboard = async () => {
  const response = await fetch('/v1/access?page_size=50');
  return response.json();
};

// Filter by risk level
const getCriticalAccess = async () => {
  const response = await fetch('/v1/access?risk_level=Critical');
  return response.json();
};

// Show expiring access
const getExpiringAccess = async () => {
  const response = await fetch('/v1/access?expires_within_days=30');
  return response.json();
};
```

### **User Detail Integration**
```javascript
// Get complete user access profile
const getUserAccessProfile = async (userCid) => {
  const response = await fetch(`/v1/access/user/${userCid}?include_revoked=true`);
  return response.json();
};

// Get user's audit history
const getUserAuditHistory = async (userCid) => {
  const response = await fetch(`/v1/access/user/${userCid}/audit?page_size=100`);
  return response.json();
};

// Connect to existing user tab
const enhanceUserView = async (userCid) => {
  const [userInfo, accessProfile, auditHistory] = await Promise.all([
    fetch(`/v1/users/${userCid}`).then(r => r.json()),
    getUserAccessProfile(userCid),
    getUserAuditHistory(userCid)
  ]);
  
  return {
    user: userInfo,
    access: accessProfile,
    audit: auditHistory
  };
};
```

### **Compliance Reporting**
```javascript
// Generate SOX compliance report
const generateComplianceReport = async (framework) => {
  const response = await fetch(`/v1/access/compliance/${framework}?include_details=true`);
  return response.json();
};

// Emergency access monitoring
const getEmergencyAccess = async () => {
  const response = await fetch('/v1/access?is_emergency=true');
  return response.json();
};
```

## 📈 Sample Data Created

The seeding system creates realistic enterprise access data:

### **Access Grants Per User**
- **Base Access**: Office building, Google Workspace, Slack (all users)
- **Department Access**: Role-appropriate systems (Engineers get GitHub, Finance gets QuickBooks)
- **Seniority Access**: Senior roles get production access
- **Management Access**: Managers get admin privileges
- **Executive Access**: C-suite gets executive floor and BI tools

### **Realistic Access Patterns**
- **85% Active** access grants
- **10% Expired** access grants  
- **5% Revoked** access grants
- **5% Emergency** access grants
- **30% Time-limited** access (with expiration dates)

### **Complete Audit Trail**
- **Access Granted** events for all grants
- **Access Reviewed** events (40% of grants)
- **Access Revoked** events with proof of removal
- **Cryptographic hashes** and signatures on all records

### **Compliance Integration**
- **SOX tags** on financial and production systems
- **PCI DSS tags** on payment-related access
- **GDPR tags** on customer data access
- **Risk levels** based on system criticality

## 🚀 Key Benefits for Your Demo

### **1. Enterprise Authenticity**
- Real-world access patterns and systems
- Authentic compliance requirements
- Professional justifications and workflows

### **2. Compliance Ready**
- SOX, PCI, GDPR, HIPAA compliance tracking
- Immutable audit trails for regulatory requirements
- Risk-based access classification

### **3. Security-First Design**
- Cryptographic integrity verification
- Tamper-evident audit records
- Emergency access tracking and alerts

### **4. Integration Ready**
- Direct user profile integration
- Dashboard-friendly summary APIs
- Real-time access monitoring

### **5. Forensic Capable**
- Complete timeline reconstruction
- Before/after state tracking
- IP address and session tracking
- Cross-system request tracing

## 🔗 Perfect for Access Tab

This framework provides everything needed for a comprehensive **Access** tab:

1. **Current Access View**: Who has what access right now
2. **Historical Timeline**: Complete access history for any user
3. **Compliance Dashboard**: Risk levels and compliance status
4. **Audit Trail**: Cryptographically verified access changes
5. **User Integration**: Direct links from user profiles to access details
6. **Proof of Removal**: Immutable evidence of access revocation

The system demonstrates enterprise-grade identity governance with the cryptographic integrity and audit capabilities that Fortune 500 companies require for compliance and security.

## Next Steps

1. **Deploy the enhanced models and APIs**
2. **Create the Access tab in your frontend**
3. **Integrate with existing User tab for on-demand audits**
4. **Demonstrate compliance reporting capabilities**
5. **Show cryptographic integrity verification**

This access management framework transforms your MVP into a comprehensive enterprise IAM solution with audit-grade security and compliance capabilities.
