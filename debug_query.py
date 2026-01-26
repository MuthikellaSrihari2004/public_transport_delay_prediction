from src.database.queries import TransportDB
from datetime import datetime

db = TransportDB()
origin = "Secunderabad"
dest = "Miyapur"
t_type = "Bus"
date_str = "2026-01-26"

try:
    search_date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    ref_day = 6 + search_date_obj.weekday()
    mapped_date = f"2025-01-{ref_day:02d}"
except:
    mapped_date = "2025-01-06"

print(f"Querying: From={origin}, To={dest}, Type={t_type}, Date={mapped_date}")
df = db.get_schedules_by_route(origin, dest, t_type, mapped_date)
print(f"Results found: {len(df)}")
if not df.empty:
    print(df.head())
else:
    # Check if anything exists for those locations at all
    import sqlite3
    conn = sqlite3.connect('data/transport.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM schedules WHERE From_Location=? AND To_Location=? AND Transport_Type=?", (origin, dest, t_type))
    count = cursor.fetchone()[0]
    print(f"General count for route: {count}")
    
    cursor.execute("SELECT DISTINCT Date FROM schedules WHERE From_Location=? AND To_Location=? LIMIT 5")
    dates = cursor.fetchall()
    print(f"Available dates for route: {dates}")
