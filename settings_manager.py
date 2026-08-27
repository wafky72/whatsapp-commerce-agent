import sqlite3
import json
from typing import Dict, Any

class SettingsManager:
    """
    Manages all admin panel settings with SQLite persistence.
    """
    def __init__(self, db_path="config.db"):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Create settings table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Set defaults if first time
        defaults = self.get_default_settings()
        for key, value in defaults.items():
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
        
        conn.commit()
        conn.close()
    
    def get_default_settings(self) -> Dict[str, Any]:
        """Define default configuration."""
        return {
            # Widget Appearance
            "widget_position": "bottom-right",
            "primary_color": "#007bff",
            "secondary_color": "#6c757d",
            "text_color": "#ffffff",
            "bot_avatar": "🤖",
            "welcome_message": "Hello! I am from Roze BioHealth. How can I help you today?",
            "widget_size": "medium",
            
            # Behavior
            "auto_open_delay": 0,
            "show_on_pages": "all",
            "hide_on_mobile": False,
            "typing_indicator": True,
            
            # AI Configuration
            "ai_model": "llama-3.3-70b-versatile",
            "temperature": 0.7,
            "response_length": "medium",
            "fallback_message": "I'm having trouble right now. Please try again.",
            
            # Business Hours
            "business_hours_enabled": False,
            "timezone": "Asia/Dubai",
            "operating_hours": {"start": "09:00", "end": "18:00"},
            "after_hours_message": "We're currently offline. Our business hours are 9 AM - 6 PM GST."
        }
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Retrieve all settings."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        conn.close()
        
        settings = {}
        for key, value in rows:
            try:
                settings[key] = json.loads(value)
            except:
                settings[key] = value
        
        return settings
    
    def get_setting(self, key: str) -> Any:
        """Get a specific setting."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row[0])
            except:
                return row[0]
        return None
    
    def update_setting(self, key: str, value: Any):
        """Update a single setting."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
            (json.dumps(value), key)
        )
        
        conn.commit()
        conn.close()
    
    def update_settings(self, settings: Dict[str, Any]):
        """Bulk update settings."""
        for key, value in settings.items():
            self.update_setting(key, value)
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        defaults = self.get_default_settings()
        self.update_settings(defaults)
