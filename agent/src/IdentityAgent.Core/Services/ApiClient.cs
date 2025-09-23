using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using IdentityAgent.Core.Models;

namespace IdentityAgent.Core.Services
{
    /// <summary>
    /// Client for communicating with the Identity Platform backend API
    /// </summary>
    public class ApiClient : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<ApiClient> _logger;
        private readonly AgentConfiguration _config;
        private readonly JsonSerializerOptions _jsonOptions;

        public ApiClient(HttpClient httpClient, ILogger<ApiClient> logger, AgentConfiguration config)
        {
            _httpClient = httpClient;
            _logger = logger;
            _config = config;

            // Configure HTTP client
            _httpClient.BaseAddress = new Uri(_config.ApiBaseUrl);
            _httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {_config.AuthToken}");
            _httpClient.DefaultRequestHeaders.Add("User-Agent", "IdentityAgent/1.0");
            _httpClient.Timeout = TimeSpan.FromSeconds(_config.ApiTimeoutSeconds);

            // Configure JSON serialization
            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                WriteIndented = false
            };
        }

        /// <summary>
        /// Register the agent with the backend
        /// </summary>
        public async Task<bool> RegisterAgentAsync(DeviceInfo deviceInfo)
        {
            try
            {
                var registrationData = new
                {
                    deviceInfo.Name,
                    deviceInfo.HardwareUuid,
                    deviceInfo.MotherboardSerial,
                    deviceInfo.CpuId,
                    deviceInfo.MacAddress,
                    deviceInfo.IpAddress,
                    deviceInfo.OsVersion,
                    deviceInfo.Manufacturer,
                    deviceInfo.Model,
                    AgentVersion = "1.0.0",
                    OrganizationId = _config.OrganizationId,
                    Fingerprint = deviceInfo.GenerateFingerprint()
                };

                var response = await PostAsync("/v1/agents/register", registrationData);
                
                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();
                    var result = JsonSerializer.Deserialize<Dictionary<string, object>>(responseContent, _jsonOptions);
                    
                    if (result?.ContainsKey("deviceId") == true)
                    {
                        _config.DeviceId = result["deviceId"].ToString();
                        _logger.LogInformation("Agent registered successfully with device ID: {DeviceId}", _config.DeviceId);
                        return true;
                    }
                }

                _logger.LogWarning("Agent registration failed with status: {StatusCode}", response.StatusCode);
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error registering agent");
                return false;
            }
        }

        /// <summary>
        /// Send heartbeat to backend
        /// </summary>
        public async Task<bool> SendHeartbeatAsync(DeviceInfo deviceInfo)
        {
            try
            {
                var heartbeatData = new
                {
                    DeviceId = _config.DeviceId,
                    Timestamp = DateTime.UtcNow,
                    Status = "Running",
                    AgentVersion = "1.0.0",
                    deviceInfo.IpAddress,
                    deviceInfo.LastBootTime,
                    SystemUptime = DateTime.UtcNow - deviceInfo.LastBootTime,
                    ConfigHash = _config.GetConfigHash()
                };

                var response = await PostAsync("/v1/agents/heartbeat", heartbeatData);
                
                if (response.IsSuccessStatusCode)
                {
                    _logger.LogDebug("Heartbeat sent successfully");
                    return true;
                }

                _logger.LogWarning("Heartbeat failed with status: {StatusCode}", response.StatusCode);
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error sending heartbeat");
                return false;
            }
        }

        /// <summary>
        /// Send batch of events to backend
        /// </summary>
        public async Task<bool> SendEventsAsync(List<AgentEvent> events)
        {
            if (events == null || events.Count == 0)
                return true;

            try
            {
                var eventBatch = new
                {
                    DeviceId = _config.DeviceId,
                    Events = events,
                    BatchTimestamp = DateTime.UtcNow
                };

                var response = await PostAsync("/v1/agents/events", eventBatch);
                
                if (response.IsSuccessStatusCode)
                {
                    _logger.LogDebug("Sent {EventCount} events successfully", events.Count);
                    return true;
                }

                _logger.LogWarning("Event batch failed with status: {StatusCode}", response.StatusCode);
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error sending events");
                return false;
            }
        }

        /// <summary>
        /// Get configuration updates from backend
        /// </summary>
        public async Task<AgentConfiguration> GetConfigurationAsync()
        {
            try
            {
                var response = await GetAsync($"/v1/agents/{_config.DeviceId}/config");
                
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var config = JsonSerializer.Deserialize<AgentConfiguration>(content, _jsonOptions);
                    
                    if (config != null && config.IsValid())
                    {
                        _logger.LogInformation("Retrieved updated configuration");
                        return config;
                    }
                }

                _logger.LogWarning("Failed to get configuration with status: {StatusCode}", response.StatusCode);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting configuration");
            }

            return _config; // Return current config if update fails
        }

        /// <summary>
        /// Report correlation discrepancy to backend
        /// </summary>
        public async Task<bool> ReportDiscrepancyAsync(string discrepancyType, object discrepancyData)
        {
            try
            {
                var report = new
                {
                    DeviceId = _config.DeviceId,
                    DiscrepancyType = discrepancyType,
                    DiscrepancyData = discrepancyData,
                    Timestamp = DateTime.UtcNow,
                    AgentVersion = "1.0.0"
                };

                var response = await PostAsync("/v1/agents/discrepancies", report);
                
                if (response.IsSuccessStatusCode)
                {
                    _logger.LogInformation("Reported discrepancy: {Type}", discrepancyType);
                    return true;
                }

                _logger.LogWarning("Discrepancy report failed with status: {StatusCode}", response.StatusCode);
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error reporting discrepancy");
                return false;
            }
        }

        private async Task<HttpResponseMessage> GetAsync(string endpoint)
        {
            return await ExecuteWithRetryAsync(() => _httpClient.GetAsync(endpoint));
        }

        private async Task<HttpResponseMessage> PostAsync(string endpoint, object data)
        {
            var json = JsonSerializer.Serialize(data, _jsonOptions);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            return await ExecuteWithRetryAsync(() => _httpClient.PostAsync(endpoint, content));
        }

        private async Task<HttpResponseMessage> ExecuteWithRetryAsync(Func<Task<HttpResponseMessage>> operation)
        {
            var attempt = 0;
            var delay = TimeSpan.FromSeconds(_config.RetryDelaySeconds);

            while (attempt < _config.MaxRetryAttempts)
            {
                try
                {
                    var response = await operation();
                    
                    // Don't retry on client errors (4xx), only server errors (5xx) and network issues
                    if (response.IsSuccessStatusCode || ((int)response.StatusCode >= 400 && (int)response.StatusCode < 500))
                    {
                        return response;
                    }

                    _logger.LogWarning("API call failed with status {StatusCode}, attempt {Attempt}/{MaxAttempts}", 
                        response.StatusCode, attempt + 1, _config.MaxRetryAttempts);
                }
                catch (HttpRequestException ex)
                {
                    _logger.LogWarning(ex, "Network error on attempt {Attempt}/{MaxAttempts}", 
                        attempt + 1, _config.MaxRetryAttempts);
                }
                catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
                {
                    _logger.LogWarning("Request timeout on attempt {Attempt}/{MaxAttempts}", 
                        attempt + 1, _config.MaxRetryAttempts);
                }

                attempt++;
                
                if (attempt < _config.MaxRetryAttempts)
                {
                    await Task.Delay(delay);
                    delay = TimeSpan.FromSeconds(delay.TotalSeconds * 2); // Exponential backoff
                }
            }

            throw new HttpRequestException($"API call failed after {_config.MaxRetryAttempts} attempts");
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }
}
