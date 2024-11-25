import sqlite3
from datetime import datetime
import json

class DubaiTourismDB:
    def __init__(self):
        self.db_name = "dubai_tourism.db"
        self.init_db()

    def init_db(self):
        """Initialize the database and create tables if they don't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Create interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                travel_dates TEXT,
                duration TEXT,
                group_info TEXT,
                preferences TEXT,
                budget TEXT,
                conversation_history TEXT,
                generated_itinerary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def store_interaction(self, data: dict):
        """Store a new interaction"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO interactions (
                session_id,
                travel_dates,
                duration,
                group_info,
                preferences,
                budget,
                conversation_history,
                generated_itinerary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('session_id', 'default'),
            data.get('travel_dates'),
            str(data.get('duration')),
            data.get('group_info'),
            data.get('preferences'),
            str(data.get('budget')),
            json.dumps(data.get('conversation_history', [])),
            json.dumps(data.get('generated_itinerary', {}))
        ))

        conn.commit()
        conn.close()

    def get_interactions(self, session_id=None):
        """Get all interactions or filter by session_id"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if session_id:
            cursor.execute('SELECT * FROM interactions WHERE session_id = ?', (session_id,))
        else:
            cursor.execute('SELECT * FROM interactions')

        rows = cursor.fetchall()
        conn.close()

        return rows

# Create a global instance
db = DubaiTourismDB() 