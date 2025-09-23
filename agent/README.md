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

The agent will be distributed as an MSI package that:
1. Installs the service binary
2. Configures Windows service
3. Sets up initial configuration
4. Starts the service automatically

## Configuration

Configuration is managed through:
- Local config file (initial setup)
- Remote configuration from backend
- Windows registry settings
- Group Policy (enterprise deployments)

## Communication Protocol

The agent communicates with the backend using:
- HTTPS REST API
- JSON message format
- JWT authentication
- Automatic retry with exponential backoff
- Heartbeat mechanism for health monitoring

## Development

Built with:
- .NET 6.0
- Windows Service framework
- WMI for system monitoring
- Windows Event Log integration
- Secure HTTP client

## Deployment

Supports multiple deployment methods:
- Manual MSI installation
- Group Policy deployment
- SCCM/Intune deployment
- PowerShell DSC
- Automated deployment scripts
