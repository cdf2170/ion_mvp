"""
Okta Connector - Pulls user and group data from Okta.

This demonstrates how to implement a specific API connector
using the base connector framework.
"""

import logging
from typing import Dict, Any, List

from backend.app.services.connectors.base_connector import BaseConnector, APIError

logger = logging.getLogger(__name__)


class OktaConnector(BaseConnector):
    """
    Connector for Okta Identity Provider.
    
    Pulls:
    - Users with profile information
    - Group memberships
    - User status (active/suspended)
    """
    
    def _setup_authentication(self):
        """Set up Okta API authentication using API token."""
        api_token = self.credentials.get('api_token')
        if not api_token:
            raise APIError("Okta API token not found in credentials")
        
        # Set authorization header
        self.session.headers.update({
            'Authorization': f'SSWS {api_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Okta connection by fetching current user info."""
        try:
            # Test with a simple API call
            response = self._make_request('GET', '/api/v1/users/me')
            data = response.json()
            
            return {
                "status": "success",
                "message": f"Connected to Okta as {data.get('profile', {}).get('email', 'unknown')}",
                "details": {
                    "okta_domain": self.connection.base_url,
                    "api_version": "v1",
                    "user_email": data.get('profile', {}).get('email')
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Okta connection failed: {str(e)}"
            }
    
    def get_users(self) -> List[Dict[str, Any]]:
        """
        Get all users from Okta with their profile information.
        
        Returns:
            List of user dictionaries with standardized field names
        """
        try:
            # Fetch users with pagination
            users = self._paginate_results('/api/v1/users', params={
                'limit': 200,  # Max per page
                'filter': 'status eq "ACTIVE" or status eq "SUSPENDED"'
            })
            
            standardized_users = []
            for okta_user in users:
                # Map Okta user format to our standard format
                standardized_user = self._standardize_user(okta_user)
                standardized_users.append(standardized_user)
            
            logger.info(f"Retrieved {len(standardized_users)} users from Okta")
            return standardized_users
            
        except Exception as e:
            logger.error(f"Failed to get users from Okta: {e}")
            raise APIError(f"Okta user sync failed: {e}")
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """
        Okta doesn't directly manage devices, but we can get device info
        from user login sessions or device trust policies.
        """
        # Okta primarily manages users, not devices
        # This would require additional Okta Device Trust API calls
        logger.info("Okta device sync not implemented - Okta primarily manages users")
        return []
    
    def get_user_groups(self, user_id: str) -> List[str]:
        """Get groups for a specific user."""
        try:
            response = self._make_request('GET', f'/api/v1/users/{user_id}/groups')
            groups = response.json()
            
            return [group['profile']['name'] for group in groups]
            
        except Exception as e:
            logger.error(f"Failed to get groups for user {user_id}: {e}")
            return []
    
    def _standardize_user(self, okta_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Okta user format to our standardized format.
        
        Args:
            okta_user: Raw user data from Okta API
            
        Returns:
            Standardized user dictionary
        """
        profile = okta_user.get('profile', {})
        
        # Map Okta fields to our standard fields
        standardized = {
            'email': profile.get('email'),
            'first_name': profile.get('firstName'),
            'last_name': profile.get('lastName'),
            'full_name': f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip(),
            'department': profile.get('department'),
            'title': profile.get('title'),
            'manager': profile.get('manager'),
            'office': profile.get('city'),
            'phone': profile.get('mobilePhone') or profile.get('primaryPhone'),
            'employee_id': profile.get('employeeNumber'),
            'status': self._map_okta_status(okta_user.get('status')),
            'last_login': okta_user.get('lastLogin'),
            'created': okta_user.get('created'),
            'activated': okta_user.get('activated'),
            'password_changed': okta_user.get('passwordChanged'),
            'okta_id': okta_user.get('id')
        }
        
        # Get user's groups
        if okta_user.get('id'):
            standardized['groups'] = self.get_user_groups(okta_user['id'])
        
        return standardized
    
    def _map_okta_status(self, okta_status: str) -> str:
        """Map Okta status to our standard status."""
        status_mapping = {
            'ACTIVE': 'active',
            'SUSPENDED': 'disabled',
            'DEPROVISIONED': 'disabled',
            'PROVISIONED': 'active',
            'RECOVERY': 'active',
            'LOCKED_OUT': 'disabled'
        }
        
        return status_mapping.get(okta_status, 'unknown')
    
    def _extract_page_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Okta returns results as a direct array."""
        if isinstance(data, list):
            return data
        return []
    
    def _get_next_page_url(self, data: Dict[str, Any], response) -> str:
        """Okta uses Link header for pagination."""
        link_header = response.headers.get('Link')
        if link_header and 'rel="next"' in link_header:
            import re
            match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
            if match:
                return match.group(1)
        return None


# Example of how to extend for other Okta features
class OktaAdvancedConnector(OktaConnector):
    """Extended Okta connector with additional features."""
    
    def get_applications(self) -> List[Dict[str, Any]]:
        """Get applications and user assignments."""
        try:
            apps = self._paginate_results('/api/v1/apps', params={'limit': 200})
            return apps
        except Exception as e:
            logger.error(f"Failed to get applications from Okta: {e}")
            return []
    
    def get_user_app_assignments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get app assignments for a specific user."""
        try:
            response = self._make_request('GET', f'/api/v1/apps?filter=user.id eq "{user_id}"')
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get app assignments for user {user_id}: {e}")
            return []
