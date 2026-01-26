import sqlite3
import os
import sys
from pathlib import Path

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config

def init_db(db_path=None):
    """Initialize the database schema and create necessary tables"""
    target_path = db_path or str(config.DB_PATH)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    print(f"🗄️  Initializing database at {target_path}...")
    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()
    
    # Create Schedules Table (Snake Case)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        transport_type TEXT,
        route_id TEXT,
        service_id TEXT,
        from_location TEXT,
        to_location TEXT,
        stops TEXT,
        scheduled_departure TEXT,
        scheduled_arrival TEXT,
        actual_departure TEXT,
        actual_arrival TEXT,
        delay_minutes INTEGER,
        delay_reason TEXT,
        weather TEXT,
        is_holiday INTEGER,
        is_peak_hour INTEGER,
        event_scheduled INTEGER,
        traffic_density TEXT,
        temperature_c REAL,
        humidity_pct INTEGER,
        passenger_load INTEGER,
        distance_km REAL,
        weather_score REAL,
        traffic_score REAL,
        weather_traffic_index REAL,
        month INTEGER,
        day_of_week INTEGER,
        is_weekend INTEGER,
        dep_hour INTEGER
    )
    ''')
    
    # Create Indexes for optimization
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_route ON schedules(from_location, to_location, transport_type, date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_service_id ON schedules(service_id)')
    
    # Create Table for Predictions (Audit Log)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        pred_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        from_location TEXT,
        to_location TEXT,
        transport_type TEXT,
        scheduled_time TEXT,
        predicted_delay INTEGER,
        reason TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized successfully.")

if __name__ == "__main__":
    init_db()
