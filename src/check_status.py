import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from src.models.engine import ENGINE

def check_system_status():
    print("="*60)
    print("      REALTIME SYSTEM STATUS CHECK (BASED ON SYSTEM TIME)")
    print("="*60)
    
    # 1. System Time
    now = datetime.now()
    print(f"[*] SYSTEM TIME     : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] HOUR            : {now.hour}")
    print("-" * 60)
    
    # 2. Weather
    print("[*] CHECKING WEATHER...")
    weather = ENGINE.get_realtime_weather()
    print(f"    - Description   : {weather['description']}")
    print(f"    - Temperature   : {weather['temp']}°C")
    print(f"    - Humidity      : {weather['humidity']}%")
    print(f"    - Source        : {weather['source']}")
    print("-" * 60)
    
    # 3. Events & Holidays
    print("[*] CHECKING EVENTS & HOLIDAYS...")
    date_str = now.strftime("%Y-%m-%d")
    holiday = ENGINE._check_holidays(date_str)
    event_flag = ENGINE._check_events(date_str)
    
    print(f"    - Date          : {date_str}")
    print(f"    - Holiday       : {holiday if holiday else 'None'}")
    print(f"    - Major Event   : {'Yes' if event_flag else 'No'}")
    print("-" * 60)
    
    # 4. Traffic & Peak Hours
    print("[*] CHECKING TRAFFIC & CONTEXT...")
    is_peak = (8 <= now.hour <= 11 or 17 <= now.hour <= 20)
    traffic = ENGINE._get_traffic(now.hour, weather['is_rainy'], event_flag)
    
    print(f"    - Peak Hour?    : {'YES' if is_peak else 'NO'} (Morning: 8-11, Evening: 17-20)")
    print(f"    - Traffic Level : {traffic}")
    print("="*60)

if __name__ == "__main__":
    check_system_status()
