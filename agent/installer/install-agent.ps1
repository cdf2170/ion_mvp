# Identity Agent Installation Script
# This script installs and configures the Identity Agent Windows service

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiBaseUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$AuthToken,
    
    [Parameter(Mandatory=$false)]
    [string]$OrganizationId = "",
    
    [Parameter(Mandatory=$false)]
    [string]$InstallPath = "C:\Program Files\IdentityAgent",
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "IdentityAgent",
    
    [Parameter(Mandatory=$false)]
    [switch]$Uninstall
)

# Ensure running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator. Exiting..."
    exit 1
}

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message"
}

function Test-ServiceExists {
    param([string]$ServiceName)
    return (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) -ne $null
}

function Uninstall-Agent {
    Write-Log "Starting Identity Agent uninstallation..."
    
    # Stop service if running
    if (Test-ServiceExists $ServiceName) {
        Write-Log "Stopping service: $ServiceName"
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        
        # Remove service
        Write-Log "Removing service: $ServiceName"
        sc.exe delete $ServiceName
    }
    
    # Remove installation directory
    if (Test-Path $InstallPath) {
        Write-Log "Removing installation directory: $InstallPath"
        Remove-Item -Path $InstallPath -Recurse -Force
    }
    
    # Remove Windows Event Log source
    if ([System.Diagnostics.EventLog]::SourceExists("IdentityAgent")) {
        Write-Log "Removing event log source"
        [System.Diagnostics.EventLog]::DeleteEventSource("IdentityAgent")
    }
    
    Write-Log "Identity Agent uninstalled successfully"
    exit 0
}

function Install-Agent {
    Write-Log "Starting Identity Agent installation..."
    
    # Validate parameters
    if ([string]::IsNullOrWhiteSpace($ApiBaseUrl)) {
        throw "ApiBaseUrl is required"
    }
    
    if ([string]::IsNullOrWhiteSpace($AuthToken)) {
        throw "AuthToken is required"
    }
    
    # Create installation directory
    Write-Log "Creating installation directory: $InstallPath"
    if (-not (Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    }
    
    # Copy agent files (assuming they're in the same directory as this script)
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $agentFiles = @(
        "IdentityAgent.Service.exe",
        "IdentityAgent.Core.dll",
        "appsettings.json",
        "Microsoft.Extensions.*.dll",
        "System.*.dll"
    )
    
    Write-Log "Copying agent files..."
    foreach ($pattern in $agentFiles) {
        $files = Get-ChildItem -Path $scriptDir -Filter $pattern -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            Copy-Item -Path $file.FullName -Destination $InstallPath -Force
            Write-Log "Copied: $($file.Name)"
        }
    }
    
    # Create configuration file
    $configPath = Join-Path $InstallPath "appsettings.json"
    $config = @{
        "AgentConfiguration" = @{
            "ApiBaseUrl" = $ApiBaseUrl
            "AuthToken" = $AuthToken
            "OrganizationId" = $OrganizationId
            "HeartbeatIntervalSeconds" = 300
            "DataCollectionIntervalSeconds" = 60
            "MaxEventBatchSize" = 100
            "MaxBatchWaitSeconds" = 30
            "EnableRealTimeMonitoring" = $true
            "EnableProcessMonitoring" = $true
            "EnableNetworkMonitoring" = $true
            "EnableUsbMonitoring" = $true
            "EnableRegistryMonitoring" = $false
            "LogLevel" = "Information"
            "MaxLogFileSizeMB" = 10
            "LogFileRetentionCount" = 5
            "ApiTimeoutSeconds" = 30
            "MaxRetryAttempts" = 3
            "RetryDelaySeconds" = 5
            "EnableRemoteConfiguration" = $true
            "ConfigUpdateIntervalSeconds" = 3600
        }
        "Logging" = @{
            "LogLevel" = @{
                "Default" = "Information"
                "Microsoft" = "Warning"
                "Microsoft.Hosting.Lifetime" = "Information"
            }
        }
    }
    
    Write-Log "Creating configuration file: $configPath"
    $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configPath -Encoding UTF8
    
    # Create Windows Event Log source
    if (-not [System.Diagnostics.EventLog]::SourceExists("IdentityAgent")) {
        Write-Log "Creating event log source"
        [System.Diagnostics.EventLog]::CreateEventSource("IdentityAgent", "Application")
    }
    
    # Install Windows service
    $servicePath = Join-Path $InstallPath "IdentityAgent.Service.exe"
    
    if (Test-ServiceExists $ServiceName) {
        Write-Log "Service already exists, stopping and removing..."
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        sc.exe delete $ServiceName
        Start-Sleep -Seconds 2
    }
    
    Write-Log "Installing Windows service: $ServiceName"
    $serviceArgs = @(
        "create",
        $ServiceName,
        "binPath=`"$servicePath`"",
        "DisplayName=`"Identity Agent Service`"",
        "Description=`"Provides real-time identity and device monitoring for the Identity Platform`"",
        "start=auto"
    )
    
    $result = & sc.exe @serviceArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create service: $result"
    }
    
    # Set service to restart on failure
    Write-Log "Configuring service recovery options..."
    sc.exe failure $ServiceName reset=86400 actions=restart/30000/restart/60000/restart/120000
    
    # Start the service
    Write-Log "Starting service: $ServiceName"
    Start-Service -Name $ServiceName
    
    # Wait a moment and check service status
    Start-Sleep -Seconds 5
    $service = Get-Service -Name $ServiceName
    if ($service.Status -eq "Running") {
        Write-Log "Service started successfully"
    } else {
        Write-Warning "Service may not have started correctly. Status: $($service.Status)"
        Write-Log "Check Windows Event Log for details"
    }
    
    Write-Log "Identity Agent installation completed successfully!"
    Write-Log "Service Name: $ServiceName"
    Write-Log "Installation Path: $InstallPath"
    Write-Log "Configuration File: $configPath"
    Write-Log ""
    Write-Log "To check service status: Get-Service -Name $ServiceName"
    Write-Log "To view logs: Get-EventLog -LogName Application -Source IdentityAgent -Newest 10"
}

# Main execution
try {
    if ($Uninstall) {
        Uninstall-Agent
    } else {
        Install-Agent
    }
} catch {
    Write-Error "Installation failed: $($_.Exception.Message)"
    Write-Error "Stack trace: $($_.ScriptStackTrace)"
    exit 1
}
