# Identity Correlation Agent

A Windows service agent that provides real-time device monitoring and identity correlation for the MVP Identity Management Platform.

## Overview

The agent runs as a Windows service and provides:
- Real-time user login/logout monitoring
- Process and service monitoring
- Network connection tracking
- Hardware fingerprinting for device correlation
- Secure communication with the backend API
- **Automatic correlation validation against API data**
- **Discrepancy detection and reporting**

## The Hybrid Correlation Strategy

This agent implements a revolutionary approach to identity management:

1. **API Data Collection**: Your backend pulls data from Okta, Azure AD, CrowdStrike, etc.
2. **Agent Ground Truth**: The agent reports what's actually happening on the device
3. **Correlation Validation**: The system compares API data vs. agent reality
4. **Gap Detection**: Automatically identifies discrepancies and missing data
5. **Error Correction**: Uses agent data as the source of truth when conflicts arise

### Example Scenarios

**Shadow IT Detection**:
- API: User has 1 corporate laptop
- Agent: Reports 2 devices (corporate + personal laptop accessing resources)
- Result: Alert for unmanaged device

**Stale Identity Data**:
- API: User terminated 30 days ago
- Agent: User actively logged in right now
- Result: Critical alert for terminated user with active access

**Device Ownership Confusion**:
- API: Device belongs to John Smith
- Agent: Sarah Jones is actually logged in
- Result: Device ownership correction needed

## Architecture

```
Agent Service
├── Core Service Framework
├── Data Collection Modules
│   ├── User Session Monitor
│   ├── Process Monitor
│   ├── Network Monitor
│   └── Hardware Fingerprinter
├── Communication Layer
│   ├── API Client
│   ├── Authentication
│   ├── Retry Logic
│   └── Discrepancy Reporting
├── Configuration Manager
└── Correlation Validator
```

## Features

### Real-time Monitoring
- User login/logout events
- Process start/stop events
- Network connections
- USB device connections
- Service state changes
- Registry modifications

### Hardware Fingerprinting
- Motherboard serial number
- CPU identifier
- Hardware UUID
- MAC addresses
- System specifications

### Correlation Validation
- Validates API data against real device state
- Detects discrepancies between systems
- Reports shadow IT and unmanaged devices
- Identifies stale identity data

### Security
- Encrypted communication with backend
- Certificate-based authentication
- Secure credential storage
- Tamper detection

## Installation

### Quick Install (PowerShell)
```powershell
# Run as Administrator
.\install-agent.ps1 -ApiBaseUrl "https://your-api.com" -AuthToken "your-token" -OrganizationId "your-org"
```

### Manual Installation
The agent can be distributed as:
1. **MSI Package** (recommended for enterprise)
2. **PowerShell Script** (quick deployment)
3. **Group Policy** (domain environments)
4. **SCCM/Intune** (managed environments)

### Installation Steps
1. Installs the service binary to `C:\Program Files\IdentityAgent`
2. Configures Windows service with auto-start
3. Sets up initial configuration
4. Creates Windows Event Log source
5. Starts the service automatically
6. Registers with backend API

## Configuration

### Local Configuration (`appsettings.json`)
```json
{
  "AgentConfiguration": {
    "ApiBaseUrl": "https://your-backend-api.com",
    "AuthToken": "your-auth-token",
    "OrganizationId": "your-org-id",
    "HeartbeatIntervalSeconds": 300,
    "EnableRealTimeMonitoring": true,
    "EnableProcessMonitoring": true,
    "EnableNetworkMonitoring": true,
    "EnableUsbMonitoring": true,
    "LogLevel": "Information"
  }
}
```

### Remote Configuration
- Configuration updates pushed from backend
- Feature toggles controlled centrally
- Monitoring intervals adjustable per device
- Policy enforcement from central console

## API Endpoints

The agent communicates with these backend endpoints:

### Registration
```
POST /v1/agents/register
```
Registers the agent and correlates with existing device records.

### Heartbeat
```
POST /v1/agents/heartbeat
```
Regular status updates and configuration sync.

### Event Reporting
```
POST /v1/agents/events
```
Batch upload of collected events and system changes.

### Discrepancy Reporting
```
POST /v1/agents/discrepancies
```
Reports when agent data doesn't match API data.

### Configuration Updates
```
GET /v1/agents/{device_id}/config
```
Retrieves updated configuration from backend.

## Hardware Fingerprinting

The agent collects multiple hardware identifiers for robust device correlation:

- **Hardware UUID** (most reliable)
- **Motherboard Serial Number**
- **CPU Identifier**
- **MAC Addresses** (all network adapters)
- **System Manufacturer/Model**
- **Memory Configuration**

This creates a unique device fingerprint that survives:
- OS reinstalls
- Network changes
- Hardware upgrades (partial)
- Domain changes

## Event Types Monitored

- **User Sessions**: Login/logout events with context
- **Process Activity**: Application starts/stops with details
- **Network Connections**: Outbound connections and traffic
- **USB Devices**: Connect/disconnect events
- **Software Changes**: Install/uninstall events
- **Service Changes**: Windows service state changes
- **Registry Changes**: Critical registry modifications (optional)
- **Security Events**: Certificate usage, policy violations

## Security Features

- **Encrypted Communication**: All API calls use HTTPS with certificate validation
- **Token-Based Authentication**: Secure API token authentication
- **Tamper Detection**: Service integrity monitoring
- **Secure Storage**: Credentials encrypted at rest
- **Minimal Privileges**: Runs with least required permissions
- **Event Log Integration**: All activities logged to Windows Event Log

## Troubleshooting

### Check Service Status
```powershell
Get-Service -Name "IdentityAgent"
```

### View Recent Logs
```powershell
Get-EventLog -LogName Application -Source "IdentityAgent" -Newest 10
```

### Test API Connectivity
```powershell
# Check if agent can reach backend
Test-NetConnection -ComputerName "your-api-domain.com" -Port 443
```

### Manual Service Control
```powershell
# Stop service
Stop-Service -Name "IdentityAgent"

# Start service
Start-Service -Name "IdentityAgent"

# Restart service
Restart-Service -Name "IdentityAgent"
```

### Uninstall Agent
```powershell
.\install-agent.ps1 -Uninstall
```

## Development

### Prerequisites
- .NET 6.0 SDK
- Visual Studio 2022 or VS Code
- Windows 10/11 or Windows Server 2019+

### Build Instructions
```bash
cd agent/src
dotnet build
dotnet publish -c Release -r win-x64 --self-contained
```

### Testing
```bash
dotnet test
```

## Deployment Strategies

### Small Organizations (< 100 devices)
- PowerShell script deployment
- Manual installation on key devices
- Basic monitoring and alerting

### Medium Organizations (100-1000 devices)
- Group Policy deployment
- Centralized configuration management
- Automated monitoring dashboards

### Large Enterprises (1000+ devices)
- SCCM/Intune deployment
- Advanced policy management
- Integration with existing ITSM tools
- Custom reporting and analytics

## Performance Impact

The agent is designed for minimal system impact:
- **CPU Usage**: < 1% average
- **Memory Usage**: < 50MB typical
- **Network Usage**: < 1MB/day per device
- **Disk Usage**: < 100MB installation + logs
- **Boot Impact**: < 2 seconds additional startup time

## Compliance and Privacy

- **Data Minimization**: Only collects necessary identity/security data
- **Retention Policies**: Configurable data retention periods
- **Audit Trails**: Complete audit log of all agent activities
- **Privacy Controls**: User notification options available
- **Compliance Ready**: Supports SOX, PCI, GDPR, HIPAA requirements
