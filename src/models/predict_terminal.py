import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config
from src.models.engine import ENGINE
from src.database.queries import TransportDB

def run_interactive():
    print("\n--- DEBUG: STARTING INTERACTIVE SESSION ---")
    # Ensure artifacts are ready
    if not config.XGBOOST_MODEL_PATH.exists():
        print("❌ Error: ML Model not found. Please run 'python main.py' first.")
        return

    db = TransportDB()
    print("\n" + "═"*70)
    print("🚀 HYDERTRAX: ELITE TRANSIT ANALYTICS (CLI VERSION)")
    print("═"*70)
    
    # User Inputs
    try:
        origin = input("📍 From (e.g. Secunderabad): ").strip().title()
        dest = input("📍 To   (e.g. Miyapur):      ").strip().title()
        
        date_input = input("📅 Date (YYYY-MM-DD) [Enter for Today]: ").strip()
        try:
            if date_input:
                datetime.strptime(date_input, '%Y-%m-%d') # Validate format
                date_str = date_input
            else:
                raise ValueError("Empty input")
        except ValueError:
            date_str = datetime.now().strftime("%Y-%m-%d")
            if date_input:
                print(f"⚠️ Invalid format '{date_input}'. Using today: {date_str}")
            
        t_mode = input("🚌 Mode (Bus/Metro/Train) [Bus]: ").strip()
        t_type = "Bus" if not t_mode else t_mode.title()
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
        return

    print(f"\n🔎 Scanning neural pathways for {date_str}...", flush=True)
    
    # Date Logic
    # Pass requested date directly
    mapped_date = date_str

    print(f"📡 Status: Fetching scheduling threads from vault...", flush=True)

    # Query Database
    schedules_df = db.get_schedules_by_route(origin, dest, t_type, mapped_date)
    
    if schedules_df.empty:
        print(f"❌ No matching {t_type} services found for {origin} -> {dest}.")
        print(f"💡 Tip: Verify location spelling. Available: {['Secunderabad', 'Miyapur', 'Koti', 'Ameerpet'][:4]}...")
        return

    print(f"🧠 Status: Running ML Inference on {len(schedules_df)} threads...", flush=True)

    # Process Batch logic
    try:
        schedules_raw = schedules_df.to_dict('records')
        processed_schedules = ENGINE.process_batch(schedules_raw, date_str)
    except Exception as e:
        print(f"❌ AI Engine Error: {e}")
        return

    print(f"\n📋 FOUND {len(processed_schedules)} SERVICES:")
    print(f"{'IDX':<5} | {'SERVICE ID':<18} | {'DEP TIME':<10} | {'PREDICTED ARRIVAL'}")
    print("-" * 70)
    
    for i, svc in enumerate(processed_schedules):
        pred = svc['prediction']
        print(f"{i+1:<5} | {svc.get('Service_ID', 'UNK'):<18} | {svc.get('Scheduled_Departure', '--:--'):<10} | {pred['predicted_arrival']}")
        
    try:
        user_choice = input("\n🔢 Index to Track (or Enter to quit): ").strip()
        if not user_choice: return
        sel_idx = int(user_choice) - 1
        if sel_idx < 0 or sel_idx >= len(processed_schedules):
            print("❌ Invalid selection.")
            return
    except ValueError:
        return
        
    selected_service = processed_schedules[sel_idx]
    result = selected_service['prediction']
    
    print(f"\n⚡ Synchronizing telemetry for {selected_service.get('Service_ID')}...")
    
    sch_dep = selected_service.get('Scheduled_Departure')
    try:
        dep_time_obj = datetime.strptime(f"{date_str} {sch_dep}", "%Y-%m-%d %H:%M")
    except:
        dep_time_obj = datetime.now()
    
    # Timeline details
    dist = selected_service.get('Distance_KM', config.DEFAULT_DISTANCE_KM)
    spd = config.SPEED_ESTIMATES.get(t_type, 30)
    base_dur = int((dist / spd) * 60)
    
    print("\n" + "═"*70)
    print(f"🎯 JOURNEY INSIGHTS")
    print("═"*70)
    print(f"🚦 Predicted Status:   {result['status_text']}")
    print(f"🔮 Estimated Delay:   +{result['predicted_delay']} Min")
    print(f"📝 Contributing Factor: {result['reason']}")
    print(f"📡 Risk Level:         {result['risk_level']}")
    print(f"💡 Recommendation:     {result['recommendation']}")
    print("-" * 70)
    print(f"🕒 Scheduled Dep:      {sch_dep}")
    print(f"🕒 Predicted Arr:      {result['predicted_arrival']}")
    print("═"*70)
    
    # Live Stop Tracking
    now = datetime.now()
    stops_raw = selected_service.get('Stops', '').split('|')
    total_time = base_dur + result.get('predicted_delay', 0)
    time_per_stop = total_time / max(1, (len(stops_raw) - 1))
    
    print(f"\n📍 NODE TRACKING (System Time: {now.strftime('%H:%M:%S')})")
    print(f"{'STATION NAME':<25} | {'EST. TIME':<10} | {'TELEMETRY STATUS'}")
    print("-" * 70)
    
    found_current = False
    is_today = (date_str == now.strftime("%Y-%m-%d"))
    
    for i, stop in enumerate(stops_raw):
        stop_time = dep_time_obj + timedelta(minutes=int(i * time_per_stop))
        stop_str = stop_time.strftime('%H:%M')
        
        status = "○ UPCOMING"
        if is_today:
            if now > stop_time + timedelta(minutes=2):
                status = "✓ PASSED"
            elif now >= stop_time - timedelta(minutes=2):
                status = "● AT STATION"
                found_current = True
            elif not found_current and i > 0:
                prev_stop_time = dep_time_obj + timedelta(minutes=int((i-1) * time_per_stop))
                if now > prev_stop_time:
                    status = "▶ IN TRANSIT"
                    found_current = True
            
        print(f"{stop:<25} | {stop_str:<10} | {status}")

if __name__ == "__main__":
    while True:
        try:
            run_interactive()
            cont = input("\n🔄 Analyze another route? (y/n) [n]: ").lower().strip()
            if cont != 'y': break
        except KeyboardInterrupt:
            break
    print("\n👋 System disconnected. Travel safe!")
