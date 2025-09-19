"""
Base Connector Class - Foundation for all API connectors.

This provides the common interface and error handling that all
specific API connectors (Okta, Azure AD, etc.) will inherit from.
"""

import logging
import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.app.db.models import APIConnection

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Abstract base class for all API connectors.
    
    This provides:
    - Common error handling
    - Rate limiting
    - Authentication management
    - Retry logic
    - Standard interface
    """
    
    def __init__(self, connection: APIConnection, db):
        self.connection = connection
        self.db = db
        self.session = requests.Session()
        
        # Parse credentials
        try:
            self.credentials = json.loads(connection.credentials) if connection.credentials else {}
        except json.JSONDecodeError:
            self.credentials = {}
        
        # Set up authentication
        self._setup_authentication()
        
        # Rate limiting
        self.rate_limit_requests = int(connection.rate_limit_requests or "100")
        self.rate_limit_window = connection.rate_limit_window or "minute"
        self.request_timestamps = []
    
    @abstractmethod
    def _setup_authentication(self):
        """Set up authentication for this API. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_users(self) -> List[Dict[str, Any]]:
        """Get users from this API. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get devices from this API. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test the API connection. Must be implemented by subclasses."""
        pass
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with error handling and rate limiting.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL or relative path
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            APIError: If request fails after retries
        """
        # Handle relative URLs
        if not url.startswith('http'):
            url = f"{self.connection.base_url.rstrip('/')}/{url.lstrip('/')}"
        
        # Rate limiting
        self._enforce_rate_limit()
        
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)
                
                # Track request for rate limiting
                self.request_timestamps.append(datetime.now())
                
                # Handle HTTP errors
                if response.status_code == 429:  # Rate limited
                    wait_time = self._get_rate_limit_wait_time(response)
                    logger.warning(f"Rate limited by {self.connection.name}, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code == 401:  # Unauthorized
                    logger.error(f"Authentication failed for {self.connection.name}")
                    raise APIError(f"Authentication failed: {response.text}")
                
                elif response.status_code >= 400:
                    logger.error(f"HTTP {response.status_code} from {self.connection.name}: {response.text}")
                    raise APIError(f"HTTP {response.status_code}: {response.text}")
                
                return response
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                if attempt == max_retries - 1:
                    raise APIError(f"Request timeout after {max_retries} attempts")
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1} for {url}: {e}")
                if attempt == max_retries - 1:
                    raise APIError(f"Connection error after {max_retries} attempts: {e}")
                
            # Wait before retry
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
        
        raise APIError(f"Request failed after {max_retries} attempts")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting based on connection configuration."""
        if not self.rate_limit_requests:
            return
        
        # Clean old timestamps
        cutoff_time = self._get_rate_limit_cutoff()
        self.request_timestamps = [
            ts for ts in self.request_timestamps if ts > cutoff_time
        ]
        
        # Check if we're at the limit
        if len(self.request_timestamps) >= self.rate_limit_requests:
            # Calculate wait time
            oldest_request = min(self.request_timestamps)
            wait_until = oldest_request + self._get_rate_limit_window_delta()
            wait_time = (wait_until - datetime.now()).total_seconds()
            
            if wait_time > 0:
                logger.info(f"Rate limiting: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
    
    def _get_rate_limit_cutoff(self) -> datetime:
        """Get the cutoff time for rate limit tracking."""
        return datetime.now() - self._get_rate_limit_window_delta()
    
    def _get_rate_limit_window_delta(self) -> timedelta:
        """Get the time delta for the rate limit window."""
        if self.rate_limit_window == "minute":
            return timedelta(minutes=1)
        elif self.rate_limit_window == "hour":
            return timedelta(hours=1)
        else:
            return timedelta(minutes=1)  # Default
    
    def _get_rate_limit_wait_time(self, response: requests.Response) -> int:
        """Extract wait time from rate limit response headers."""
        # Try common rate limit headers
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
        
        # Try X-RateLimit-Reset
        reset_time = response.headers.get('X-RateLimit-Reset')
        if reset_time:
            try:
                reset_timestamp = int(reset_time)
                wait_time = reset_timestamp - int(datetime.now().timestamp())
                return max(wait_time, 1)
            except ValueError:
                pass
        
        # Default wait time
        return 60
    
    def _paginate_results(self, initial_url: str, params: Dict = None) -> List[Dict[str, Any]]:
        """
        Handle paginated API responses.
        
        Args:
            initial_url: Starting URL
            params: Query parameters
            
        Returns:
            Combined results from all pages
        """
        all_results = []
        url = initial_url
        page = 1
        max_pages = 100  # Safety limit
        
        while url and page <= max_pages:
            try:
                response = self._make_request('GET', url, params=params if page == 1 else None)
                data = response.json()
                
                # Extract results (this may need customization per API)
                results = self._extract_page_results(data)
                all_results.extend(results)
                
                # Get next page URL
                url = self._get_next_page_url(data, response)
                page += 1
                
                logger.debug(f"Fetched page {page-1}, got {len(results)} results")
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        logger.info(f"Fetched {len(all_results)} total results across {page-1} pages")
        return all_results
    
    def _extract_page_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract results from a page of data.
        Override this in subclasses for API-specific response formats.
        """
        # Common patterns
        if isinstance(data, list):
            return data
        elif 'data' in data:
            return data['data']
        elif 'results' in data:
            return data['results']
        elif 'items' in data:
            return data['items']
        else:
            return []
    
    def _get_next_page_url(self, data: Dict[str, Any], response: requests.Response) -> Optional[str]:
        """
        Get the next page URL from response.
        Override this in subclasses for API-specific pagination.
        """
        # Try common pagination patterns
        if 'next' in data:
            return data['next']
        elif 'nextLink' in data:
            return data['nextLink']
        elif '@odata.nextLink' in data:
            return data['@odata.nextLink']
        
        # Check Link header
        link_header = response.headers.get('Link')
        if link_header and 'rel="next"' in link_header:
            import re
            match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
            if match:
                return match.group(1)
        
        return None


class APIError(Exception):
    """Custom exception for API-related errors."""
    pass


# Import time for sleep functionality
import time
