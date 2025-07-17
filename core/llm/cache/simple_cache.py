"""
Simple in-memory cache for LLM responses.
Phase 1 implementation using basic dictionary storage.
"""

import logging
import time
from typing import Dict, Any, Optional
from core.logging_config import get_logger


class SimpleCache:
    """Basic in-memory cache for LLM responses."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.logger = get_logger("llm.cache")
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[str]:
        """Get cached response by key."""
        if key not in self._cache:
            return None
        
        # Check if expired
        entry = self._cache[key]
        if time.time() - entry['timestamp'] > self.ttl_seconds:
            self._remove_key(key)
            self.logger.debug(f"Cache entry expired: {key}")
            return None
        
        # Update access time
        self._access_times[key] = time.time()
        
        self.logger.debug(f"Cache hit: {key}")
        return entry['response']
    
    def set(self, key: str, response: str):
        """Set cached response."""
        # Remove oldest entries if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        timestamp = time.time()
        self._cache[key] = {
            'response': response,
            'timestamp': timestamp
        }
        self._access_times[key] = timestamp
        
        self.logger.debug(f"Cache set: {key}")
    
    def _remove_key(self, key: str):
        """Remove key from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_times:
            del self._access_times[key]
    
    def _evict_oldest(self):
        """Remove the least recently used entry."""
        if not self._access_times:
            return
        
        oldest_key = min(self._access_times, key=self._access_times.get)
        self._remove_key(oldest_key)
        self.logger.debug(f"Evicted oldest cache entry: {oldest_key}")
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        self._access_times.clear()
        self.logger.info("Cache cleared")
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry['timestamp'] > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self._remove_key(key)
        
        if expired_keys:
            self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds,
            'oldest_entry': min(
                (entry['timestamp'] for entry in self._cache.values()),
                default=None
            ),
            'newest_entry': max(
                (entry['timestamp'] for entry in self._cache.values()),
                default=None
            )
        }