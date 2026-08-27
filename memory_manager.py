import time

class MemoryManager:
    """
    Manages in-memory conversation history with a simple TTL.
    """
    def __init__(self, ttl_seconds=3600, max_history=10):
        self.history = {} # {session_id: [{"role": "...", "content": "..."}]}
        self.expirations = {} # {session_id: timestamp_to_expire}
        self.ttl = ttl_seconds
        self.max_history = max_history

    def get_history(self, session_id):
        """Get history for a session, checking for expiration."""
        now = time.time()
        if session_id in self.expirations:
            if now > self.expirations[session_id]:
                # Expired, clear it
                self.history[session_id] = []
                del self.expirations[session_id]
        
        return self.history.get(session_id, [])

    def add_message(self, session_id, role, content):
        """Add a message to the session's history."""
        if session_id not in self.history:
            self.history[session_id] = []
        
        self.history[session_id].append({"role": role, "content": content})
        
        # Keep it trimmed
        if len(self.history[session_id]) > (self.max_history * 2): # *2 because user/bot pairs
             self.history[session_id] = self.history[session_id][-self.max_history*2:]
        
        # Reset expiration
        self.expirations[session_id] = time.time() + self.ttl

    def clear(self, session_id):
        """Manually clear a session."""
        if session_id in self.history:
            del self.history[session_id]
        if session_id in self.expirations:
            del self.expirations[session_id]
