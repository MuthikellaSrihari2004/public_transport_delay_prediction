from flask import Flask, render_template, request, redirect, url_for, flash
import os
import sys
from datetime import datetime, timedelta
import sqlite3
from dotenv import load_dotenv

# Load Env
load_dotenv()

# Path Setup
sys.path.append(os.getcwd())

import config

# Ensure directories exist (Critical for Gunicorn/Render)
config.ensure_directories()

try:
    from src.database.queries import TransportDB
    from src.models.engine import ENGINE
except ImportError:
    # Fallback to local import if running from root
    from src.database.queries import TransportDB
    from src.models.engine import ENGINE

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "hyder-transit-secret-key")

# Initialize DB with explicit check
DB = TransportDB()
if not os.path.exists(config.DB_PATH):
    print(f"CRITICAL WARNING: Database file not found at {config.DB_PATH}")

# Route: Home Page
@app.route('/')
def index():
    # Show rich live telemetry
    weather = ENGINE.get_realtime_weather()
    hour = datetime.now().hour
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    traffic = ENGINE._get_traffic(hour, weather['is_rainy'], 0)
    holiday_name = ENGINE._check_holidays(date_str)
    event_flag = ENGINE._check_events(date_str)
    
    # Simple context enrichment
    ctx = {
        "is_peak": (8 <= hour <= 11 or 17 <= hour <= 20),
        "peak_status": "Peak Hours" if (8 <= hour <= 11 or 17 <= hour <= 20) else "Normal Flow",
        "day_type": "Weekend" if datetime.now().weekday() >= 5 else "Weekday",
        "event_flag": event_flag or bool(holiday_name),
        "traffic_status": traffic
    }
    
    live_env = {
        "weather": weather,
        "ctx": ctx,
        "traffic": traffic,
        "holiday_name": holiday_name,
        "is_holiday": bool(holiday_name),
        "event_flag": event_flag
    }
    return render_template('index.html', live_env=live_env)


# Route: Manual Prediction Page
@app.route('/predict')
def prediction_page():
    return render_template('prediction.html')

# API: Search (Used by Prediction Page) & Form Post
@app.route('/search', methods=['POST'])
def search():
    from_loc = request.form.get('from_location', '').strip().title()
    to_loc = request.form.get('to_location', '').strip().title()
    date_str = request.form.get('travel_date', '2026-01-26')
    t_type = request.form.get('transport_type', 'Bus')
    
    # Name Mapping
    mapping = {"Lb Nagar": "L.B. Nagar", "Hi-Tech City": "Hitech City"}
    from_loc = mapping.get(from_loc, from_loc)
    to_loc = mapping.get(to_loc, to_loc)

    # Date Logic
    try:
        search_date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        ref_day = 6 + search_date_obj.weekday()
        mapped_date = f"2025-01-{ref_day:02d}"
    except:
        mapped_date = "2025-01-06"

    # 1. Get Schedules
    schedules_df = DB.get_schedules_by_route(from_loc, to_loc, t_type, mapped_date)
    
    weather = ENGINE.get_realtime_weather()
    hour = datetime.now().hour
    date_str_now = datetime.now().strftime("%Y-%m-%d")
    traffic = ENGINE._get_traffic(hour, weather['is_rainy'], 0)
    holiday_name = ENGINE._check_holidays(date_str_now)
    event_flag = ENGINE._check_events(date_str_now)
    
    live_env = {
        "weather": weather, 
        "ctx": {
            "peak_status": "Peak Hours" if (8 <= hour <= 11 or 17 <= hour <= 20) else "Normal Flow",
            "day_type": "Weekend" if datetime.now().weekday() >= 5 else "Weekday",
            "event_flag": event_flag or bool(holiday_name),
            "traffic_status": traffic
        },
        "traffic": traffic,
        "holiday_name": holiday_name,
        "is_holiday": bool(holiday_name),
        "event_flag": event_flag
    }


    if schedules_df.empty:
        return render_template('index.html', error=f"No services found.", live_env=live_env)

    # 2. Process Batch using Engine (Enforces Distribution)
    schedules_raw = schedules_df.to_dict('records')
    schedules = ENGINE.process_batch(schedules_raw, date_str)

    return render_template('index.html', 
                          schedules=schedules, 
                          from_loc=from_loc, 
                          to_loc=to_loc,
                          travel_date=date_str,
                          t_type=t_type,
                          live_env=live_env)

