"""
Caching Layer
In-memory cache for search results
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import threading


class SearchCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.cache = {}
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Dict]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check if expired
                if datetime.now() < entry['expires_at']:
                    self.hits += 1
                    return entry['value']
                else:
                    # Remove expired entry
                    del self.cache[key]
            
            self.misses += 1
            return None
    
    def set(self, key: str, value: Dict):
        """Set value in cache"""
        with self.lock:
            self.cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=self.ttl_seconds),
                'created_at': datetime.now()
            }
    
    def clear(self) -> int:
        """Clear all cache entries"""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            return count
    
    def size(self) -> int:
        """Get cache size"""
        with self.lock:
            # Clean expired entries
            self._clean_expired()
            return len(self.cache)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            'size': self.size(),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2),
            'ttl_seconds': self.ttl_seconds
        }
    
    def _clean_expired(self):
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now >= entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
