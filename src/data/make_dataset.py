"""
make_dataset.py — Synthetic Data Generator
============================================
Generates realistic Hyderabad transport delay data with proper
route networks, intermediate stops, and delay distributions.
"""

import pandas as pd
import numpy as np
import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config


def generate_hyderabad_data():
    """Generate synthetic transport data for Hyderabad routes."""
    print("Generating transport data for Hyderabad...")

    # Hub locations
    hubs = [
        "Secunderabad", "Koti", "Mehdipatnam", "Charminar", "Ameerpet",
        "Hitech City", "Gachibowli", "Miyapur", "Uppal", "L.B. Nagar"
    ]

    # Intermediate stops (realistic Hyderabad stop names)
    stop_pool = [
        "Paradise", "Patny", "Tarnaka", "Habsiguda", "Mettuguda", "Begumpet",
        "Punjagutta", "Banjara Hills", "Jubilee Hills Checkpost", "Madhapur",
        "Kondapur", "Kothaguda", "Hafeezpet", "JNTU", "KPHB", "Erragadda",
        "SR Nagar", "Lakdikapul", "Khairatabad", "Nampally", "Assembly",
        "Sultan Bazar", "Malakpet", "Dilsukhnagar", "Chaitanyapuri", "Nagole",
        "RTC X Roads", "Musheerabad", "Gandhi Hospital", "Chikkadpally",
        "Narayanguda", "Abids", "Nayapul", "Madina", "Attapur", "Rethibowli",
        "Tolichowki", "Nanal Nagar", "DLF", "Financial District", "IIIT Junction"
    ]

    transport_types = ["Bus", "Metro", "Train"]
    weather_types = ["Clear", "Rainy", "Foggy", "Overcast", "Cloudy"]
    delay_reasons = ["Traffic Congestion", "Technical Glitch", "Weather Conditions",
                     "Public Rally", "Signal Delay", "Accident"]

    # Date range: Jan–Mar 2026
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 3, 31)
    date_list = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

    # Holiday dates
    holidays = {"2024-01-01", "2024-01-14", "2024-01-15", "2024-01-26", "2024-03-25",
                "2024-04-11", "2024-08-15", "2024-10-02", "2024-11-01", "2024-12-25",
                "2025-01-01", "2025-01-14", "2025-01-15", "2025-01-26",
                "2025-08-15", "2025-10-02", "2025-12-25"}

    # Build routes (both directions)
    routes = []
    for i in range(len(hubs)):
        for j in range(i + 1, len(hubs)):
            stops = random.sample(stop_pool, 8)
            forward = [hubs[i]] + stops + [hubs[j]]
            backward = forward[::-1]
            dist = round(random.uniform(15.0, 45.0), 2)

            routes.append({'from': hubs[i], 'to': hubs[j], 'id': f"RT_{i}{j}",
                           'stops': "|".join(forward), 'dist': dist})
            routes.append({'from': hubs[j], 'to': hubs[i], 'id': f"RT_{j}{i}",
                           'stops': "|".join(backward), 'dist': dist})

    # Generate records
    records = []
    speed_map = {"Bus": 25, "Metro": 40, "Train": 50}

    for t_type in transport_types:
        print(f"  Generating {t_type} data...")
        for date in date_list:
            date_str = date.strftime('%Y-%m-%d')
            is_holiday = 1 if date_str in holidays or date.weekday() >= 5 else 0
            weather = random.choice(weather_types)
            temp = round(random.uniform(20.0, 42.0), 1)
            humidity = random.randint(30, 90)
            is_event = 1 if random.random() < 0.08 else 0

            for route in routes:
                for slot in range(38):  # 05:00–23:30 in 30-min slots
                    dep_dt = date + timedelta(minutes=300 + slot * 30)
                    if dep_dt.day != date.day:
                        continue

                    hour = dep_dt.hour
                    is_peak = 1 if (8 <= hour <= 11 or 17 <= hour <= 20) else 0

                    # Traffic density
                    if is_peak:
                        traffic = random.choice(["High", "High", "Medium"])
                    elif is_holiday:
                        traffic = "Low"
                    else:
                        traffic = random.choice(["Low", "Medium"])

                    # Duration and arrival
                    duration = int((route['dist'] / speed_map[t_type]) * 60)
                    arr_dt = dep_dt + timedelta(minutes=duration)

                    # Delay generation (25% on-time, 55% minor, 20% major)
                    rand_val = random.random()
                    if rand_val < 0.25:
                        delay, reason = 0, "None"
                    elif rand_val < 0.80:
                        delay = random.randint(1, 15)
                        reason = random.choice(delay_reasons)
                    else:
                        delay = random.randint(30, 120) if (is_peak or weather == "Rainy" or is_event) else random.randint(16, 45)
                        reason = random.choice(delay_reasons)

                    # Actual times (with small variance)
                    act_dep = (dep_dt + timedelta(minutes=random.randint(-2, 5))).strftime('%H:%M')
                    act_arr = (arr_dt + timedelta(minutes=delay)).strftime('%H:%M')

                    # Introduce ~2% missing values
                    if random.random() < 0.02: act_dep = None
                    if random.random() < 0.02: act_arr = ""
                    if random.random() < 0.05: reason = np.nan
                    if random.random() < 0.01: weather = None

                    load = random.randint(40, 100) if is_peak else random.randint(10, 60)

                    records.append({
                        'Date': date_str,
                        'Transport_Type': t_type,
                        'Route_ID': f"{t_type[0]}_{route['id']}",
                        'Service_ID': f"SVC_{t_type[0]}_{route['id']}_{slot:02d}",
                        'From_Location': route['from'],
                        'To_Location': route['to'],
                        'Stops': route['stops'],
                        'Scheduled_Departure': dep_dt.strftime('%H:%M'),
                        'Scheduled_Arrival': arr_dt.strftime('%H:%M'),
                        'Actual_Departure': act_dep,
                        'Actual_Arrival': act_arr,
                        'Delay_Minutes': delay,
                        'Delay_Reason': reason,
                        'Weather': weather,
                        'Is_Holiday': is_holiday,
                        'Is_Peak_Hour': is_peak,
                        'Event_Scheduled': is_event,
                        'Traffic_Density': traffic,
                        'Temperature_C': temp,
                        'Humidity_Pct': humidity,
                        'Passenger_Load': load,
                        'Distance_KM': route['dist']
                    })

    df = pd.DataFrame(records)
    output_path = str(config.RAW_DATA_FILE)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Generated {len(df):,} records -> {output_path}")
    return df


if __name__ == "__main__":
    generate_hyderabad_data()