@app.route('/api/search', methods=['POST'])
def api_search():
    # Logic for Prediction Page JSON API
    data = request.json
    from_loc = data.get('from', '').strip().title()
    to_loc = data.get('to', '').strip().title()
    date_str = data.get('date', '2026-01-26')
    t_type = data.get('type', 'Bus')
    
    mapping = {"Lb Nagar": "L.B. Nagar", "Hi-Tech City": "Hitech City"}
    from_loc = mapping.get(from_loc, from_loc)
    to_loc = mapping.get(to_loc, to_loc)

    try:
        search_date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        ref_day = 6 + search_date_obj.weekday()
        mapped_date = f"2025-01-{ref_day:02d}"
    except:
        mapped_date = "2025-01-06"

    schedules_df = DB.get_schedules_by_route(from_loc, to_loc, t_type, mapped_date)
    
    if schedules_df.empty:
        return {"error": "No services found"}, 404
        
    schedules_raw = schedules_df.to_dict('records')
    # Use same batch process
    schedules = ENGINE.process_batch(schedules_raw, date_str)
    
    # Extract one sample for the "Representative Insight" box
    # We pick the one with highest delay to show 'worst case' or average?
    # Let's pick the first one.
    sample = schedules[0]['prediction']
    
    return {
        "schedules": schedules,
        "representative_insight": sample
    }

