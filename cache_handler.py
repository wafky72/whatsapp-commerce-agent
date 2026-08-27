import json
import hashlib
from datetime import datetime, timedelta

class ResponseCache:
    """
    Simple in-memory cache for AI responses to reduce OpenAI API calls.
    Cache expires after 5 minutes to keep data fresh.
    """
    def __init__(self, ttl_minutes=5):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def _generate_key(self, message: str) -> str:
        """Generate a cache key from the user message."""
        return hashlib.md5(message.lower().strip().encode()).hexdigest()
    
    def get(self, message: str):
        """Retrieve cached response if valid."""
        key = self._generate_key(message)
        if key in self.cache:
            cached_data = self.cache[key]
            # Check if still valid
            if datetime.now() < cached_data['expires']:
                return cached_data['response']
            else:
                # Expired, remove
                del self.cache[key]
        return None
    
    def set(self, message: str, response: str):
        """Cache a response."""
        key = self._generate_key(message)
        self.cache[key] = {
            'response': response,
            'expires': datetime.now() + self.ttl
        }
    
    def clear(self):
        """Clear all cached responses."""
        self.cache = {}
