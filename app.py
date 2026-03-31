"""
app.py — Flask Web Application
================================
Routes for the HyderTrax transport delay prediction web interface.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

import config
config.ensure_directories()

from src.database.queries import TransportDB
from src.models.engine import ENGINE

# ── App Setup ───────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

DB = TransportDB()

# Location name aliases (handles common user input variations)
LOCATION_ALIASES = {"Lb Nagar": "L.B. Nagar", "Hi-Tech City": "Hitech City"}


def _normalize_location(name):
    """Apply location aliases to user input."""
    return LOCATION_ALIASES.get(name, name)


def _get_live_env():
    """Build real-time environment context for templates."""
    weather = ENGINE.get_realtime_weather()
    now = config.get_now_ist()
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


# ── Page Routes ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html',
                           live_env=_get_live_env(),
                           today_date=config.get_now_ist().strftime("%Y-%m-%d"))


@app.route('/predict')
def prediction_page():
    return render_template('prediction.html',
                           today_date=config.get_now_ist().strftime("%Y-%m-%d"),
                           live_env=_get_live_env())


@app.route('/map')
def live_map():
    return render_template('map.html', live_env=_get_live_env())


@app.route('/analytics')
def analytics():
    return render_template('analytics.html', live_env=_get_live_env())


# ── Search Routes ───────────────────────────────────────────────────────

@app.route('/search', methods=['POST'])
def search():
    """Form-based search — returns rendered HTML page."""
    from_loc = _normalize_location(request.form.get('from_location', '').strip().title())
    to_loc = _normalize_location(request.form.get('to_location', '').strip().title())
    date_str = request.form.get('travel_date', '') or config.get_now_ist().strftime("%Y-%m-%d")
    t_type = request.form.get('transport_type', 'Bus')

    schedules_df = DB.get_schedules_by_route(from_loc, to_loc, t_type, date_str)
    live_env = _get_live_env()

    # Warn if requested mode was unavailable but alternatives exist
    if not schedules_df.empty:
        unique_modes = schedules_df['Transport_Type'].unique()
        if t_type not in unique_modes:
            flash(f"Requested mode '{t_type}' unavailable. Showing alternatives.", "warning")

    if schedules_df.empty:
        return render_template('index.html',
                               error=f"No services found for this route on {date_str}.",
                               live_env=live_env, travel_date=date_str)

    schedules = ENGINE.process_batch(schedules_df.to_dict('records'), date_str)

    return render_template('index.html',
                           schedules=schedules,
                           from_loc=from_loc, to_loc=to_loc,
                           travel_date=date_str, t_type=t_type,
                           live_env=live_env)


@app.route('/api/search', methods=['POST'])
def api_search():
    """JSON API search — returns prediction data."""
    data = request.json
    from_loc = _normalize_location(data.get('from', '').strip().title())
    to_loc = _normalize_location(data.get('to', '').strip().title())
    date_str = data.get('date', '') or config.get_now_ist().strftime("%Y-%m-%d")
    t_type = data.get('type', 'Bus')

    schedules_df = DB.get_schedules_by_route(from_loc, to_loc, t_type, date_str)

    if schedules_df.empty:
        return {"error": "No services found"}, 404

    schedules = ENGINE.process_batch(schedules_df.to_dict('records'), date_str)

    return {
        "schedules": schedules,
        "representative_insight": schedules[0]['prediction']
    }


# ── Tracking Routes ─────────────────────────────────────────────────────

def _get_tracking_data(service_id, travel_date):
    """Build complete tracking data for a single service."""
    # Fetch service from database
    try:
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM schedules WHERE id = ?", (service_id,))
        service = cursor.fetchone()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
        return None

    if not service:
        return None

    svc = dict(service)
    pred = ENGINE.predict_one(svc, travel_date)

    # Parse departure time
    sch_dep = svc['Scheduled_Departure']
    try:
        base_dt = datetime.strptime(f"{travel_date} {sch_dep}", "%Y-%m-%d %H:%M")
    except ValueError:
        base_dt = config.get_now_ist()

    # Calculate journey duration
    scheduled_arrival = pred.get('scheduled_arrival', '10:00')
    predicted_arrival = pred.get('predicted_arrival', '10:00')

    try:
        arr_dt = datetime.strptime(f"{travel_date} {scheduled_arrival}", "%Y-%m-%d %H:%M")
        duration = int((arr_dt - base_dt).total_seconds() / 60)
        if duration <= 0:
            raise ValueError
    except (ValueError, TypeError):
        duration = 30

    # Build stop timeline
    now = config.get_now_ist()
    try:
        check_date = datetime.strptime(travel_date, "%Y-%m-%d").date()
    except ValueError:
        check_date = now.date()

    is_today = (check_date == now.date())
    is_past = (check_date < now.date())
    is_future = (check_date > now.date())

    raw_stops = svc.get('Stops', '').split('|')
    num_stops = max(1, len(raw_stops) - 1)

    # First pass: compute estimated times for each stop
    stop_data = []
    for i, stop_name in enumerate(raw_stops):
        sched_offset = int(i * (duration / num_stops))
        sched_time = base_dt + timedelta(minutes=sched_offset)
        delay_at_stop = int(i * (pred['predicted_delay'] / num_stops))
        est_time = base_dt + timedelta(minutes=sched_offset + delay_at_stop)
        stop_data.append({"name": stop_name, "sched_time": sched_time, "est_time": est_time})

    # Second pass: determine active stop index
    active_index = -1
    if is_today:
        last_passed = -1
        for i, sd in enumerate(stop_data):
            if now >= sd['est_time']:
                last_passed = i
        if last_passed == -1:
            active_index = 0
        elif last_passed == len(stop_data) - 1:
            active_index = last_passed
        else:
            active_index = last_passed + 1
    elif is_future:
        active_index = 0

    # Third pass: build final stop list with status
    stops = []
    for i, sd in enumerate(stop_data):
        is_current = (i == active_index)
        is_passed = False

        if is_today:
            if i < active_index:
                status, is_passed = "Departed", True
            elif is_current:
                status = "At Station"
            else:
                status = "Upcoming"
        elif is_past:
            status = "Reached" if i == len(stop_data) - 1 else "Departed"
            is_passed = True
        elif is_future:
            status = "Boarding" if is_current else "Upcoming"
        else:
            status = "Upcoming"

        stops.append({
            "name": sd['name'],
            "est": sd['est_time'].strftime("%H:%M"),
            "sched": sd['sched_time'].strftime("%H:%M"),
            "is_passed": is_passed,
            "is_current": is_current,
            "status": status
        })

    return {
        "service": svc,
        "info": {
            "Service_ID": svc['Service_ID'],
            "Start_Time": base_dt.strftime("%H:%M"),
            "Sched_Reach": scheduled_arrival,
            "Reach_Time": predicted_arrival,
            "From_Location": svc['From_Location'],
            "To_Location": svc['To_Location'],
            "Transport_Type": svc['Transport_Type'],
            "Is_Live": is_today and any(s['is_current'] or s['is_passed'] for s in stops)
                       and not all(s['is_passed'] for s in stops)
        },
        "insights": pred,
        "stops": stops,
        "now_time": now.strftime('%H:%M:%S')
    }


@app.route('/track/<int:service_id>')
def track(service_id):
    travel_date = request.args.get('date', '') or config.get_now_ist().strftime("%Y-%m-%d")
    data = _get_tracking_data(service_id, travel_date)
    if not data:
        return redirect(url_for('index'))
    data['live_env'] = _get_live_env()
    return render_template('schedule.html', **data)


@app.route('/api/track/<int:service_id>')
def api_track(service_id):
    travel_date = request.args.get('date', '') or config.get_now_ist().strftime("%Y-%m-%d")
    data = _get_tracking_data(service_id, travel_date)
    if not data:
        return {"error": "Not Found"}, 404
    return data


# ── Utility API Routes ──────────────────────────────────────────────────

@app.route('/api/route', methods=['POST'])
def api_route_details():
    data = request.json
    from_loc = _normalize_location(data.get('from', '').strip())
    to_loc = _normalize_location(data.get('to', '').strip())
    mode = data.get('mode')

    details = DB.get_route_details(from_loc, to_loc, mode)
    if not details:
        details = DB.get_route_details(from_loc.title(), to_loc.title(), mode)
    if not details:
        return {"error": "Route not found."}, 404

    return details


@app.route('/api/locations')
def api_locations():
    """Return all unique locations for autocomplete."""
    return jsonify(DB.get_locations())


# ── Entry Point ─────────────────────────────────────────────────────────

if __name__ == '__main__':
    from src.database.db_config import init_db
    init_db()
    app.run(debug=True, port=config.FLASK_PORT)
