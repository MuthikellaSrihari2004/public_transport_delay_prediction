import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import random

def generate_hyderabad_data():
    print("Initializing Enhanced Data Generation for Hyderabad Transport with Real Stop Names...")
    
    # Configuration
    hubs = [
        "Secunderabad", "Koti", "Mehdipatnam", "Charminar", "Ameerpet",
        "Hitech City", "Gachibowli", "Miyapur", "Uppal", "L.B. Nagar"
    ]
    
    # Pool of realistic Hyderabad intermediate stop names
    intermediate_stop_pool = [
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
    delay_reasons = ["Traffic Congestion", "Technical Glitch", "Weather Conditions", "Public Rally", "Signal Delay", "Accident"]
    
    # 1 year range (2025)
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_list = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    
    # Define Routes (Vice-versa)
    routes = []
    for i in range(len(hubs)):
        for j in range(i + 1, len(hubs)):
            from_loc = hubs[i]
            to_loc = hubs[j]
            
            # Select 8 unique random stops from pool for this specific route
            selected_stops = random.sample(intermediate_stop_pool, 8)
            # Add start and end
            full_stops_forward = [from_loc] + selected_stops + [to_loc]
            full_stops_backward = full_stops_forward[::-1]
            
            dist = round(random.uniform(15.0, 45.0), 2)
            
            routes.append({'from': from_loc, 'to': to_loc, 'id': f"RT_{i}{j}", 'stops': "|".join(full_stops_forward), 'dist': dist})
            routes.append({'from': to_loc, 'to': from_loc, 'id': f"RT_{j}{i}", 'stops': "|".join(full_stops_backward), 'dist': dist})

    final_data = []

    # Holiday list simulation
    holidays = ["2024-01-01", "2024-01-14", "2024-01-15", "2024-01-26", "2024-03-25", "2024-04-11",
                "2024-08-15", "2024-10-02", "2024-11-01", "2024-12-25",
                "2025-01-01", "2025-01-14", "2025-01-15", "2025-01-26", "2025-08-15", "2025-10-02", "2025-12-25"]

    # We will iterate by Transport Type first as requested
    for t_type in transport_types:
        print(f"Generating data for {t_type}...")
        for current_date in date_list:
            date_str = current_date.strftime('%Y-%m-%d')
            is_holiday = 1 if date_str in holidays or current_date.weekday() >= 5 else 0
            
            # Daily environmental factors
            daily_weather = random.choice(weather_types)
            temp = round(random.uniform(20.0, 42.0), 1)
            humidity = random.randint(30, 90)
            is_event = 1 if random.random() < 0.08 else 0

            for route in routes:
                # 30-minute interval from 05:00 to 23:30 (approx 38 services)
                for s_idx in range(38):
                    start_minutes = 300 + (s_idx * 30)
                    sched_dep_dt = current_date + timedelta(minutes=start_minutes)
                    
                    if sched_dep_dt.hour >= 24 or (sched_dep_dt.day != current_date.day): 
                        continue

                    hour = sched_dep_dt.hour
                    is_peak = 1 if (8 <= hour <= 11) or (17 <= hour <= 20) else 0
                    
                    # Traffic & Delay Logic
                    traffic_density = "Low"
                    if is_peak:
                        traffic_density = random.choice(["High", "High", "Medium"])
                    elif is_holiday:
                        traffic_density = "Low"
                    else:
                        traffic_density = random.choice(["Low", "Medium"])

                    # Speed: Bus 25km/h, Metro 40km/h, Train 50km/h
                    avg_speed = 25 if t_type == "Bus" else 40 if t_type == "Metro" else 50
                    duration_mins = int((route['dist'] / avg_speed) * 60)
                    sched_arr_dt = sched_dep_dt + timedelta(minutes=duration_mins)

                    # Target distribution: 25% On-time, 55% Minor, 20% Major
                    rand_p = random.random()
                    delay = 0
                    reason = "None"
                    
                    if rand_p < 0.25: # On-time
                        delay = 0
                    elif rand_p < 0.80: # Minor (1-15 mins)
                        delay = random.randint(1, 15)
                        reason = random.choice(delay_reasons)
                    else: # Major (15-120 mins)
                        if is_peak or daily_weather == "Rainy" or is_event:
                            delay = random.randint(30, 120)
                        else:
                            delay = random.randint(16, 45)
                        reason = random.choice(delay_reasons)

                    # Probability of Missing Values (NULL/None) - ~2%
                    act_dep_dt = sched_dep_dt + timedelta(minutes=random.randint(-2, 5))
                    act_arr_dt = sched_arr_dt + timedelta(minutes=delay)
                    
                    # Formatting strings with potential nulls
                    act_dep_str = act_dep_dt.strftime('%H:%M')
                    act_arr_str = act_arr_dt.strftime('%H:%M')
                    weather_val = daily_weather
                    reason_val = reason

                    if random.random() < 0.02: act_dep_str = None
                    if random.random() < 0.02: act_arr_str = ""
                    if random.random() < 0.05: reason_val = np.nan
                    if random.random() < 0.01: weather_val = None

                    passenger_load = random.randint(40, 100) if is_peak else random.randint(10, 60)

                    final_data.append({
                        'Date': date_str,
                        'Transport_Type': t_type,
                        'Route_ID': f"{t_type[0]}_{route['id']}",
                        'Service_ID': f"SVC_{t_type[0]}_{route['id']}_{s_idx:02d}",
                        'From_Location': route['from'],
                        'To_Location': route['to'],
                        'Stops': route['stops'],
                        'Scheduled_Departure': sched_dep_dt.strftime('%H:%M'),
                        'Scheduled_Arrival': sched_arr_dt.strftime('%H:%M'),
                        'Actual_Departure': act_dep_str,
                        'Actual_Arrival': act_arr_str,
                        'Delay_Minutes': delay,
                        'Delay_Reason': reason_val,
                        'Weather': weather_val,
                        'Is_Holiday': is_holiday,
                        'Is_Peak_Hour': is_peak,
                        'Event_Scheduled': is_event,
                        'Traffic_Density': traffic_density,
                        'Temperature_C': temp,
                        'Humidity_Pct': humidity,
                        'Passenger_Load': passenger_load,
                        'Distance_KM': route['dist']
                    })

    df = pd.DataFrame(final_data)
    os.makedirs('data/raw', exist_ok=True)
    output_file = 'data/raw/hyderabad_transport_raw.csv'
    df.to_csv(output_file, index=False)
    
    print(f"Dataset generated with {len(df)} rows.")
    print(f"Saved to: {output_file}")
    print("\nSample Stops Check:")
    print(df['Stops'].iloc[0])

if __name__ == "__main__":
    generate_hyderabad_data()
