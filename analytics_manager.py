import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict

class AnalyticsManager:
    """
    Track and analyze chat conversations and performance metrics.
    """
    def __init__(self, db_path="analytics.db"):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Create analytics tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time_ms INTEGER,
                user_satisfaction INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                total_conversations INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0,
                satisfaction_score REAL DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def track_conversation(self, user_message: str, bot_response: str, response_time_ms: int = 0):
        """Log a conversation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (user_message, bot_response, response_time_ms)
            VALUES (?, ?, ?)
        """, (user_message, bot_response, response_time_ms))
        
        conn.commit()
        conn.close()
    
    def get_total_conversations(self, days: int = 7) -> int:
        """Get total conversations in last N days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT COUNT(*) FROM conversations
            WHERE timestamp >= ?
        """, (since_date,))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_most_asked_questions(self, limit: int = 10) -> List[Dict]:
        """Get most frequently asked questions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_message, COUNT(*) as count
            FROM conversations
            WHERE timestamp >= datetime('now', '-30 days')
            GROUP BY LOWER(TRIM(user_message))
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{"question": row[0], "count": row[1]} for row in rows]
    
    def get_avg_response_time(self) -> float:
        """Get average response time in milliseconds."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT AVG(response_time_ms)
            FROM conversations
            WHERE response_time_ms > 0
            AND timestamp >= datetime('now', '-7 days')
        """)
        
        avg = cursor.fetchone()[0] or 0
        conn.close()
        return round(avg, 2)
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily conversation counts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM conversations
            WHERE timestamp >= datetime('now', ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, (f'-{days}',))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{"date": row[0], "count": row[1]} for row in rows]
    
    def get_dashboard_stats(self) -> Dict:
        """Get summary stats for dashboard."""
        return {
            "today": self.get_total_conversations(1),
            "week": self.get_total_conversations(7),
            "month": self.get_total_conversations(30),
            "avg_response_time": self.get_avg_response_time(),
            "most_asked": self.get_most_asked_questions(5),
            "daily_trend": self.get_daily_stats(7)
        }
