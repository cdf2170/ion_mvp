using System;
using System.Collections.Generic;
using System.Linq;
using System.Management;
using System.Net.NetworkInformation;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using IdentityAgent.Core.Models;

namespace IdentityAgent.Core.Services
{
    /// <summary>
    /// Service for collecting hardware information and generating device fingerprints
    /// </summary>
    public class HardwareFingerprinter
    {
        private readonly ILogger<HardwareFingerprinter> _logger;

        public HardwareFingerprinter(ILogger<HardwareFingerprinter> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Collect comprehensive device information
        /// </summary>
        public async Task<DeviceInfo> CollectDeviceInfoAsync()
        {
            var deviceInfo = new DeviceInfo();

            try
            {
                // Collect basic system information
                await CollectBasicSystemInfo(deviceInfo);

                // Collect hardware identifiers
                await CollectHardwareIdentifiers(deviceInfo);

                // Collect network information
                await CollectNetworkInfo(deviceInfo);

                // Collect security information
                await CollectSecurityInfo(deviceInfo);

                // Collect OS and update information
                await CollectOSInfo(deviceInfo);

                _logger.LogInformation("Successfully collected device information");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error collecting device information");
            }

            return deviceInfo;
        }

        private async Task CollectBasicSystemInfo(DeviceInfo deviceInfo)
        {
            try
            {
                deviceInfo.Name = Environment.MachineName;
                deviceInfo.Domain = Environment.UserDomainName;
                deviceInfo.IsDomainJoined = !string.Equals(deviceInfo.Domain, deviceInfo.Name, StringComparison.OrdinalIgnoreCase);

                // Get system information from WMI
                using var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_ComputerSystem");
                foreach (ManagementObject obj in searcher.Get())
                {
                    deviceInfo.Manufacturer = obj["Manufacturer"]?.ToString() ?? "";
                    deviceInfo.Model = obj["Model"]?.ToString() ?? "";
                    deviceInfo.TotalMemoryGB = Convert.ToInt64(obj["TotalPhysicalMemory"] ?? 0) / (1024 * 1024 * 1024);
                    
                    if (!deviceInfo.IsDomainJoined)
                    {
                        deviceInfo.Workgroup = obj["Workgroup"]?.ToString() ?? "";
                    }
                }

                // Get CPU information
                using var cpuSearcher = new ManagementObjectSearcher("SELECT * FROM Win32_Processor");
                foreach (ManagementObject obj in cpuSearcher.Get())
                {
                    deviceInfo.CpuName = obj["Name"]?.ToString() ?? "";
                    deviceInfo.CpuCores = Convert.ToInt32(obj["NumberOfCores"] ?? 0);
                    break; // Just get the first CPU
                }

                // Get last boot time
                using var osSearcher = new ManagementObjectSearcher("SELECT * FROM Win32_OperatingSystem");
                foreach (ManagementObject obj in osSearcher.Get())
                {
                    var lastBootUpTime = obj["LastBootUpTime"]?.ToString();
                    if (!string.IsNullOrEmpty(lastBootUpTime))
                    {
                        deviceInfo.LastBootTime = ManagementDateTimeConverter.ToDateTime(lastBootUpTime);
                    }
                    break;
                }

                deviceInfo.TimeZone = TimeZoneInfo.Local.Id;
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Error collecting basic system information");
            }
        }

        private async Task CollectHardwareIdentifiers(DeviceInfo deviceInfo)
        {
            try
            {
                // Get hardware UUID from computer system product
                using var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_ComputerSystemProduct");
                foreach (ManagementObject obj in searcher.Get())
                {
                    deviceInfo.HardwareUuid = obj["UUID"]?.ToString() ?? "";
                    break;
                }

                // Get motherboard serial number
                using var mbSearcher = new ManagementObjectSearcher("SELECT * FROM Win32_BaseBoard");
                foreach (ManagementObject obj in mbSearcher.Get())
                {
                    deviceInfo.MotherboardSerial = obj["SerialNumber"]?.ToString() ?? "";
                    break;
                }

                // Get CPU ID
                using var cpuSearcher = new ManagementObjectSearcher("SELECT * FROM Win32_Processor");
                foreach (ManagementObject obj in cpuSearcher.Get())
                {
                    deviceInfo.CpuId = obj["ProcessorId"]?.ToString() ?? "";
                    break;
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Error collecting hardware identifiers");
            }
        }

        private async Task CollectNetworkInfo(DeviceInfo deviceInfo)
        {
            try
            {
                var networkInterfaces = NetworkInterface.GetAllNetworkInterfaces()
                    .Where(ni => ni.OperationalStatus == OperationalStatus.Up && 
                                ni.NetworkInterfaceType != NetworkInterfaceType.Loopback)
                    .ToList();

                foreach (var ni in networkInterfaces)
                {
                    var macAddress = ni.GetPhysicalAddress().ToString();
                    if (!string.IsNullOrEmpty(macAddress) && macAddress != "000000000000")
                    {
                        // Format MAC address with colons
                        var formattedMac = string.Join(":", 
                            Enumerable.Range(0, macAddress.Length / 2)
                                     .Select(i => macAddress.Substring(i * 2, 2)));
                        
                        deviceInfo.AllMacAddresses.Add(formattedMac);

                        // Use the first valid MAC as primary
                        if (string.IsNullOrEmpty(deviceInfo.MacAddress))
                        {
                            deviceInfo.MacAddress = formattedMac;
                        }
                    }

                    // Get IP address
                    var ipProperties = ni.GetIPProperties();
                    var ipAddress = ipProperties.UnicastAddresses
                        .FirstOrDefault(ip => ip.Address.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork)
                        ?.Address.ToString();

                    if (!string.IsNullOrEmpty(ipAddress) && string.IsNullOrEmpty(deviceInfo.IpAddress))
                    {
                        deviceInfo.IpAddress = ipAddress;
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Error collecting network information");
            }
        }

        private async Task CollectSecurityInfo(DeviceInfo deviceInfo)
        {
            try
            {
                // Check Windows Defender status
                try
                {
                    using var searcher = new ManagementObjectSearcher(@"root\Microsoft\Windows\Defender", 
                        "SELECT * FROM MSFT_MpComputerStatus");
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        deviceInfo.DefenderEnabled = Convert.ToBoolean(obj["AntivirusEnabled"] ?? false);
                        break;
                    }
                }
                catch
                {
                    // Defender WMI might not be available on all systems
                }

                // Check for antivirus products
                try
                {
                    using var searcher = new ManagementObjectSearcher(@"root\SecurityCenter2", 
                        "SELECT * FROM AntiVirusProduct");
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        var displayName = obj["displayName"]?.ToString();
                        if (!string.IsNullOrEmpty(displayName))
                        {
                            deviceInfo.AntivirusProducts.Add(displayName);
                        }
                    }
                }
                catch
                {
                    // SecurityCenter2 might not be available
                }

                // Check TPM status
                try
                {
                    using var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_Tpm");
                    deviceInfo.TpmEnabled = searcher.Get().Count > 0;
                }
                catch
                {
                    // TPM WMI might not be available
                }

                // Check BitLocker status (simplified check)
                try
                {
                    using var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_EncryptableVolume");
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        var protectionStatus = Convert.ToInt32(obj["ProtectionStatus"] ?? 0);
                        if (protectionStatus == 1) // Protected
                        {
                            deviceInfo.BitLockerEnabled = true;
                            break;
                        }
                    }
                }
                catch
                {
                    // BitLocker WMI might not be available
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Error collecting security information");
            }
        }

        private async Task CollectOSInfo(DeviceInfo deviceInfo)
        {
            try
            {
                using var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_OperatingSystem");
                foreach (ManagementObject obj in searcher.Get())
                {
                    deviceInfo.OsVersion = obj["Caption"]?.ToString() ?? "";
                    deviceInfo.OsBuild = obj["BuildNumber"]?.ToString() ?? "";
                    
                    var lastUpdateSearch = obj["LastBootUpTime"]?.ToString();
                    // Note: Getting actual Windows Update info requires more complex WMI queries
                    // This is a simplified implementation
                    break;
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Error collecting OS information");
            }
        }
    }
}
