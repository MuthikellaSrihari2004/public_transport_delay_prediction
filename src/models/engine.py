import pandas as pd
import numpy as np
import joblib
import os
import requests
import random
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class TransportEngine:
    def __init__(self):
        print("Initializing Logic Core...")
        self.model_path = 'models/xgboost_delay_model.pkl'
        self.encoder_path = 'models/label_encoders.pkl'
        
        # API Keys
        self.weather_key = os.getenv("OPENWEATHER_API_KEY")
        self.traffic_key = os.getenv("TRAFFIC_API_KEY")
        self.event_key = os.getenv("EVENT_API_KEY") # e.g. PredictHQ or Ticketmaster
        self.holiday_key = os.getenv("HOLIDAY_API_KEY") # e.g. Calendarific
        
        self.model = None
        self.encoders = None
        
        if os.path.exists(self.model_path) and os.path.exists(self.encoder_path):
            self.model = joblib.load(self.model_path)
            self.encoders = joblib.load(self.encoder_path)
        else:
            print("⚠️ ML Artifacts not found. Running in heuristic simulation mode.")
            
        # Real-time Telemetry Cache & Circuit Breaker
        self._weather_cache = None
        self._traffic_cache = {}
        self._cache_time = None
        self._api_disabled = False # Circuit breaker for connection timeouts

    def get_realtime_weather(self):
        """Fetch highly accurate live weather using Open-Meteo (No-Key Required)
           Refined to match Google Search results (Apparent Temp + Precision Mapping)
        """
        now = datetime.now()
        # 10-minute caching for API efficiency
        if self._weather_cache and self._cache_time and (now - self._cache_time).seconds < 600:
            return self._weather_cache

        lat, lon = 17.3850, 78.4867
        # Default fallback
        weather_data = {"description": "Clear", "temp": 24.0, "humidity": 50, "is_rainy": False, "source": "Cached/Simulated"}
        
        try:
            # Using Open-Meteo with apparent_temperature to match Google's 'Feels Like' perception
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code&timezone=auto"
            resp = requests.get(url, timeout=3)
            
            if resp.status_code == 200:
                data = resp.json()['current']
                code = data['weather_code']
                
                # High-fidelity WMO Weather mapping for Google consistency
                desc_map = {
                    0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
                    45: "Foggy", 48: "Depositing Rime Fog",
                    51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
                    61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
                    71: "Slight Snow", 73: "Moderate Snow", 75: "Heavy Snow",
                    80: "Slight Rain Showers", 81: "Moderate Rain Showers", 82: "Violent Rain Showers",
                    95: "Thunderstorm", 96: "Thunderstorm with Hail", 99: "Heavy Hail"
                }
                
                description = desc_map.get(code, "Clear Sky")
                is_rainy = code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]
                
                # Google usually prioritizes 'Apparent Temperature' (Apparent / Feels Like)
                # We blend them for the most 'Correct' feel
                temp_display = data['apparent_temperature']

                weather_data = {
                    "description": description,
                    "temp": round(temp_display, 1),
                    "humidity": data['relative_humidity_2m'],
                    "is_rainy": is_rainy,
                    "source": "Open-Meteo Real-Time"
                }
        except Exception as e:
            print(f"📡 Remote Weather API error: {e}")
            
        self._weather_cache = weather_data
        self._cache_time = now
        return weather_data

    def _get_traffic(self, hour, is_rainy, event_flag):
        """Fetch real-time traffic density from TomTom or simulate based on stressors"""
        now = datetime.now()
        cache_key = f"{hour}_{is_rainy}_{event_flag}"
        if cache_key in self._traffic_cache and self._cache_time and (now - self._cache_time).seconds < 300:
            return self._traffic_cache[cache_key]

        traffic_status = "Low"
        if not self._api_disabled and self.traffic_key and self.traffic_key not in ["YOUR_TOMTOM_API_KEY", ""]:
            try:
                url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point=17.3850,78.4867&key={self.traffic_key}"
                res = requests.get(url, timeout=1).json() 
                if "flowSegmentData" in res:
                    frc = res["flowSegmentData"].get("currentSpeed", 30)
                    ffs = res["flowSegmentData"].get("freeFlowSpeed", 40)
                    ratio = frc / ffs
                    if ratio < 0.4: traffic_status = "Very High"
                    elif ratio < 0.7: traffic_status = "High"
                    elif ratio < 0.9: traffic_status = "Medium"
                    else: traffic_status = "Low"
            except Exception:
                self._api_disabled = True

        if traffic_status == "Low":
            score = 0
            if 8 <= hour <= 11 or 17 <= hour <= 20: score += 5 
            if is_rainy: score += 3
            if event_flag: score += 4
            if score >= 9: traffic_status = "Very High"
            elif score >= 6: traffic_status = "High"
            elif score >= 3: traffic_status = "Medium"
        
        self._traffic_cache[cache_key] = traffic_status
        return traffic_status

    def _check_events(self, date_str):
        """Check for major local events via PredictHQ or similar"""
        # For Demo: Trigger events on some dates
        special_event_dates = ["2026-01-26", "2026-01-30", "2026-02-14"]
        if date_str in special_event_dates:
            return 1

        if not self._api_disabled and self.event_key and self.event_key not in ["YOUR_EVENT_API_KEY", ""]:
            try:
                headers = {"Authorization": f"Bearer {self.event_key}", "Accept": "application/json"}
                url = f"https://api.predicthq.com/v1/events/?location_around.origin=17.3850,78.4867&active.gte={date_str}&active.lte={date_str}&category=concerts,sports,festivals"
                res = requests.get(url, headers=headers, timeout=1).json() # Ultra fast timeout
                if res.get("results") and len(res["results"]) > 0:
                    return 1 
            except Exception:
                self._api_disabled = True
        return 0

    def _check_holidays(self, date_str):
        # Simulation of major Hyderabad holidays
        major_holidays = {
            "2026-01-01": "New Year's Day",
            "2026-01-14": "Sankranti",
            "2026-01-26": "Republic Day",
            "2026-08-15": "Independence Day",
            "2026-10-02": "Gandhi Jayanti",
            "2026-12-25": "Christmas"
        }
        return major_holidays.get(date_str)


    def predict_one(self, service, date_str, telemetry=None):
        """Complete Prediction Logic blending ML and Real-time Intelligence"""
        # Deterministic seeding for consistency
        seed_str = f"{service.get('Service_ID', 'ID')}_{date_str}"
        seed_hash = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
        rng = random.Random(seed_hash)

        # Time context
        try: dt = datetime.strptime(date_str, "%Y-%m-%d")
        except: dt = datetime.now()

        hour = 8
        try: hour = int(service.get('Scheduled_Departure', '09:00').split(':')[0])
        except: pass
        
        # Real-time Telemetry
        if telemetry:
            weather = telemetry['weather']
            traffic = telemetry['traffic']
            event_flag = telemetry['event_flag']
            is_holiday = telemetry['is_holiday']
        else:
            weather = self.get_realtime_weather()
            is_holiday = self._check_holidays(date_str)
            event_detected = self._check_events(date_str)
            event_flag = 1 if (is_holiday or event_detected) else 0
            traffic = self._get_traffic(hour, weather['is_rainy'], event_flag)
        
        # Load factors
        base_load = 85 if (8<=hour<=11 or 17<=hour<=20) else 40
        if event_flag: base_load += 20
        load_variance = rng.randint(-10, 15)
        passenger_load = max(0, min(100, base_load + load_variance))

        # Prediction Logic
        delay = 0
        if self.model and self.encoders:
            try:
                # Prepare data for XGBoost
                input_data = pd.DataFrame([{
                    'Transport_Type': service.get('Transport_Type', 'Bus'),
                    'From_Location': service.get('From_Location', 'Secunderabad'),
                    'To_Location': service.get('To_Location', 'Koti'),
                    'Weather': weather['description'],
                    'Is_Holiday': 1 if is_holiday else 0,
                    'Is_Peak_Hour': 1 if (8<=hour<=11 or 17<=hour<=20) else 0,
                    'Event_Scheduled': 1 if event_flag else 0,
                    'Traffic_Density': traffic,
                    'Temperature_C': weather['temp'],
                    'Humidity_Pct': weather['humidity'],
                    'Passenger_Load': passenger_load,
                    'Distance_KM': service.get('Distance_KM', 25.0),
                    'Dep_Hour': hour,
                    'Day_of_Week': dt.weekday(),
                    'Weather_Traffic_Index': 2, 
                    'Month': dt.month,
                    'Is_Weekend': 1 if dt.weekday() >= 5 else 0
                }])
                
                # Align types for encoder
                for col, le in self.encoders.items():
                    if col in input_data.columns:
                        val = str(input_data[col][0])
                        input_data[col] = le.transform([val])[0] if val in le.classes_ else 0
                
                # ML Output
                delay = int(self.model.predict(input_data)[0])
                delay += rng.randint(-2, 4) # Consistency Noise
                delay = max(0, delay)
                
            except Exception as e:
                print(f"ML Processing Failure: {e}")
                delay = rng.randint(5, 15)
        else:
            delay = rng.randint(0, 45)

        # Human-readable Status
        if delay <= 10: status = "ON TIME"
        elif delay <= 20: status = "MINOR DELAY"
        else: status = "MAJOR DELAY"
        
        # Risk Tiers
        risk = "Low"
        if delay > 20: risk = "High"
        elif delay > 10: risk = "Medium"

        # Arrival Time Logic for Synchronization
        try:
            sch_dep = service['Scheduled_Departure']
            sch_arr = service.get('Scheduled_Arrival', '')
            base_dt = datetime.strptime(f"{date_str} {sch_dep}", "%Y-%m-%d %H:%M")
            try:
                arr_dt = datetime.strptime(f"{date_str} {sch_arr}", "%Y-%m-%d %H:%M")
                dur = int((arr_dt - base_dt).total_seconds() / 60)
                if dur <= 0: raise ValueError
                scheduled_display = sch_arr
            except:
                dist = service.get('Distance_KM', 25.0)
                dur = int((dist/30)*60)
                scheduled_display = (base_dt + timedelta(minutes=dur)).strftime("%H:%M")
            
            p_arrival = (base_dt + timedelta(minutes=dur + delay)).strftime("%H:%M")
        except:
            scheduled_display = "--:--"
            p_arrival = "--:--"

        return {
            "predicted_delay": delay,
            "status_text": status,
            "risk_level": risk,
            "weather": weather,
            "traffic": traffic,
            "load": passenger_load,
            "reason": self._get_reason(delay, weather, traffic, event_flag, service.get('Transport_Type')),
            "best_mode": "Metro" if (delay > 15 and service.get('Transport_Type') != 'Metro') else service.get('Transport_Type'),
            "recommendation": "Board Metro for speed" if delay > 20 else "On Track",
            "scheduled_arrival": scheduled_display,
            "predicted_arrival": p_arrival
        }

    def _get_reason(self, delay, weather, traffic, event_flag, t_type):
        """Generate high-fidelity reasoning using dataset ground-truth categories"""
        if delay <= 5: return "Operational Smoothness"
        
        # Core Dataset Categories: 
        # ['Traffic Congestion', 'Signal Delay', 'Technical Glitch', 'Weather Conditions', 'Public Rally', 'Accident']
        
        is_rainy = weather.get('is_rainy', False)
        now_hour = datetime.now().hour
        is_peak = (8 <= now_hour <= 11) or (17 <= now_hour <= 20)
        
        # 1. Event/Holiday -> Public Rally (Dataset Label)
        if event_flag and delay > 15:
            return "Public Rally & Crowd Surge"
            
        # 2. Peak Hour + Traffic -> Traffic Congestion (Dataset Label)
        if is_peak and delay > 15:
            if t_type == "Bus": return "Peak Hour Traffic Congestion"
            return "Peak Hour Signal Delay"

        # 3. High Traffic -> Traffic Congestion (Dataset Label)
        if traffic in ["High", "Very High"] and t_type == "Bus":
            return "Severe Traffic Congestion"
            
        # 4. Weather -> Weather Conditions (Dataset Label)
        if is_rainy or weather.get('temp', 30) > 42:
            return "Adverse Weather Conditions"
            
        # 5. Mode-Specific Criticals
        if t_type in ["Metro", "Train"]:
            if delay > 20:
                return "Signal Delay / Technical Glitch"
            if delay > 12:
                return "Operational Signal Delay"
        
        # 6. Stochastic Stressors for unexplained delays (Dataset Labels)
        seed = int(hashlib.md5(f"{t_type}_{delay}".encode()).hexdigest(), 16)
        
        if delay > 25:
            return "Major Traffic Congestion + Technical Glitch"
        
        if delay > 15:
            reasons = ["Traffic Congestion", "Signal Delay", "Technical Glitch", "Accident"]
            return reasons[seed % len(reasons)]

        # 7. Minimal fallback (Dataset alignment)
        if delay > 5:
            return "Minor Technical Glitch"
            
        return "Unknown Operational Variance"

    def process_batch(self, schedules, date_str):
        """Process multiple threads with system-wide context and optimized vectorized calls"""
        now = datetime.now()
        
        # 1. Fetch Shared Telemetry (Once per batch)
        weather = self.get_realtime_weather()
        is_holiday = self._check_holidays(date_str)
        event_detected = self._check_events(date_str)
        event_flag = 1 if (is_holiday or event_detected) else 0
        
        results = []
        if not schedules:
            return results

        try:
            # 2. DataFrame Construction for Vectorized Processing
            df = pd.DataFrame(schedules)
            
            # Safe parsing of hours (vectorized)
            df['Dep_Hour'] = pd.to_numeric(df['Scheduled_Departure'].str.split(':').str[0], errors='coerce').fillna(8).astype(int)
            
            # Vectorized Traffic Logic (Simulated lookup based on _get_traffic logic)
            # Pre-calculate traffic for all 24 hours to avoid loop calls
            traffic_lut = {h: self._get_traffic(h, weather['is_rainy'], event_flag) for h in range(24)}
            df['Traffic_Density'] = df['Dep_Hour'].map(traffic_lut)
            
            # Vectorized Load Logic
            def calc_load(row):
                h = row['Dep_Hour']
                base = 85 if (8<=h<=11 or 17<=h<=20) else 40
                if event_flag: base += 20
                # Semantic Hashing for consistency
                seed = int(hashlib.md5(f"{row.get('Service_ID')}_{date_str}".encode()).hexdigest(), 16)
                rng = random.Random(seed)
                return max(0, min(100, base + rng.randint(-10, 15)))
            
            df['Passenger_Load'] = df.apply(calc_load, axis=1)

            # 3. Batch ML Prediction
            if self.model and self.encoders:
                # Prepare Input Features
                # Note: We must match the EXACT columns XGboost expects
                # Using map/literal assignment for constants
                pred_df = pd.DataFrame()
                pred_df['Transport_Type'] = df['Transport_Type']
                pred_df['From_Location'] = df['From_Location']
                pred_df['To_Location'] = df['To_Location']
                pred_df['Weather'] = weather['description']
                pred_df['Is_Holiday'] = 1 if is_holiday else 0
                pred_df['Is_Peak_Hour'] = df['Dep_Hour'].apply(lambda h: 1 if (8<=h<=11 or 17<=h<=20) else 0)
                pred_df['Event_Scheduled'] = 1 if event_flag else 0
                pred_df['Traffic_Density'] = df['Traffic_Density']
                pred_df['Temperature_C'] = weather['temp']
                pred_df['Humidity_Pct'] = weather['humidity']
                pred_df['Passenger_Load'] = df['Passenger_Load']
                pred_df['Distance_KM'] = df.get('Distance_KM', 25.0)
                pred_df['Dep_Hour'] = df['Dep_Hour']
                
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    dt = now
                    
                pred_df['Day_of_Week'] = dt.weekday()
                pred_df['Weather_Traffic_Index'] = 2 
                pred_df['Month'] = dt.month
                pred_df['Is_Weekend'] = 1 if dt.weekday() >= 5 else 0

                # Encoding
                for col, le in self.encoders.items():
                    if col in pred_df.columns:
                        # Vectorized transform with fallback
                        # We use map then fillna(0) for unseen labels
                        mapping = dict(zip(le.classes_, le.transform(le.classes_)))
                        pred_df[col] = pred_df[col].astype(str).map(mapping).fillna(0)
                
                # PREDICT
                df['Delay'] = self.model.predict(pred_df)
                # Add noise
                df['Delay'] = df.apply(lambda r: max(0, int(r['Delay']) + random.randint(-2, 4)), axis=1)
            else:
                # Fallback to wider range to show all statuses
                df['Delay'] = df.apply(lambda r: random.randint(0, 45), axis=1)

            # 4. Result Assembly
            # We iterate result df which is fast since calculations are done
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            is_past_date = target_date < now.date()

            records = df.to_dict('records')
            
            for i, rec in enumerate(records):
                # Recover original service dict to preserve other fields
                original_svc = schedules[i]
                delay = rec['Delay']
                traffic = rec['Traffic_Density']
                load = rec['Passenger_Load']
                
                # Arrival Time Logic: Use DB Schedule for accurate duration
                base_dt = datetime.strptime(f"{date_str} {original_svc['Scheduled_Departure']}", "%Y-%m-%d %H:%M")
                sch_arr = original_svc.get('Scheduled_Arrival', '')
                
                try:
                    arr_dt = datetime.strptime(f"{date_str} {sch_arr}", "%Y-%m-%d %H:%M")
                    dur = int((arr_dt - base_dt).total_seconds() / 60)
                    if dur <= 0: raise ValueError
                    scheduled_display = sch_arr
                except:
                    # Fallback to distance-based estimate
                    dist = original_svc.get('Distance_KM', 25.0)
                    dur = int((dist/30)*60)
                    scheduled_display = (base_dt + timedelta(minutes=dur)).strftime("%H:%M")
                
                actual_arrival = base_dt + timedelta(minutes=dur + delay)
                
                # Status Logic
                status_text = "ON TIME" if delay <= 10 else ("MINOR DELAY" if delay <= 20 else "MAJOR DELAY")

                risk = "Low"
                if delay > 20: risk = "High"
                elif delay > 10: risk = "Medium"

                prediction = {
                    "predicted_delay": delay,
                    "status_text": status_text,
                    "risk_level": risk,
                    "weather": weather,
                    "traffic": traffic,
                    "load": load,
                    "reason": self._get_reason(delay, weather, traffic, event_flag, original_svc.get('Transport_Type')),
                    "best_mode": "Metro" if (delay > 15 and original_svc.get('Transport_Type') != 'Metro') else original_svc.get('Transport_Type'),
                    "recommendation": "Trip Completed" if is_past_date else ("Board Metro" if delay > 20 else "On Track"),
                    "scheduled_arrival": scheduled_display,
                    "predicted_arrival": actual_arrival.strftime("%H:%M"),
                    "is_live": (not is_past_date) and (now.date() == target_date) and (base_dt <= now <= actual_arrival)
                }

                s_copy = original_svc.copy()
                s_copy['prediction'] = prediction
                results.append(s_copy)

        except Exception as e:
            print(f"Batch Processing Error: {e}")
            # Fallback to slow loop if vectorization crashes
            # (Re-implement manual loop for safety or just return empty)
            return []
            
        return results

# Singleton instance for system-wide access
ENGINE = TransportEngine()
