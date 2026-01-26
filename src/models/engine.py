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
        """Fetch live weather or fallback to simulated data with 5-min caching"""
        now = datetime.now()
        if self._weather_cache and self._cache_time and (now - self._cache_time).seconds < 300:
            return self._weather_cache

        lat, lon = 17.3850, 78.4867
        weather_data = {"description": "Partly Cloudy", "temp": 29.0, "humidity": 60, "is_rainy": False, "source": "Simulated"}
        
        if not self._api_disabled and self.weather_key and self.weather_key not in ["YOUR_OPENWEATHER_API_KEY", ""]:
            try:
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.weather_key}&units=metric"
                resp = requests.get(url, timeout=1) # Fast timeout
                if resp.status_code == 200:
                    d = resp.json()
                    weather_data = {
                        "description": d['weather'][0]['main'],
                        "temp": d['main']['temp'],
                        "humidity": d['main']['humidity'],
                        "is_rainy": "Rain" in d['weather'][0]['main'],
                        "source": "Live API"
                    }
            except Exception:
                print("📡 Weather API unreachable. Switching to simulation mode.")
                self._api_disabled = True
            
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
            delay = rng.randint(5, 15)

        # Human-readable Status
        if delay <= 5: status = "ON TIME"
        elif delay <= 15: status = "MINOR DELAY"
        else: status = "MAJOR DELAY"
        
        # Risk Tiers
        risk = "Low"
        if delay > 25: risk = "High"
        elif delay > 10: risk = "Medium"

        return {
            "predicted_delay": delay,
            "status_text": status,
            "risk_level": risk,
            "weather": weather,
            "traffic": traffic,
            "load": passenger_load,
            "reason": self._get_reason(delay, weather, traffic, event_flag, service.get('Transport_Type')),
            "best_mode": "Metro" if (delay > 15 and service.get('Transport_Type') != 'Metro') else service.get('Transport_Type'),
            "recommendation": "Board Metro for speed" if delay > 20 else "On Track"
        }

    def _get_reason(self, delay, weather, traffic, event_flag, t_type):
        if delay <= 5: return "Optimal Operations"
        reasons = []
        if weather['is_rainy']: reasons.append("Adverse Weather")
        if event_flag: reasons.append("Local Event Impact")
        if traffic in ["High", "Very High"]: reasons.append("Traffic Congestion")
        
        if not reasons: return "Operational Delay"
        return " & ".join(reasons[:2])

    def process_batch(self, schedules, date_str):
        """Process multiple threads with system-wide context and optimized calls"""
        now = datetime.now()
        
        # Fetch shared telemetry once to avoid redundant API calls within the loop
        weather = self.get_realtime_weather()
        is_holiday = self._check_holidays(date_str)
        event_detected = self._check_events(date_str)
        event_flag = 1 if (is_holiday or event_detected) else 0
        
        # We can't cache traffic per-batch perfectly because 'hour' shifts, 
        # but predict_one now uses the internal cache we added to _get_traffic.
        
        results = []
        for svc in schedules:
            try:
                # Create per-service telemetry context (Traffic varies by service hour)
                hour = int(svc.get('Scheduled_Departure', '09:00').split(':')[0])
                traffic = self._get_traffic(hour, weather['is_rainy'], event_flag)
                
                telemetry = {
                    'weather': weather, 
                    'traffic': traffic, 
                    'event_flag': event_flag, 
                    'is_holiday': is_holiday
                }
                
                res = self.predict_one(svc, date_str, telemetry=telemetry)
                
                # Enrich with absolute timing
                original_dep = svc.get('Scheduled_Departure', '09:00')
                try:
                    base_dt = datetime.strptime(f"{date_str} {original_dep}", "%Y-%m-%d %H:%M")
                except:
                    base_dt = now
                    
                dist = svc.get('Distance_KM', 25.0)
                spd = 30 # standard spd
                dur = int((dist/spd)*60)
                
                actual_arrival = base_dt + timedelta(minutes=dur + res['predicted_delay'])
                
                res['predicted_arrival'] = actual_arrival.strftime("%H:%M")
                try:
                    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    res['is_live'] = (now.date() == target_date) and (base_dt <= now <= actual_arrival)
                except:
                    res['is_live'] = False
                
                s_copy = svc.copy()
                s_copy['prediction'] = res
                results.append(s_copy)
            except Exception as e:
                print(f"Error processing service: {e}")
                continue
            
        return results

# Singleton instance for system-wide access
ENGINE = TransportEngine()
