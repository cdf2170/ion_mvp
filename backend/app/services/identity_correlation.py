"""
Identity Correlation Engine - The "Brain" of Your System

This module handles automatic mapping of data from external APIs to canonical identities
with proper fallbacks, conflict resolution, and error handling.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.app.db.models import (
    CanonicalIdentity, Device, Account, GroupMembership, 
    StatusEnum, DeviceStatusEnum, ActivityHistory, ActivityTypeEnum
)

logger = logging.getLogger(__name__)


class IdentityCorrelationEngine:
    """
    The core engine that correlates external API data to canonical identities.
    
    This is the "brain" that:
    - Matches users across systems by email, employee ID, etc.
    - Resolves data conflicts using business rules
    - Handles errors gracefully with fallbacks
    - Detects orphaned resources
    - Validates data integrity
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.correlation_stats = {
            "users_processed": 0,
            "users_created": 0,
            "users_updated": 0,
            "conflicts_resolved": 0,
            "errors": []
        }
    
    def correlate_user_data(self, api_data: Dict[str, Any], source_system: str) -> Tuple[CanonicalIdentity, bool]:
        """
        Main entry point for correlating user data from any API.
        
        Args:
            api_data: User data from external API
            source_system: Name of the source system (e.g., "Okta", "Azure AD")
            
        Returns:
            Tuple of (canonical_user, was_created)
        """
        try:
            self.correlation_stats["users_processed"] += 1
            
            # Step 1: Validate incoming data
            validated_data = self._validate_user_data(api_data, source_system)
            
            # Step 2: Find or create canonical identity
            canonical_user, was_created = self._find_or_create_canonical_user(validated_data, source_system)
            
            # Step 3: Update user data with conflict resolution
            self._update_user_with_conflict_resolution(canonical_user, validated_data, source_system)
            
            # Step 4: Update statistics
            if was_created:
                self.correlation_stats["users_created"] += 1
            else:
                self.correlation_stats["users_updated"] += 1
            
            # Step 5: Log activity
            self._log_correlation_activity(canonical_user, source_system, "USER_CORRELATED")
            
            return canonical_user, was_created
            
        except Exception as e:
            error_msg = f"Failed to correlate user data from {source_system}: {str(e)}"
            logger.error(error_msg)
            self.correlation_stats["errors"].append(error_msg)
            
            # Return None to indicate failure - caller should handle
            raise CorrelationError(error_msg) from e
    
    def correlate_device_data(self, device_data: Dict[str, Any], source_system: str) -> Tuple[Device, bool]:
        """
        Correlate device data from external APIs to canonical devices.
        
        Args:
            device_data: Device data from external API
            source_system: Name of the source system (e.g., "CrowdStrike", "Jamf")
            
        Returns:
            Tuple of (device, was_created)
        """
        try:
            # Step 1: Validate device data
            validated_data = self._validate_device_data(device_data, source_system)
            
            # Step 2: Find owner by various methods
            owner_cid = self._find_device_owner(validated_data, source_system)
            
            # Step 3: Find or create device
            device, was_created = self._find_or_create_device(validated_data, owner_cid, source_system)
            
            # Step 4: Update device data
            self._update_device_data(device, validated_data, source_system)
            
            # Step 5: Log activity
            if owner_cid:
                self._log_correlation_activity(None, source_system, "DEVICE_CORRELATED", device_id=device.id)
            
            return device, was_created
            
        except Exception as e:
            error_msg = f"Failed to correlate device data from {source_system}: {str(e)}"
            logger.error(error_msg)
            self.correlation_stats["errors"].append(error_msg)
            raise CorrelationError(error_msg) from e
    
    def _validate_user_data(self, api_data: Dict[str, Any], source_system: str) -> Dict[str, Any]:
        """Validate and normalize user data from external APIs."""
        validated = {}
        
        # Email is required for correlation
        email = api_data.get("email") or api_data.get("userPrincipalName") or api_data.get("mail")
        if not email:
            raise ValueError(f"No email found in user data from {source_system}")
        
        validated["email"] = email.lower().strip()
        
        # Name fields with fallbacks
        validated["full_name"] = (
            api_data.get("full_name") or 
            api_data.get("displayName") or
            f"{api_data.get('firstName', '')} {api_data.get('lastName', '')}".strip() or
            f"{api_data.get('givenName', '')} {api_data.get('surname', '')}".strip() or
            email.split("@")[0]  # Fallback to email prefix
        )
        
        # Department with various field names
        validated["department"] = (
            api_data.get("department") or
            api_data.get("dept") or
            api_data.get("division") or
            "Unknown"
        )
        
        # Role/Title
        validated["role"] = (
            api_data.get("role") or
            api_data.get("title") or
            api_data.get("jobTitle") or
            "Employee"
        )
        
        # Manager
        validated["manager"] = api_data.get("manager") or api_data.get("managerDisplayName")
        
        # Location
        validated["location"] = (
            api_data.get("location") or
            api_data.get("office") or
            api_data.get("city")
        )
        
        # Status
        status_value = api_data.get("status") or api_data.get("accountEnabled")
        if status_value in [True, "active", "Active", "enabled", "Enabled"]:
            validated["status"] = StatusEnum.ACTIVE
        else:
            validated["status"] = StatusEnum.DISABLED
        
        # Employee ID for additional correlation
        validated["employee_id"] = api_data.get("employee_id") or api_data.get("employeeId")
        
        return validated
    
    def _find_or_create_canonical_user(self, validated_data: Dict[str, Any], source_system: str) -> Tuple[CanonicalIdentity, bool]:
        """
        Find existing canonical user or create new one using multiple correlation strategies.
        """
        # Strategy 1: Match by email (primary method)
        existing_user = self.db.query(CanonicalIdentity).filter(
            CanonicalIdentity.email == validated_data["email"]
        ).first()
        
        if existing_user:
            logger.info(f"Found existing user by email: {validated_data['email']}")
            return existing_user, False
        
        # Strategy 2: Match by employee ID (if available)
        if validated_data.get("employee_id"):
            # Note: We'd need to add employee_id field to CanonicalIdentity model
            # For now, we'll search in a custom field or skip this strategy
            pass
        
        # Strategy 3: Fuzzy match by name and department (last resort)
        potential_matches = self.db.query(CanonicalIdentity).filter(
            and_(
                CanonicalIdentity.full_name.ilike(f"%{validated_data['full_name']}%"),
                CanonicalIdentity.department == validated_data["department"]
            )
        ).all()
        
        if len(potential_matches) == 1:
            logger.warning(f"Found potential match by name+department: {validated_data['full_name']}")
            # In production, you might want to flag this for manual review
            return potential_matches[0], False
        elif len(potential_matches) > 1:
            logger.warning(f"Multiple potential matches found for {validated_data['full_name']} - creating new user")
        
        # No match found - create new canonical identity
        new_user = CanonicalIdentity(
            cid=uuid4(),
            email=validated_data["email"],
            full_name=validated_data["full_name"],
            department=validated_data["department"],
            role=validated_data["role"],
            manager=validated_data.get("manager"),
            location=validated_data.get("location"),
            status=validated_data["status"]
        )
        
        self.db.add(new_user)
        self.db.flush()  # Get the ID
        
        logger.info(f"Created new canonical user: {validated_data['email']}")
        return new_user, True
    
    def _update_user_with_conflict_resolution(self, user: CanonicalIdentity, new_data: Dict[str, Any], source_system: str):
        """
        Update user data using business rules for conflict resolution.
        """
        # Business Rules for Data Precedence:
        hr_systems = ["Workday", "BambooHR", "ADP"]
        identity_systems = ["Okta", "Azure AD", "Auth0"]
        
        conflicts_resolved = 0
        
        # Rule 1: HR systems win for department and role
        if source_system in hr_systems:
            if user.department != new_data["department"]:
                logger.info(f"HR system updating department: {user.department} -> {new_data['department']}")
                user.department = new_data["department"]
                conflicts_resolved += 1
            
            if user.role != new_data["role"]:
                logger.info(f"HR system updating role: {user.role} -> {new_data['role']}")
                user.role = new_data["role"]
                conflicts_resolved += 1
        
        # Rule 2: Identity systems win for status
        if source_system in identity_systems:
            if user.status != new_data["status"]:
                logger.info(f"Identity system updating status: {user.status} -> {new_data['status']}")
                user.status = new_data["status"]
                conflicts_resolved += 1
        
        # Rule 3: Most recent update wins for contact info
        if new_data.get("manager") and new_data["manager"] != user.manager:
            user.manager = new_data["manager"]
            conflicts_resolved += 1
        
        if new_data.get("location") and new_data["location"] != user.location:
            user.location = new_data["location"]
            conflicts_resolved += 1
        
        # Rule 4: Never overwrite full_name with worse data
        if len(new_data["full_name"]) > len(user.full_name or ""):
            user.full_name = new_data["full_name"]
            conflicts_resolved += 1
        
        # Update last_seen timestamp
        user.last_seen = datetime.now()
        
        if conflicts_resolved > 0:
            self.correlation_stats["conflicts_resolved"] += conflicts_resolved
            logger.info(f"Resolved {conflicts_resolved} conflicts for user {user.email}")
    
    def _validate_device_data(self, device_data: Dict[str, Any], source_system: str) -> Dict[str, Any]:
        """Validate and normalize device data from external APIs."""
        validated = {}
        
        # Device name/hostname - we'll improve this later if we have owner info
        validated["name"] = (
            device_data.get("name") or
            device_data.get("hostname") or
            device_data.get("device_name") or
            device_data.get("computer_name") or
            f"Unknown Device {uuid4().hex[:8]}"
        )
        
        # Network information
        validated["ip_address"] = device_data.get("ip_address") or device_data.get("local_ip")
        validated["mac_address"] = device_data.get("mac_address") or device_data.get("mac")
        validated["vlan"] = device_data.get("vlan") or device_data.get("network_segment")
        
        # System information
        validated["os_version"] = (
            device_data.get("os_version") or
            device_data.get("operating_system") or
            device_data.get("platform")
        )
        
        # Status
        status_value = device_data.get("status") or device_data.get("online")
        if status_value in ["online", "connected", True, "Online", "Connected"]:
            validated["status"] = DeviceStatusEnum.CONNECTED
        elif status_value in ["offline", "disconnected", False, "Offline", "Disconnected"]:
            validated["status"] = DeviceStatusEnum.DISCONNECTED
        else:
            validated["status"] = DeviceStatusEnum.UNKNOWN
        
        # Compliance
        compliance_value = device_data.get("compliant") or device_data.get("compliant_status")
        validated["compliant"] = compliance_value in [True, "compliant", "Compliant", "pass", "Pass"]
        
        # Owner identification data
        validated["owner_email"] = (
            device_data.get("owner_email") or
            device_data.get("user_email") or
            device_data.get("assigned_user")
        )
        
        validated["owner_id"] = device_data.get("owner_id") or device_data.get("user_id")
        
        return validated
    
    def _find_device_owner(self, device_data: Dict[str, Any], source_system: str) -> Optional[UUID]:
        """
        Find the canonical user who owns this device using multiple strategies.
        """
        # Strategy 1: Match by owner email
        if device_data.get("owner_email"):
            owner = self.db.query(CanonicalIdentity).filter(
                CanonicalIdentity.email == device_data["owner_email"].lower()
            ).first()
            if owner:
                return owner.cid
        
        # Strategy 2: Extract owner from device name patterns
        device_name = device_data["name"].lower()
        
        # Common patterns: "John's MacBook", "MacBook-jsmith", "LAPTOP-JSMITH"
        if "'s " in device_name:
            owner_name = device_name.split("'s ")[0].strip()
            potential_owners = self.db.query(CanonicalIdentity).filter(
                CanonicalIdentity.full_name.ilike(f"%{owner_name}%")
            ).all()
            if len(potential_owners) == 1:
                return potential_owners[0].cid
        
        # Strategy 3: Look for email patterns in device name
        if "@" in device_name:
            # Extract email from device name
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, device_name)
            if emails:
                owner = self.db.query(CanonicalIdentity).filter(
                    CanonicalIdentity.email == emails[0].lower()
                ).first()
                if owner:
                    return owner.cid
        
        # No owner found - device will be orphaned
        logger.warning(f"Could not find owner for device: {device_data['name']}")
        return None
    
    def _find_or_create_device(self, device_data: Dict[str, Any], owner_cid: Optional[UUID], source_system: str) -> Tuple[Device, bool]:
        """Find existing device or create new one."""
        
        # Try to find existing device by multiple criteria
        existing_device = None
        
        # Strategy 1: Match by MAC address (most reliable)
        if device_data.get("mac_address"):
            existing_device = self.db.query(Device).filter(
                Device.mac_address == device_data["mac_address"]
            ).first()
        
        # Strategy 2: Match by name and owner
        if not existing_device and owner_cid:
            existing_device = self.db.query(Device).filter(
                and_(
                    Device.name == device_data["name"],
                    Device.owner_cid == owner_cid
                )
            ).first()
        
        # Strategy 3: Match by IP address (less reliable)
        if not existing_device and device_data.get("ip_address"):
            existing_device = self.db.query(Device).filter(
                Device.ip_address == device_data["ip_address"]
            ).first()
        
        if existing_device:
            return existing_device, False
        
        # Improve device name with owner information if available
        improved_name = self._improve_device_name(device_data["name"], owner_cid)
        
        # Create new device
        new_device = Device(
            id=uuid4(),
            name=improved_name,
            owner_cid=owner_cid,
            ip_address=device_data.get("ip_address"),
            mac_address=device_data.get("mac_address"),
            vlan=device_data.get("vlan"),
            os_version=device_data.get("os_version"),
            status=device_data["status"],
            compliant=device_data["compliant"]
        )
        
        self.db.add(new_device)
        self.db.flush()
        
        return new_device, True
    
    def _update_device_data(self, device: Device, new_data: Dict[str, Any], source_system: str):
        """Update device data with source-specific rules."""
        
        # Security/MDM systems win for compliance status
        security_systems = ["CrowdStrike", "Jamf", "Intune", "Carbon Black"]
        
        if source_system in security_systems:
            device.compliant = new_data["compliant"]
            device.status = new_data["status"]
        
        # Network systems win for network info
        network_systems = ["Cisco ISE", "Aruba ClearPass", "Network Scanner"]
        
        if source_system in network_systems:
            if new_data.get("ip_address"):
                device.ip_address = new_data["ip_address"]
            if new_data.get("vlan"):
                device.vlan = new_data["vlan"]
        
        # Always update last_check_in and OS info
        device.last_check_in = datetime.now()
        if new_data.get("os_version"):
            device.os_version = new_data["os_version"]
        
        # Improve device name if we have better owner information now
        if device.owner_cid:
            improved_name = self._improve_device_name(device.name, device.owner_cid)
            if improved_name != device.name:
                logger.info(f"Improving device name: '{device.name}' -> '{improved_name}'")
                device.name = improved_name
    
    def _improve_device_name(self, current_name: str, owner_cid: UUID) -> str:
        """
        Improve device name by adding last name for better clarity.
        
        Examples:
        - "Brandon's iPad" + owner "Brandon Smith" -> "Brandon Smith's iPad"
        - "LAPTOP-JOHN" + owner "John Doe" -> "John Doe's Laptop"
        - "Unknown Device" + owner "Jane Wilson" -> "Jane Wilson's Device"
        
        Args:
            current_name: Current device name
            owner_cid: Canonical identity of the device owner
            
        Returns:
            Improved device name with last name included
        """
        try:
            # Get owner information
            owner = self.db.query(CanonicalIdentity).filter(
                CanonicalIdentity.cid == owner_cid
            ).first()
            
            if not owner or not owner.full_name:
                return current_name
            
            # Parse owner name
            name_parts = owner.full_name.strip().split()
            if len(name_parts) < 2:
                return current_name  # Need at least first and last name
            
            first_name = name_parts[0]
            last_name = name_parts[-1]  # Last name is the last part
            full_name = f"{first_name} {last_name}"
            
            # Pattern 1: "FirstName's Device" -> "FirstName LastName's Device"
            if f"{first_name}'s " in current_name:
                improved_name = current_name.replace(f"{first_name}'s ", f"{full_name}'s ")
                return improved_name
            
            # Pattern 2: "FIRSTNAME-DEVICE" -> "FirstName LastName's Device"
            if f"{first_name.upper()}-" in current_name.upper():
                device_part = current_name.upper().split(f"{first_name.upper()}-", 1)[1]
                # Convert device part to title case
                device_part = device_part.replace("-", " ").replace("_", " ")
                device_part = " ".join(word.capitalize() for word in device_part.split())
                improved_name = f"{full_name}'s {device_part}"
                return improved_name
            
            # Pattern 3: "LAPTOP-FIRSTNAME" -> "FirstName LastName's Laptop"
            if f"-{first_name.upper()}" in current_name.upper():
                device_part = current_name.upper().split(f"-{first_name.upper()}", 1)[0]
                device_part = device_part.replace("-", " ").replace("_", " ")
                device_part = " ".join(word.capitalize() for word in device_part.split())
                improved_name = f"{full_name}'s {device_part}"
                return improved_name
            
            # Pattern 4: Generic device names -> "FirstName LastName's Device"
            generic_patterns = ["unknown device", "device", "computer", "laptop", "desktop", "workstation"]
            if any(pattern in current_name.lower() for pattern in generic_patterns):
                # Extract device type if possible
                device_type = "Device"
                for pattern in ["laptop", "desktop", "workstation", "computer"]:
                    if pattern in current_name.lower():
                        device_type = pattern.capitalize()
                        break
                improved_name = f"{full_name}'s {device_type}"
                return improved_name
            
            # Pattern 5: If name contains first name but not last name, add last name
            if first_name in current_name and last_name not in current_name:
                # Try to insert last name before the possessive
                if "'s " in current_name:
                    improved_name = current_name.replace(f"{first_name}'s ", f"{full_name}'s ")
                    return improved_name
                elif f"{first_name} " in current_name:
                    improved_name = current_name.replace(f"{first_name} ", f"{full_name} ")
                    return improved_name
            
            # If no patterns match, return original name
            return current_name
            
        except Exception as e:
            logger.error(f"Failed to improve device name '{current_name}': {e}")
            return current_name
    
    def _log_correlation_activity(self, user: Optional[CanonicalIdentity], source_system: str, activity_type: str, device_id: Optional[UUID] = None):
        """Log correlation activities for audit trail."""
        try:
            activity = ActivityHistory(
                id=uuid4(),
                user_cid=user.cid if user else None,
                device_id=device_id,
                activity_type=ActivityTypeEnum.CONFIGURATION_CHANGE,
                source_system=source_system,
                description=f"Data correlation from {source_system}: {activity_type}",
                timestamp=datetime.now(),
                risk_score="Low"
            )
            self.db.add(activity)
        except Exception as e:
            logger.error(f"Failed to log correlation activity: {e}")
    
    def detect_orphaned_resources(self) -> Dict[str, List[Dict]]:
        """
        Detect orphaned resources that need attention.
        """
        orphans = {
            "devices_without_owners": [],
            "accounts_without_users": [],
            "inactive_users_with_resources": []
        }
        
        # Find devices without owners
        orphaned_devices = self.db.query(Device).filter(
            Device.owner_cid.is_(None)
        ).all()
        
        for device in orphaned_devices:
            orphans["devices_without_owners"].append({
                "id": str(device.id),
                "name": device.name,
                "ip_address": str(device.ip_address) if device.ip_address else None,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None
            })
        
        # Find accounts without canonical users
        orphaned_accounts = self.db.query(Account).filter(
            Account.cid.is_(None)
        ).all()
        
        for account in orphaned_accounts:
            orphans["accounts_without_users"].append({
                "id": str(account.id),
                "service": account.service,
                "user_email": account.user_email
            })
        
        # Find inactive users with active resources
        inactive_with_resources = self.db.query(CanonicalIdentity).filter(
            CanonicalIdentity.status == StatusEnum.DISABLED
        ).join(Device).all()
        
        for user in inactive_with_resources:
            device_count = len(user.devices)
            account_count = len(user.accounts)
            if device_count > 0 or account_count > 0:
                orphans["inactive_users_with_resources"].append({
                    "cid": str(user.cid),
                    "email": user.email,
                    "full_name": user.full_name,
                    "device_count": device_count,
                    "account_count": account_count
                })
        
        return orphans
    
    def get_correlation_stats(self) -> Dict[str, Any]:
        """Get statistics from the correlation process."""
        return self.correlation_stats.copy()


class CorrelationError(Exception):
    """Custom exception for correlation errors."""
    pass
