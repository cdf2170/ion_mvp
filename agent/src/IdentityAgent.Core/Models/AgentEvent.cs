using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace IdentityAgent.Core.Models
{
    /// <summary>
    /// Types of events the agent can report
    /// </summary>
    public enum AgentEventType
    {
        Login,
        Logout,
        ProcessStart,
        ProcessEnd,
        NetworkConnection,
        FileAccess,
        UsbConnect,
        UsbDisconnect,
        SoftwareInstall,
        SoftwareUninstall,
        RegistryChange,
        ServiceStart,
        ServiceStop,
        CertificateUse,
        PolicyViolation,
        Heartbeat
    }

    /// <summary>
    /// Event data collected by the agent
    /// </summary>
    public class AgentEvent
    {
        /// <summary>
        /// Unique event identifier
        /// </summary>
        public string Id { get; set; } = Guid.NewGuid().ToString();

        /// <summary>
        /// Device identifier
        /// </summary>
        public string DeviceId { get; set; } = string.Empty;

        /// <summary>
        /// Type of event
        /// </summary>
        public AgentEventType EventType { get; set; }

        /// <summary>
        /// When the event occurred
        /// </summary>
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;

        /// <summary>
        /// Event-specific data
        /// </summary>
        public Dictionary<string, object> EventData { get; set; } = new Dictionary<string, object>();

        /// <summary>
        /// User context (username, SID, etc.)
        /// </summary>
        public string UserContext { get; set; } = string.Empty;

        /// <summary>
        /// Risk score (0-100)
        /// </summary>
        public int RiskScore { get; set; } = 0;

        /// <summary>
        /// Correlation ID for grouping related events
        /// </summary>
        public string CorrelationId { get; set; } = string.Empty;

        /// <summary>
        /// Parent event ID for event chains
        /// </summary>
        public string ParentEventId { get; set; } = string.Empty;

        /// <summary>
        /// Additional metadata
        /// </summary>
        public Dictionary<string, string> Metadata { get; set; } = new Dictionary<string, string>();
    }

    /// <summary>
    /// Login event specific data
    /// </summary>
    public class LoginEventData
    {
        public string Username { get; set; } = string.Empty;
        public string Domain { get; set; } = string.Empty;
        public string SessionId { get; set; } = string.Empty;
        public string LoginType { get; set; } = string.Empty; // Interactive, Network, Service, etc.
        public string SourceIp { get; set; } = string.Empty;
        public bool IsSuccessful { get; set; }
        public string FailureReason { get; set; } = string.Empty;
    }

    /// <summary>
    /// Process event specific data
    /// </summary>
    public class ProcessEventData
    {
        public int ProcessId { get; set; }
        public string ProcessName { get; set; } = string.Empty;
        public string ExecutablePath { get; set; } = string.Empty;
        public string CommandLine { get; set; } = string.Empty;
        public int ParentProcessId { get; set; }
        public string ParentProcessName { get; set; } = string.Empty;
        public string Username { get; set; } = string.Empty;
        public DateTime StartTime { get; set; }
        public string FileHash { get; set; } = string.Empty;
        public bool IsSigned { get; set; }
        public string Publisher { get; set; } = string.Empty;
    }

    /// <summary>
    /// Network connection event data
    /// </summary>
    public class NetworkEventData
    {
        public string Protocol { get; set; } = string.Empty; // TCP, UDP
        public string LocalAddress { get; set; } = string.Empty;
        public int LocalPort { get; set; }
        public string RemoteAddress { get; set; } = string.Empty;
        public int RemotePort { get; set; }
        public string Direction { get; set; } = string.Empty; // Inbound, Outbound
        public int ProcessId { get; set; }
        public string ProcessName { get; set; } = string.Empty;
        public string Username { get; set; } = string.Empty;
        public long BytesSent { get; set; }
        public long BytesReceived { get; set; }
    }

    /// <summary>
    /// USB device event data
    /// </summary>
    public class UsbEventData
    {
        public string DeviceId { get; set; } = string.Empty;
        public string VendorId { get; set; } = string.Empty;
        public string ProductId { get; set; } = string.Empty;
        public string DeviceName { get; set; } = string.Empty;
        public string SerialNumber { get; set; } = string.Empty;
        public string DeviceClass { get; set; } = string.Empty;
        public bool IsRemovableStorage { get; set; }
        public long? StorageCapacity { get; set; }
    }

    /// <summary>
    /// Software installation event data
    /// </summary>
    public class SoftwareEventData
    {
        public string SoftwareName { get; set; } = string.Empty;
        public string Version { get; set; } = string.Empty;
        public string Publisher { get; set; } = string.Empty;
        public string InstallLocation { get; set; } = string.Empty;
        public DateTime InstallDate { get; set; }
        public string InstallSource { get; set; } = string.Empty;
        public string Username { get; set; } = string.Empty;
        public bool IsSystemInstall { get; set; }
    }

    /// <summary>
    /// Registry change event data
    /// </summary>
    public class RegistryEventData
    {
        public string KeyPath { get; set; } = string.Empty;
        public string ValueName { get; set; } = string.Empty;
        public string OldValue { get; set; } = string.Empty;
        public string NewValue { get; set; } = string.Empty;
        public string ValueType { get; set; } = string.Empty;
        public string Operation { get; set; } = string.Empty; // Create, Modify, Delete
        public int ProcessId { get; set; }
        public string ProcessName { get; set; } = string.Empty;
        public string Username { get; set; } = string.Empty;
    }
}