def _get_tracking_data(service_id, travel_date):
    conn = sqlite3.connect('data/transport.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules WHERE id = ?", (service_id,))
    service = cursor.fetchone()
    conn.close()

    if not service: return None

    svc_dict = dict(service)
    pred = ENGINE.predict_one(svc_dict, travel_date)
    
    sch_dep = svc_dict['Scheduled_Departure']
    try:
        base_dt = datetime.strptime(f"{travel_date} {sch_dep}", "%Y-%m-%d %H:%M")
    except:
        base_dt = datetime.now()
        
    start_var = 0 if pred['predicted_delay'] == 0 else 2
    actual_start = base_dt + timedelta(minutes=start_var)
    
    dist = svc_dict.get('Distance_KM', 25.0)
    spd = 25 if svc_dict.get('Transport_Type') == 'Bus' else 45
    dur = int((dist/spd)*60)
    
    # Stops logic
    stops = []
    raw_stops = svc_dict.get('Stops', '').split('|')
    now = datetime.now()
    try:
        chk_dt = datetime.strptime(travel_date, "%Y-%m-%d").date()
    except:
        chk_dt = now.date()
        
    is_today = (chk_dt == now.date())
    found_current = False
    
    for i, s_name in enumerate(raw_stops):
        sched_offset = int(i * (dur / max(1, len(raw_stops)-1)))
        sched_time = base_dt + timedelta(minutes=sched_offset)
        delay_at_stop = int(i * (pred['predicted_delay'] / max(1, len(raw_stops)-1)))
        est_time = base_dt + timedelta(minutes=sched_offset + delay_at_stop)
        
        status = "Upcoming"
        is_passed = False
        is_current = False
        
        if is_today:
            if now > est_time + timedelta(minutes=2):
                status = "Departed"
                is_passed = True
            elif now >= est_time - timedelta(minutes=2):
                status = "At Station"
                is_current = True
                found_current = True
            elif not found_current and i > 0:
                prev_delay = int((i-1) * (pred['predicted_delay'] / max(1, len(raw_stops)-1)))
                prev_sched = int((i-1) * (dur / max(1, len(raw_stops)-1)))
                prev_est = base_dt + timedelta(minutes=prev_sched + prev_delay)
                if now > prev_est:
                    status = "In Transit"
                    is_current = True
                    found_current = True
        
        stops.append({
            "name": s_name,
            "est": est_time.strftime("%H:%M"),
            "sched": sched_time.strftime("%H:%M"),
            "is_passed": is_passed,
            "is_current": is_current,
            "status": status
        })

    return {
        "service": svc_dict,
        "info": {
            "Service_ID": svc_dict['Service_ID'],
            "Start_Time": base_dt.strftime("%H:%M"),
            "Reach_Time": (base_dt + timedelta(minutes=dur + pred['predicted_delay'])).strftime("%H:%M"),
            "Is_Live": is_today and any(s['is_current'] or s['is_passed'] for s in stops) and not all(s['is_passed'] for s in stops)
        },
        "insights": pred,
        "stops": stops,
        "now_time": now.strftime('%H:%M:%S')
    }

@app.route('/track/<int:service_id>')
def track(service_id):
    travel_date = request.args.get('date', '2026-01-26')
    data = _get_tracking_data(service_id, travel_date)
    if not data:
        return redirect(url_for('index'))
    return render_template('schedule.html', **data)

@app.route('/api/track/<int:service_id>')
def api_track(service_id):
    travel_date = request.args.get('date', '2026-01-26')
    data = _get_tracking_data(service_id, travel_date)
    if not data:
        return {"error": "Not Found"}, 404
    return data


@app.route('/map')
def live_map():
    weather = ENGINE.get_realtime_weather()
    hour = datetime.now().hour
    date_str = datetime.now().strftime("%Y-%m-%d")
    traffic = ENGINE._get_traffic(hour, weather['is_rainy'], 0)
    holiday_name = ENGINE._check_holidays(date_str)
    event_flag = ENGINE._check_events(date_str)
    
    # Fetch locations for the "From" and "To" dropdowns
    locations = DB.get_locations()
    
    live_env = {
        "weather": weather, 
        "ctx": {"peak_status": "Active", "day_type": "Live"},
        "traffic": traffic,
        "is_holiday": bool(holiday_name),
        "holiday_name": holiday_name,
        "event_flag": event_flag
    }
    return render_template('map.html', live_env=live_env, locations=locations)

@app.route('/api/route', methods=['POST'])
def api_route_details():
    data = request.json
    from_loc = data.get('from', '').strip()
    to_loc = data.get('to', '').strip()
    mode = data.get('mode')
    
    # Handle mappings if client sends old versions
    mapping = {"Lb Nagar": "L.B. Nagar", "Hi-Tech City": "Hitech City"}
    from_loc = mapping.get(from_loc, from_loc)
    to_loc = mapping.get(to_loc, to_loc)
    
    details = DB.get_route_details(from_loc, to_loc, mode)
    if not details:
        # Try title case just in case
        details = DB.get_route_details(from_loc.title(), to_loc.title(), mode)
        
    if not details:
        return {"error": "Route not found in database intelligence."}, 404
    
    return details




@app.route('/analytics')
def analytics():
    weather = ENGINE.get_realtime_weather()
    hour = datetime.now().hour
    date_str = datetime.now().strftime("%Y-%m-%d")
    traffic = ENGINE._get_traffic(hour, weather['is_rainy'], 0)
    holiday_name = ENGINE._check_holidays(date_str)
    event_flag = ENGINE._check_events(date_str)
    live_env = {
        "weather": weather, 
        "ctx": {"peak_status": "Active", "day_type": "Live"},
        "traffic": traffic,
        "is_holiday": bool(holiday_name),
        "holiday_name": holiday_name,
        "event_flag": event_flag
    }
    return render_template('analytics.html', live_env=live_env)



if __name__ == '__main__':
    from src.database.db_config import init_db
    config.ensure_directories()
    init_db()
    app.run(debug=True, port=8000)
