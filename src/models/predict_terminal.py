"""
predict_terminal.py — CLI Prediction Interface
================================================
Interactive terminal UI for searching routes and viewing predictions.
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config
from src.models.engine import ENGINE
from src.database.queries import TransportDB


def run_interactive():
    """Run one interactive prediction session."""
    if not config.XGBOOST_MODEL_PATH.exists():
        print("Error: ML Model not found. Run 'python main.py' first.")
        return

    db = TransportDB()

    print(f"\n{'='*60}")
    print("  HYDERTRAX — Terminal Prediction")
    print(f"{'='*60}")

    # User inputs
    try:
        origin = input("From (e.g. Secunderabad): ").strip().title()
        dest = input("To   (e.g. Miyapur):      ").strip().title()

        date_input = input("Date (YYYY-MM-DD) [today]: ").strip()
        try:
            if date_input:
                datetime.strptime(date_input, '%Y-%m-%d')
                date_str = date_input
            else:
                raise ValueError
        except ValueError:
            date_str = config.get_now_ist().strftime("%Y-%m-%d")
            if date_input:
                print(f"  Invalid format. Using today: {date_str}")

        t_mode = input("Mode (Bus/Metro/Train/All) [All]: ").strip().lower()
        t_type = t_mode.title() if t_mode and t_mode != 'all' else 'All'
    except KeyboardInterrupt:
        print("\nExiting...")
        return

    print(f"\nSearching for {date_str}...")

    # Query database
    if t_type == 'All':
        dfs = []
        for m in ['Bus', 'Metro', 'Train']:
            df = db.get_schedules_by_route(origin, dest, m, date_str)
            if not df.empty:
                dfs.append(df)
        schedules_df = pd.concat(dfs) if dfs else pd.DataFrame()
    else:
        schedules_df = db.get_schedules_by_route(origin, dest, t_type, date_str)

    if schedules_df.empty:
        print(f"\nNo {t_type} services found for {origin} -> {dest} on {date_str}.")
        try:
            locs = db.get_locations()
            if locs:
                print(f"Available locations: {', '.join(locs[:10])}...")
        except Exception:
            pass
        return

    # Run predictions
    print(f"Running predictions on {len(schedules_df)} services...")
    try:
        processed = ENGINE.process_batch(schedules_df.to_dict('records'), date_str)
    except Exception as e:
        print(f"Prediction error: {e}")
        return

    # Display results
    print(f"\n{'IDX':<5} | {'MODE':<8} | {'SERVICE ID':<18} | {'DEP':<8} | {'PREDICTED ARR'}")
    print("-" * 70)
    for i, svc in enumerate(processed):
        pred = svc['prediction']
        print(f"{i+1:<5} | {svc.get('Transport_Type', '?'):<8} | "
              f"{svc.get('Service_ID', '?'):<18} | "
              f"{svc.get('Scheduled_Departure', '--:--'):<8} | "
              f"{pred['predicted_arrival']}")

    # Select service for detail
    try:
        choice = input("\nIndex to view details (or Enter to quit): ").strip()
        if not choice:
            return
        idx = int(choice) - 1
        if idx < 0 or idx >= len(processed):
            print("Invalid selection.")
            return
    except (ValueError, KeyboardInterrupt):
        return

    selected = processed[idx]
    result = selected['prediction']

    # Detail view
    sch_dep = selected.get('Scheduled_Departure', '--:--')
    try:
        dep_dt = datetime.strptime(f"{date_str} {sch_dep}", "%Y-%m-%d %H:%M")
    except ValueError:
        dep_dt = datetime.now()

    sch_arr = result.get('scheduled_arrival', '--:--')
    try:
        arr_dt = datetime.strptime(f"{date_str} {sch_arr}", "%Y-%m-%d %H:%M")
        base_dur = int((arr_dt - dep_dt).total_seconds() / 60)
    except (ValueError, TypeError):
        dist = selected.get('Distance_KM', config.DEFAULT_DISTANCE_KM)
        spd = config.SPEED_ESTIMATES.get(selected.get('Transport_Type', 'Bus'), 30)
        base_dur = int((dist / spd) * 60)

    print(f"\n{'='*60}")
    print(f"  JOURNEY INSIGHTS — {selected.get('Service_ID')}")
    print(f"{'='*60}")
    print(f"Status           : {result.get('status_text')}")
    print(f"Predicted Delay  : +{result.get('predicted_delay', 0)} min")
    print(f"Delay Reason     : {result.get('reason', 'N/A')}")
    print(f"Risk Level       : {result.get('risk_level')}")
    print(f"Recommendation   : {result.get('recommendation')}")
    print(f"-" * 60)
    print(f"Scheduled Dep    : {sch_dep}")
    print(f"Scheduled Arr    : {result.get('scheduled_arrival')}")
    print(f"Predicted Arr    : {result.get('predicted_arrival')}")
    print(f"{'='*60}")

    # Stop tracking
    now = config.get_now_ist()
    stops = selected.get('Stops', '').split('|')
    total_time = base_dur + result.get('predicted_delay', 0)
    time_per_stop = total_time / max(1, len(stops) - 1)

    is_today = (date_str == now.strftime("%Y-%m-%d"))
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    is_past = target_date < now.date()
    is_future = target_date > now.date()

    print(f"\nStop Tracking ({now.strftime('%H:%M:%S')} IST)")
    print(f"{'STOP':<25} | {'EST TIME':<10} | {'STATUS'}")
    print("-" * 55)

    for i, stop in enumerate(stops):
        stop_time = dep_dt + timedelta(minutes=int(i * time_per_stop))

        if is_past:
            status = "REACHED" if i == len(stops) - 1 else "DEPARTED"
        elif is_future:
            status = "UPCOMING"
        elif is_today:
            if now > stop_time + timedelta(minutes=2):
                status = "PASSED"
            elif now >= stop_time - timedelta(minutes=2):
                status = "AT STATION"
            else:
                status = "UPCOMING"
        else:
            status = "UPCOMING"

        print(f"{stop:<25} | {stop_time.strftime('%H:%M'):<10} | {status}")


if __name__ == "__main__":
    while True:
        try:
            run_interactive()
            if input("\nAnother route? (y/n) [n]: ").lower().strip() != 'y':
                break
        except KeyboardInterrupt:
            break
    print("\nGoodbye!")
