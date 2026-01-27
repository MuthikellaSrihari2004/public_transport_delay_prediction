
import sqlite3
import pandas as pd
import os

db_path = 'data/transport.db'

print(f"Checking database at: {db_path}")

if not os.path.exists(db_path):
    print("❌ Database file does NOT exist.")
    exit()

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    if ('schedules',) in tables:
        # Count rows
        count = cursor.execute("SELECT COUNT(1) FROM schedules").fetchone()[0]
        print(f"Total Rows in 'schedules': {count}")
        
        if count > 0:
            # Check date range
            min_date = cursor.execute("SELECT MIN(date) FROM schedules").fetchone()[0]
            max_date = cursor.execute("SELECT MAX(date) FROM schedules").fetchone()[0]
            print(f"Date Range: {min_date} to {max_date}")
            
            # Check specific route
            print("\nChecking Secunderabad -> Miyapur:")
            cursor.execute("SELECT COUNT(1) FROM schedules WHERE from_location='Secunderabad' AND to_location='Miyapur'")
            route_count = cursor.fetchone()[0]
            print(f"Direct Route Count (Any Date): {route_count}")
            
            if route_count > 0:
                 # Check 'Bus' specifically
                cursor.execute("SELECT COUNT(1) FROM schedules WHERE from_location='Secunderabad' AND to_location='Miyapur' AND transport_type='Bus'")
                bus_count = cursor.fetchone()[0]
                print(f"Bus Route Count: {bus_count}")
        else:
             print("⚠️ Table 'schedules' is empty.")
    else:
        print("❌ Table 'schedules' not found.")
        
    conn.close()
    
except Exception as e:
    print(f"❌ Error inspecting DB: {e}")
