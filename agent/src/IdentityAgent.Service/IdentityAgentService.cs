using System;
using System.Collections.Generic;
using System.ServiceProcess;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using IdentityAgent.Core.Models;
using IdentityAgent.Core.Services;

namespace IdentityAgent.Service
{
    /// <summary>
    /// Main Windows service for the Identity Agent
    /// </summary>
    public class IdentityAgentService : BackgroundService
    {
        private readonly ILogger<IdentityAgentService> _logger;
        private readonly IServiceProvider _serviceProvider;
        private readonly AgentConfiguration _config;
        
        private ApiClient _apiClient;
        private HardwareFingerprinter _fingerprinter;
        private DeviceInfo _deviceInfo;
        private readonly List<AgentEvent> _eventBuffer = new List<AgentEvent>();
        private readonly object _eventBufferLock = new object();
        
        private Timer _heartbeatTimer;
        private Timer _dataCollectionTimer;
        private Timer _configUpdateTimer;
        private Timer _eventFlushTimer;

        public IdentityAgentService(
            ILogger<IdentityAgentService> logger,
            IServiceProvider serviceProvider,
            AgentConfiguration config)
        {
            _logger = logger;
            _serviceProvider = serviceProvider;
            _config = config;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation("Identity Agent Service starting...");

            try
            {
                // Initialize services
                await InitializeServicesAsync();

                // Register with backend
                await RegisterAgentAsync();

                // Start monitoring timers
                StartTimers();

                _logger.LogInformation("Identity Agent Service started successfully");

                // Keep the service running
                while (!stoppingToken.IsCancellationRequested)
                {
                    await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
                }
            }
            catch (Exception ex)
            {
                _logger.LogCritical(ex, "Critical error in Identity Agent Service");
                throw;
            }
        }

        private async Task InitializeServicesAsync()
        {
            _logger.LogInformation("Initializing services...");

            // Create API client
            var httpClient = _serviceProvider.GetRequiredService<HttpClient>();
            _apiClient = new ApiClient(httpClient, _serviceProvider.GetRequiredService<ILogger<ApiClient>>(), _config);

            // Create hardware fingerprinter
            _fingerprinter = _serviceProvider.GetRequiredService<HardwareFingerprinter>();

            // Collect initial device information
            _deviceInfo = await _fingerprinter.CollectDeviceInfoAsync();

            _logger.LogInformation("Services initialized successfully");
        }

        private async Task RegisterAgentAsync()
        {
            _logger.LogInformation("Registering agent with backend...");

            var maxRetries = 5;
            var retryDelay = TimeSpan.FromSeconds(30);

            for (int attempt = 1; attempt <= maxRetries; attempt++)
            {
                try
                {
                    var success = await _apiClient.RegisterAgentAsync(_deviceInfo);
                    if (success)
                    {
                        _logger.LogInformation("Agent registered successfully");
                        return;
                    }

                    _logger.LogWarning("Registration attempt {Attempt} failed", attempt);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Registration attempt {Attempt} failed with error", attempt);
                }

                if (attempt < maxRetries)
                {
                    _logger.LogInformation("Retrying registration in {Delay} seconds...", retryDelay.TotalSeconds);
                    await Task.Delay(retryDelay);
                    retryDelay = TimeSpan.FromSeconds(retryDelay.TotalSeconds * 2); // Exponential backoff
                }
            }

            throw new InvalidOperationException("Failed to register agent after multiple attempts");
        }

        private void StartTimers()
        {
            _logger.LogInformation("Starting monitoring timers...");

            // Heartbeat timer
            _heartbeatTimer = new Timer(
                async _ => await SendHeartbeatAsync(),
                null,
                TimeSpan.Zero,
                TimeSpan.FromSeconds(_config.HeartbeatIntervalSeconds));

            // Data collection timer
            _dataCollectionTimer = new Timer(
                async _ => await CollectDataAsync(),
                null,
                TimeSpan.FromSeconds(10), // Start after 10 seconds
                TimeSpan.FromSeconds(_config.DataCollectionIntervalSeconds));

            // Configuration update timer
            if (_config.EnableRemoteConfiguration)
            {
                _configUpdateTimer = new Timer(
                    async _ => await UpdateConfigurationAsync(),
                    null,
                    TimeSpan.FromMinutes(5), // First check after 5 minutes
                    TimeSpan.FromSeconds(_config.ConfigUpdateIntervalSeconds));
            }

            // Event flush timer
            _eventFlushTimer = new Timer(
                async _ => await FlushEventsAsync(),
                null,
                TimeSpan.FromSeconds(_config.MaxBatchWaitSeconds),
                TimeSpan.FromSeconds(_config.MaxBatchWaitSeconds));

            _logger.LogInformation("Monitoring timers started");
        }

        private async Task SendHeartbeatAsync()
        {
            try
            {
                // Update device info before sending heartbeat
                _deviceInfo = await _fingerprinter.CollectDeviceInfoAsync();
                
                await _apiClient.SendHeartbeatAsync(_deviceInfo);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error sending heartbeat");
            }
        }

