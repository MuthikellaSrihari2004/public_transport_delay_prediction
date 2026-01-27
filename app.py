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

def get_live_env():
    """Shared helper to get rich system context for any page"""
    weather = ENGINE.get_realtime_weather()
    now = datetime.now()
    hour = now.hour
    date_str = now.strftime("%Y-%m-%d")
    
    holiday_name = ENGINE._check_holidays(date_str)
    event_flag = ENGINE._check_events(date_str)
    traffic = ENGINE._get_traffic(hour, weather['is_rainy'], event_flag)
    
    is_peak = (8 <= hour <= 11 or 17 <= hour <= 20)
    
    return {
        "weather": weather,
        "ctx": {
            "is_peak": is_peak,
            "peak_status": "Peak Hours" if is_peak else "Normal Flow",
            "day_type": "Weekend" if now.weekday() >= 5 else "Weekday",
            "event_flag": event_flag or bool(holiday_name),
            "traffic_status": traffic
        },
        "traffic": traffic,
        "holiday_name": holiday_name,
        "is_holiday": bool(holiday_name),
        "event_flag": event_flag
    }

# Route: Home Page
@app.route('/')
def index():
    live_env = get_live_env()
    return render_template('index.html', live_env=live_env, today_date=datetime.now().strftime("%Y-%m-%d"))


# Route: Manual Prediction Page
@app.route('/predict')
def prediction_page():
    return render_template('prediction.html', 
                          today_date=datetime.now().strftime("%Y-%m-%d"),
                          live_env=get_live_env())

# API: Search (Used by Prediction Page) & Form Post
@app.route('/search', methods=['POST'])
def search():
    from_loc = request.form.get('from_location', '').strip().title()
    to_loc = request.form.get('to_location', '').strip().title()
    date_str = request.form.get('travel_date', '')
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    t_type = request.form.get('transport_type', 'Bus')
    
    # Name Mapping
    mapping = {"Lb Nagar": "L.B. Nagar", "Hi-Tech City": "Hitech City"}
    from_loc = mapping.get(from_loc, from_loc)
    to_loc = mapping.get(to_loc, to_loc)

    # Date Logic
    # Pass requested date directly; DB now handles fallback to templates
    mapped_date = date_str

    # 1. Get Schedules
    schedules_df = DB.get_schedules_by_route(from_loc, to_loc, t_type, mapped_date)
    
    live_env = get_live_env()


    # Detect if fallback occurred (mixed modes)
    if not schedules_df.empty:
        unique_modes = schedules_df['Transport_Type'].unique()
        if t_type not in unique_modes and len(unique_modes) > 0:
            flash(f"Requested mode '{t_type}' unavailable. Showing available alternatives.", "warning")
            # t_type = "Any"  # Keep user selection for UI consistency

    if schedules_df.empty:
        return render_template('index.html', error=f"No services found for this specific route on {date_str}. Try popular routes like Secunderabad to Miyapur.", live_env=live_env, travel_date=date_str)

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
    date_str = data.get('date', '')
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    t_type = data.get('type', 'Bus')
    
    mapping = {"Lb Nagar": "L.B. Nagar", "Hi-Tech City": "Hitech City"}
    from_loc = mapping.get(from_loc, from_loc)
    to_loc = mapping.get(to_loc, to_loc)

    mapped_date = date_str

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
    
    # Duration Logic: Synchronize with Engine
    scheduled_arrival_str = pred.get('scheduled_arrival', '10:00')
    predicted_arrival_str = pred.get('predicted_arrival', '10:00')
    
    try:
        arr_dt = datetime.strptime(f"{travel_date} {scheduled_arrival_str}", "%Y-%m-%d %H:%M")
        dur = int((arr_dt - base_dt).total_seconds() / 60)
        if dur <= 0: raise ValueError
    except:
        dur = 30 # absolute fallback
    
    # Stops logic
    stops = []
    raw_stops = svc_dict.get('Stops', '').split('|')
    now = datetime.now()
    try:
        chk_dt = datetime.strptime(travel_date, "%Y-%m-%d").date()
    except:
        chk_dt = now.date()
        
    is_today = (chk_dt == now.date())
    is_past = (chk_dt < now.date())
    is_future = (chk_dt > now.date())
    found_current = False
    
    for i, s_name in enumerate(raw_stops):
        # Precise offset distribution based on Trip Duration
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
        elif is_past:
             status = "Departed" if i < len(raw_stops)-1 else "Reached"
             is_passed = True
        
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
            "Sched_Reach": scheduled_arrival_str,
            "Reach_Time": predicted_arrival_str,
            "From_Location": svc_dict['From_Location'],
            "To_Location": svc_dict['To_Location'],
            "Transport_Type": svc_dict['Transport_Type'],
            "Is_Live": is_today and any(s['is_current'] or s['is_passed'] for s in stops) and not all(s['is_passed'] for s in stops)
        },
        "insights": pred,
        "stops": stops,
        "now_time": now.strftime('%H:%M:%S')
    }

@app.route('/track/<int:service_id>')
def track(service_id):
    travel_date = request.args.get('date', '')
    if not travel_date:
        travel_date = datetime.now().strftime("%Y-%m-%d")
    data = _get_tracking_data(service_id, travel_date)
    if not data:
        return redirect(url_for('index'))
    data['live_env'] = get_live_env()
    return render_template('schedule.html', **data)

@app.route('/api/track/<int:service_id>')
def api_track(service_id):
    travel_date = request.args.get('date', '')
    if not travel_date:
        travel_date = datetime.now().strftime("%Y-%m-%d")
    data = _get_tracking_data(service_id, travel_date)
    if not data:
        return {"error": "Not Found"}, 404
    return data


@app.route('/map')
def live_map():
    live_env = get_live_env()
    # Fetch dynamic locations from database to resolve NameError
    locations = DB.get_locations()
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
    live_env = get_live_env()
    return render_template('analytics.html', live_env=live_env)



if __name__ == '__main__':
    from src.database.db_config import init_db
    config.ensure_directories()
    init_db()
    app.run(debug=True, port=8000)
