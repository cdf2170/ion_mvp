using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace IdentityAgent.Core.Models
{
    /// <summary>
    /// Device information for hardware fingerprinting and correlation
    /// </summary>
    public class DeviceInfo
    {
        /// <summary>
        /// Device name (computer name)
        /// </summary>
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// Hardware UUID from motherboard
        /// </summary>
        public string HardwareUuid { get; set; } = string.Empty;

        /// <summary>
        /// Motherboard serial number
        /// </summary>
        public string MotherboardSerial { get; set; } = string.Empty;

        /// <summary>
        /// CPU identifier
        /// </summary>
        public string CpuId { get; set; } = string.Empty;

        /// <summary>
        /// Primary MAC address
        /// </summary>
        public string MacAddress { get; set; } = string.Empty;

        /// <summary>
        /// All network adapter MAC addresses
        /// </summary>
        public List<string> AllMacAddresses { get; set; } = new List<string>();

        /// <summary>
        /// Current IP address
        /// </summary>
        public string IpAddress { get; set; } = string.Empty;

        /// <summary>
        /// Operating system version
        /// </summary>
        public string OsVersion { get; set; } = string.Empty;

        /// <summary>
        /// Operating system build number
        /// </summary>
        public string OsBuild { get; set; } = string.Empty;

        /// <summary>
        /// System manufacturer
        /// </summary>
        public string Manufacturer { get; set; } = string.Empty;

        /// <summary>
        /// System model
        /// </summary>
        public string Model { get; set; } = string.Empty;

        /// <summary>
        /// Total physical memory in GB
        /// </summary>
        public long TotalMemoryGB { get; set; }

        /// <summary>
        /// CPU name/model
        /// </summary>
        public string CpuName { get; set; } = string.Empty;

        /// <summary>
        /// Number of CPU cores
        /// </summary>
        public int CpuCores { get; set; }

        /// <summary>
        /// Domain the computer is joined to
        /// </summary>
        public string Domain { get; set; } = string.Empty;

        /// <summary>
        /// Workgroup name (if not domain joined)
        /// </summary>
        public string Workgroup { get; set; } = string.Empty;

        /// <summary>
        /// Whether the device is domain joined
        /// </summary>
        public bool IsDomainJoined { get; set; }

        /// <summary>
        /// Last boot time
        /// </summary>
        public DateTime LastBootTime { get; set; }

        /// <summary>
        /// Time zone information
        /// </summary>
        public string TimeZone { get; set; } = string.Empty;

        /// <summary>
        /// Installed antivirus products
        /// </summary>
        public List<string> AntivirusProducts { get; set; } = new List<string>();

        /// <summary>
        /// Windows Defender status
        /// </summary>
        public bool DefenderEnabled { get; set; }

        /// <summary>
        /// BitLocker encryption status
        /// </summary>
        public bool BitLockerEnabled { get; set; }

        /// <summary>
        /// TPM (Trusted Platform Module) status
        /// </summary>
        public bool TpmEnabled { get; set; }

        /// <summary>
        /// Secure Boot status
        /// </summary>
        public bool SecureBootEnabled { get; set; }

        /// <summary>
        /// Windows Update status
        /// </summary>
        public string WindowsUpdateStatus { get; set; } = string.Empty;

        /// <summary>
        /// Last Windows Update install date
        /// </summary>
        public DateTime? LastUpdateInstalled { get; set; }

        /// <summary>
        /// Generate a unique device fingerprint
        /// </summary>
        public string GenerateFingerprint()
        {
            var fingerprintData = $"{HardwareUuid}|{MotherboardSerial}|{CpuId}|{MacAddress}";
            using var sha256 = System.Security.Cryptography.SHA256.Create();
            var hashBytes = sha256.ComputeHash(System.Text.Encoding.UTF8.GetBytes(fingerprintData));
            return Convert.ToBase64String(hashBytes);
        }

        /// <summary>
        /// Check if device information is complete enough for correlation
        /// </summary>
        public bool IsValidForCorrelation()
        {
            // Need at least one strong identifier
            return !string.IsNullOrWhiteSpace(HardwareUuid) ||
                   !string.IsNullOrWhiteSpace(MotherboardSerial) ||
                   (!string.IsNullOrWhiteSpace(CpuId) && !string.IsNullOrWhiteSpace(MacAddress));
        }
    }
}