        private async Task CollectDataAsync()
        {
            try
            {
                if (!_config.EnableRealTimeMonitoring)
                    return;

                // Collect current system state
                var currentDeviceInfo = await _fingerprinter.CollectDeviceInfoAsync();

                // Check for changes and generate events
                await DetectChangesAsync(currentDeviceInfo);

                // Update stored device info
                _deviceInfo = currentDeviceInfo;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error collecting data");
            }
        }

        private async Task DetectChangesAsync(DeviceInfo currentInfo)
        {
            var events = new List<AgentEvent>();

            // Detect IP address changes
            if (_deviceInfo.IpAddress != currentInfo.IpAddress)
            {
                events.Add(new AgentEvent
                {
                    DeviceId = _config.DeviceId,
                    EventType = AgentEventType.NetworkConnection,
                    EventData = new Dictionary<string, object>
                    {
                        ["changeType"] = "IpAddressChange",
                        ["oldIpAddress"] = _deviceInfo.IpAddress,
                        ["newIpAddress"] = currentInfo.IpAddress
                    },
                    RiskScore = 10
                });
            }

            // Detect boot time changes (system restart)
            if (_deviceInfo.LastBootTime != currentInfo.LastBootTime)
            {
                events.Add(new AgentEvent
                {
                    DeviceId = _config.DeviceId,
                    EventType = AgentEventType.Login,
                    EventData = new Dictionary<string, object>
                    {
                        ["changeType"] = "SystemRestart",
                        ["lastBootTime"] = currentInfo.LastBootTime,
                        ["previousBootTime"] = _deviceInfo.LastBootTime
                    },
                    RiskScore = 5
                });
            }

            // Add events to buffer
            if (events.Count > 0)
            {
                lock (_eventBufferLock)
                {
                    _eventBuffer.AddRange(events);
                }

                _logger.LogDebug("Detected {EventCount} system changes", events.Count);
            }
        }

        private async Task FlushEventsAsync()
        {
            List<AgentEvent> eventsToSend;

            lock (_eventBufferLock)
            {
                if (_eventBuffer.Count == 0)
                    return;

                eventsToSend = new List<AgentEvent>(_eventBuffer);
                _eventBuffer.Clear();
            }

            try
            {
                await _apiClient.SendEventsAsync(eventsToSend);
                _logger.LogDebug("Flushed {EventCount} events", eventsToSend.Count);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error flushing events");
                
                // Put events back in buffer for retry
                lock (_eventBufferLock)
                {
                    _eventBuffer.InsertRange(0, eventsToSend);
                }
            }
        }

        private async Task UpdateConfigurationAsync()
        {
            try
            {
                var newConfig = await _apiClient.GetConfigurationAsync();
                
                if (newConfig.GetConfigHash() != _config.GetConfigHash())
                {
                    _logger.LogInformation("Configuration updated from backend");
                    
                    // Apply new configuration
                    ApplyConfiguration(newConfig);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error updating configuration");
            }
        }

        private void ApplyConfiguration(AgentConfiguration newConfig)
        {
            // Update timer intervals if they changed
            if (newConfig.HeartbeatIntervalSeconds != _config.HeartbeatIntervalSeconds)
            {
                _heartbeatTimer?.Change(TimeSpan.Zero, TimeSpan.FromSeconds(newConfig.HeartbeatIntervalSeconds));
            }

            if (newConfig.DataCollectionIntervalSeconds != _config.DataCollectionIntervalSeconds)
            {
                _dataCollectionTimer?.Change(TimeSpan.Zero, TimeSpan.FromSeconds(newConfig.DataCollectionIntervalSeconds));
            }

            // Copy new configuration values
            _config.HeartbeatIntervalSeconds = newConfig.HeartbeatIntervalSeconds;
            _config.DataCollectionIntervalSeconds = newConfig.DataCollectionIntervalSeconds;
            _config.EnableRealTimeMonitoring = newConfig.EnableRealTimeMonitoring;
            _config.EnableProcessMonitoring = newConfig.EnableProcessMonitoring;
            _config.EnableNetworkMonitoring = newConfig.EnableNetworkMonitoring;
            _config.EnableUsbMonitoring = newConfig.EnableUsbMonitoring;
            _config.EnableRegistryMonitoring = newConfig.EnableRegistryMonitoring;

            _logger.LogInformation("Applied new configuration");
        }

        public override async Task StopAsync(CancellationToken cancellationToken)
        {
            _logger.LogInformation("Identity Agent Service stopping...");

            // Stop timers
            _heartbeatTimer?.Dispose();
            _dataCollectionTimer?.Dispose();
            _configUpdateTimer?.Dispose();
            _eventFlushTimer?.Dispose();

            // Flush remaining events
            await FlushEventsAsync();

            // Dispose API client
            _apiClient?.Dispose();

            _logger.LogInformation("Identity Agent Service stopped");

            await base.StopAsync(cancellationToken);
        }
    }
}
