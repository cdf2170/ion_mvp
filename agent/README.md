# Identity Correlation Agent

A Windows service agent that provides real-time device monitoring and identity correlation for the MVP Identity Management Platform.

## Overview

The agent runs as a Windows service and provides:
- Real-time user login/logout monitoring
- Process and service monitoring
- Network connection tracking
- Hardware fingerprinting for device correlation
- Secure communication with the backend API
- Automatic correlation validation against API data

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
│   └── Retry Logic
└── Configuration Manager
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
