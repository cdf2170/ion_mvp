using System;
using System.Text.Json.Serialization;

namespace IdentityAgent.Core.Models
{
    /// <summary>
    /// Configuration model for the Identity Agent
    /// </summary>
    public class AgentConfiguration
    {
        /// <summary>
        /// Backend API base URL
        /// </summary>
        public string ApiBaseUrl { get; set; } = "https://api.identityplatform.com";

        /// <summary>
        /// Agent authentication token
        /// </summary>
        public string AuthToken { get; set; } = string.Empty;

        /// <summary>
        /// Device identifier for correlation
        /// </summary>
        public string DeviceId { get; set; } = string.Empty;

        /// <summary>
        /// Organization identifier
        /// </summary>
        public string OrganizationId { get; set; } = string.Empty;

        /// <summary>
        /// How often to send heartbeat (seconds)
        /// </summary>
        public int HeartbeatIntervalSeconds { get; set; } = 300; // 5 minutes

        /// <summary>
        /// How often to collect system data (seconds)
        /// </summary>
        public int DataCollectionIntervalSeconds { get; set; } = 60; // 1 minute

        /// <summary>
        /// Maximum events to batch before sending
        /// </summary>
        public int MaxEventBatchSize { get; set; } = 100;

        /// <summary>
        /// Maximum time to wait before sending batch (seconds)
        /// </summary>
        public int MaxBatchWaitSeconds { get; set; } = 30;

        /// <summary>
        /// Enable real-time event monitoring
        /// </summary>
        public bool EnableRealTimeMonitoring { get; set; } = true;

        /// <summary>
        /// Enable process monitoring
        /// </summary>
        public bool EnableProcessMonitoring { get; set; } = true;

        /// <summary>
        /// Enable network monitoring
        /// </summary>
        public bool EnableNetworkMonitoring { get; set; } = true;

        /// <summary>
        /// Enable USB device monitoring
        /// </summary>
        public bool EnableUsbMonitoring { get; set; } = true;

        /// <summary>
        /// Enable registry monitoring
        /// </summary>
        public bool EnableRegistryMonitoring { get; set; } = false;

        /// <summary>
        /// Log level (Debug, Info, Warning, Error)
        /// </summary>
        public string LogLevel { get; set; } = "Info";

        /// <summary>
        /// Maximum log file size in MB
        /// </summary>
        public int MaxLogFileSizeMB { get; set; } = 10;

        /// <summary>
        /// Number of log files to retain
        /// </summary>
        public int LogFileRetentionCount { get; set; } = 5;

        /// <summary>
        /// API request timeout in seconds
        /// </summary>
        public int ApiTimeoutSeconds { get; set; } = 30;

        /// <summary>
        /// Maximum retry attempts for API calls
        /// </summary>
        public int MaxRetryAttempts { get; set; } = 3;

        /// <summary>
        /// Base retry delay in seconds
        /// </summary>
        public int RetryDelaySeconds { get; set; } = 5;

        /// <summary>
        /// Enable automatic configuration updates from backend
        /// </summary>
        public bool EnableRemoteConfiguration { get; set; } = true;

        /// <summary>
        /// Configuration update check interval (seconds)
        /// </summary>
        public int ConfigUpdateIntervalSeconds { get; set; } = 3600; // 1 hour

        /// <summary>
        /// Validate configuration settings
        /// </summary>
        public bool IsValid()
        {
            if (string.IsNullOrWhiteSpace(ApiBaseUrl))
                return false;

            if (string.IsNullOrWhiteSpace(AuthToken))
                return false;

            if (HeartbeatIntervalSeconds < 60 || HeartbeatIntervalSeconds > 3600)
                return false;

            if (DataCollectionIntervalSeconds < 30 || DataCollectionIntervalSeconds > 600)
                return false;

            if (MaxEventBatchSize < 1 || MaxEventBatchSize > 1000)
                return false;

            return true;
        }

        /// <summary>
        /// Get configuration hash for change detection
        /// </summary>
        public string GetConfigHash()
        {
            var configString = System.Text.Json.JsonSerializer.Serialize(this);
            using var sha256 = System.Security.Cryptography.SHA256.Create();
            var hashBytes = sha256.ComputeHash(System.Text.Encoding.UTF8.GetBytes(configString));
            return Convert.ToBase64String(hashBytes);
        }
    }
}
