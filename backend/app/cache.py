"""
Simple in-memory cache module for the MVP application.
"""
import time
from typing import Dict, Any, Optional


class SimpleCache:
    """Simple in-memory cache with TTL (Time To Live)"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry['expires_at']:
                return entry['value']
            else:
                # Expired, remove it
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache with TTL (default 5 minutes)"""
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl_seconds
        }
    
    def delete(self, key: str) -> None:
        """Delete specific key from cache"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of cache entries (cleaning expired ones first)"""
        current_time = time.time()
        expired_keys = [k for k, v in self._cache.items() if current_time >= v['expires_at']]
        for key in expired_keys:
            del self._cache[key]
        return len(self._cache)


# Global cache instance
app_cache = SimpleCache()

