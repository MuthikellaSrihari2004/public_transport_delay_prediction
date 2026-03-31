"""
engine.py — Prediction Engine
===============================
Core ML inference engine that blends XGBoost predictions with
real-time weather, traffic, and event data to produce delay forecasts.
"""

import pandas as pd
import numpy as np
import joblib
import os
import sys
import requests
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config


class TransportEngine:
    """Prediction engine combining ML model with real-time data."""

    def __init__(self):
        self.model = None
        self.encoders = None

        # Load ML artifacts if available
        if os.path.exists(config.XGBOOST_MODEL_PATH) and os.path.exists(config.LABEL_ENCODERS_PATH):
            self.model = joblib.load(config.XGBOOST_MODEL_PATH)
            self.encoders = joblib.load(config.LABEL_ENCODERS_PATH)
            print("ML model loaded successfully.")
        else:
            print("Warning: ML model not found. Using heuristic fallback.")

        # API keys
        self.traffic_key = config.TRAFFIC_API_KEY
        self.event_key = config.EVENT_API_KEY

        # Cache
        self._weather_cache = None
        self._traffic_cache = {}
        self._cache_time = None
        self._api_disabled = False

    # ── Real-time Data ──────────────────────────────────────────────────

    def get_realtime_weather(self):
        """Fetch live weather from Open-Meteo API (no key required)."""
        now = datetime.now()

        # Return cached data if fresh (10-minute cache)
        if self._weather_cache and self._cache_time and (now - self._cache_time).seconds < 600:
            return self._weather_cache

        # Default fallback
        weather = {"description": "Clear", "temp": 24.0, "humidity": 50,
                    "is_rainy": False, "source": "Simulated"}

        try:
            url = ("https://api.open-meteo.com/v1/forecast"
                   "?latitude=17.3850&longitude=78.4867"
                   "&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code"
                   "&timezone=auto")
            resp = requests.get(url, timeout=3)

            if resp.status_code == 200:
                data = resp.json()['current']
                code = data['weather_code']

                # WMO weather code mapping
                desc_map = {
                    0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
                    45: "Foggy", 48: "Foggy",
                    51: "Light Drizzle", 53: "Drizzle", 55: "Dense Drizzle",
                    61: "Light Rain", 63: "Moderate Rain", 65: "Heavy Rain",
                    71: "Light Snow", 73: "Snow", 75: "Heavy Snow",
                    80: "Rain Showers", 81: "Rain Showers", 82: "Heavy Rain Showers",
                    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"
                }

                rainy_codes = {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}

                weather = {
                    "description": desc_map.get(code, "Clear"),
                    "temp": round(data['apparent_temperature'], 1),
                    "humidity": data['relative_humidity_2m'],
                    "is_rainy": code in rainy_codes,
                    "source": "Open-Meteo"
                }
        except Exception as e:
            print(f"Weather API error: {e}")

        self._weather_cache = weather
        self._cache_time = now
        return weather

    def _get_traffic(self, hour, is_rainy, event_flag):
        """Estimate traffic density from API or time-based heuristic."""
        now = datetime.now()
        cache_key = f"{hour}_{is_rainy}_{event_flag}"

        if cache_key in self._traffic_cache and self._cache_time and (now - self._cache_time).seconds < 300:
            return self._traffic_cache[cache_key]

        status = "Low"

        # Try TomTom API if configured
        if not self._api_disabled and self.traffic_key and self.traffic_key not in ["YOUR_TOMTOM_API_KEY", ""]:
            try:
                if 'live' in self._traffic_cache and self._cache_time and (now - self._cache_time).seconds < 300:
                    status = self._traffic_cache['live']
                else:
                    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point=17.3850,78.4867&key={self.traffic_key}"
                    res = requests.get(url, timeout=1).json()
                    if "flowSegmentData" in res:
                        ratio = res["flowSegmentData"].get("currentSpeed", 30) / res["flowSegmentData"].get("freeFlowSpeed", 40)
                        if ratio < 0.4:   status = "Very High"
                        elif ratio < 0.7: status = "High"
                        elif ratio < 0.9: status = "Medium"
                        self._traffic_cache['live'] = status
            except Exception:
                self._api_disabled = True

        # Heuristic fallback
        if status == "Low":
            score = 0
            if 8 <= hour <= 11 or 17 <= hour <= 20: score += 5
            if is_rainy: score += 3
            if event_flag: score += 4

            if score >= 9:   status = "Very High"
            elif score >= 6: status = "High"
            elif score >= 3: status = "Medium"

        self._traffic_cache[cache_key] = status
        return status

    def _check_events(self, date_str):
        """Check if major events are scheduled on the given date."""
        special_dates = ["2026-01-26", "2026-01-30", "2026-02-14"]
        if date_str in special_dates:
            return 1

        if not self._api_disabled and self.event_key and self.event_key not in ["YOUR_EVENT_API_KEY", ""]:
            try:
                headers = {"Authorization": f"Bearer {self.event_key}", "Accept": "application/json"}
                url = (f"https://api.predicthq.com/v1/events/"
                       f"?location_around.origin=17.3850,78.4867"
                       f"&active.gte={date_str}&active.lte={date_str}"
                       f"&category=concerts,sports,festivals")
                res = requests.get(url, headers=headers, timeout=1).json()
                if res.get("results"):
                    return 1
            except Exception:
                self._api_disabled = True
        return 0

    def _check_holidays(self, date_str):
        """Return holiday name if date is a holiday, else None."""
        holidays = {
            "2026-01-01": "New Year's Day",
            "2026-01-14": "Sankranti",
            "2026-01-26": "Republic Day",
            "2026-08-15": "Independence Day",
            "2026-10-02": "Gandhi Jayanti",
            "2026-12-25": "Christmas"
        }
        return holidays.get(date_str)

    # ── Prediction Logic ────────────────────────────────────────────────

    def predict_one(self, service, date_str, telemetry=None):
        """Predict delay for a single service."""
        # Deterministic seed for consistent results
        seed_str = f"{service.get('Service_ID', 'X')}_{date_str}"
        seed_hash = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
        rng = random.Random(seed_hash)

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            dt = datetime.now()

        hour = 8
        try:
            hour = int(service.get('Scheduled_Departure', '09:00').split(':')[0])
        except (ValueError, AttributeError):
            pass

        is_peak = (8 <= hour <= 11 or 17 <= hour <= 20)

        # Get environment context
        if telemetry:
            weather = telemetry['weather']
            traffic = telemetry['traffic']
            event_flag = telemetry['event_flag']
            is_holiday = telemetry['is_holiday']
        else:
            weather = self.get_realtime_weather()
            is_holiday = self._check_holidays(date_str)
            event_flag = 1 if (is_holiday or self._check_events(date_str)) else 0
            traffic = self._get_traffic(hour, weather['is_rainy'], event_flag)

        # Estimate passenger load
        base_load = 85 if is_peak else 40
        if event_flag:
            base_load += 20
        passenger_load = max(0, min(100, base_load + rng.randint(-10, 15)))

        # ML prediction
        if self.model and self.encoders:
            try:
                input_data = pd.DataFrame([{
                    'Transport_Type': service.get('Transport_Type', 'Bus'),
                    'From_Location': service.get('From_Location', 'Secunderabad'),
                    'To_Location': service.get('To_Location', 'Koti'),
                    'Weather': weather['description'],
                    'Is_Holiday': 1 if is_holiday else 0,
                    'Is_Peak_Hour': 1 if is_peak else 0,
                    'Event_Scheduled': 1 if event_flag else 0,
                    'Traffic_Density': traffic,
                    'Temperature_C': weather['temp'],
                    'Humidity_Pct': weather['humidity'],
                    'Passenger_Load': passenger_load,
                    'Distance_KM': service.get('Distance_KM', config.DEFAULT_DISTANCE_KM),
                    'Dep_Hour': hour,
                    'Day_of_Week': dt.weekday(),
                    'Weather_Traffic_Index': 2,
                    'Month': dt.month,
                    'Is_Weekend': 1 if dt.weekday() >= 5 else 0
                }])

                for col, le in self.encoders.items():
                    if col in input_data.columns:
                        val = str(input_data[col][0])
                        input_data[col] = le.transform([val])[0] if val in le.classes_ else 0

                base_delay = int(self.model.predict(input_data)[0])
                delay = self._apply_noise(base_delay, service.get('Service_ID'), date_str)
            except Exception as e:
                print(f"ML prediction error: {e}")
                delay = self._apply_noise(10, service.get('Service_ID'), date_str)
        else:
            delay = self._apply_noise(15, service.get('Service_ID'), date_str)

        # Classify delay
        if delay <= 10:
            status, risk = "ON TIME", "Low"
        elif delay <= 20:
            status, risk = "MINOR DELAY", "Medium"
        else:
            status, risk = "MAJOR DELAY", "High"

        # Calculate arrival times
        try:
            sch_dep = service['Scheduled_Departure']
            sch_arr = service.get('Scheduled_Arrival', '')
            base_dt = datetime.strptime(f"{date_str} {sch_dep}", "%Y-%m-%d %H:%M")
            try:
                arr_dt = datetime.strptime(f"{date_str} {sch_arr}", "%Y-%m-%d %H:%M")
                dur = int((arr_dt - base_dt).total_seconds() / 60)
                if dur <= 0:
                    raise ValueError
                scheduled_display = sch_arr
            except (ValueError, TypeError):
                dist = service.get('Distance_KM', config.DEFAULT_DISTANCE_KM)
                dur = int((dist / 30) * 60)
                scheduled_display = (base_dt + timedelta(minutes=dur)).strftime("%H:%M")

            predicted_arrival = (base_dt + timedelta(minutes=dur + delay)).strftime("%H:%M")
        except Exception:
            scheduled_display = "--:--"
            predicted_arrival = "--:--"

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
            "predicted_arrival": predicted_arrival
        }

    def _get_reason(self, delay, weather, traffic, event_flag, t_type):
        """Generate human-readable delay reason."""
        if delay <= 5:
            return "Operational Smoothness"

        is_rainy = weather.get('is_rainy', False)
        is_peak = (8 <= datetime.now().hour <= 11) or (17 <= datetime.now().hour <= 20)

        if event_flag and delay > 15:
            return "Public Rally & Crowd Surge"
        if is_peak and delay > 15:
            return "Peak Hour Traffic Congestion" if t_type == "Bus" else "Peak Hour Signal Delay"
        if traffic in ["High", "Very High"] and t_type == "Bus":
            return "Severe Traffic Congestion"
        if is_rainy or weather.get('temp', 30) > 42:
            return "Adverse Weather Conditions"
        if t_type in ["Metro", "Train"]:
            if delay > 20:
                return "Signal Delay / Technical Glitch"
            if delay > 12:
                return "Operational Signal Delay"
        if delay > 25:
            return "Major Traffic Congestion + Technical Glitch"
        if delay > 15:
            reasons = ["Traffic Congestion", "Signal Delay", "Technical Glitch", "Accident"]
            seed = int(hashlib.md5(f"{t_type}_{delay}".encode()).hexdigest(), 16)
            return reasons[seed % len(reasons)]
        if delay > 5:
            return "Minor Technical Glitch"

        return "Unknown Operational Variance"

    def _apply_noise(self, base_delay, service_id, date_str):
        """Apply deterministic noise for consistency across calls."""
        seed_str = f"{service_id}_{date_str}"
        seed_hash = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
        rng = random.Random(seed_hash)
        return max(0, int(base_delay) + rng.randint(-2, 3))

    # ── Batch Processing ────────────────────────────────────────────────

    def process_batch(self, schedules, date_str):
        """Process multiple schedules with ML inference. Returns results even on failure."""
        if not schedules:
            return []

        now = datetime.now()
        results = []

        # Normalize keys and set default predictions
        key_map = {
            'transport_type': 'Transport_Type', 'service_id': 'Service_ID',
            'scheduled_departure': 'Scheduled_Departure', 'scheduled_arrival': 'Scheduled_Arrival',
            'from_location': 'From_Location', 'to_location': 'To_Location',
            'distance_km': 'Distance_KM'
        }

        for s in schedules:
            row = s.copy()
            for old_key, new_key in key_map.items():
                if old_key in row:
                    row[new_key] = row.pop(old_key)

            row['prediction'] = {
                "predicted_delay": 5, "status_text": "ON TIME", "risk_level": "Low",
                "weather": {"description": "Clear", "temp": 28}, "traffic": "Low", "load": 40,
                "reason": "Operational Sync", "best_mode": row.get('Transport_Type', 'Bus'),
                "recommendation": "On Track",
                "scheduled_arrival": row.get('Scheduled_Arrival', '--:--'),
                "predicted_arrival": row.get('Scheduled_Arrival', '--:--'),
                "is_live": False
            }
            results.append(row)

        try:
            df = pd.DataFrame(results)

            # Environment context
            weather = self.get_realtime_weather()
            is_holiday = self._check_holidays(date_str)
            event_flag = 1 if (is_holiday or self._check_events(date_str)) else 0

            # Feature enrichment
            df['Dep_Hour'] = pd.to_numeric(
                df['Scheduled_Departure'].str.split(':').str[0], errors='coerce'
            ).fillna(8).astype(int)

            is_today = (date_str == now.strftime("%Y-%m-%d"))
            live_traffic = self._get_traffic(now.hour, weather['is_rainy'], event_flag) if is_today else None

            traffic_lut = {}
            for h in range(24):
                traffic_lut[h] = live_traffic if (is_today and h == now.hour) else self._get_traffic(h, weather['is_rainy'], event_flag)
            df['Traffic_Density'] = df['Dep_Hour'].map(traffic_lut)

            def calc_load(row):
                h = row['Dep_Hour']
                base = 85 if (8 <= h <= 11 or 17 <= h <= 20) else 40
                if event_flag:
                    base += 20
                seed = int(hashlib.md5(str(row.get('Service_ID')).encode()).hexdigest(), 16)
                return max(0, min(100, base + (seed % 25 - 10)))

            df['Passenger_Load'] = df.apply(calc_load, axis=1)

            # ML inference
            if self.model:
                try:
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        dt = now

                    model_features = config.MODEL_FEATURES + config.OPTIONAL_FEATURES

                    pred_data = pd.DataFrame({
                        'Transport_Type': df['Transport_Type'],
                        'From_Location': df['From_Location'],
                        'To_Location': df['To_Location'],
                        'Weather': [weather['description']] * len(df),
                        'Is_Holiday': [1 if is_holiday else 0] * len(df),
                        'Is_Peak_Hour': df['Dep_Hour'].apply(lambda h: 1 if (8 <= h <= 11 or 17 <= h <= 20) else 0),
                        'Event_Scheduled': [1 if event_flag else 0] * len(df),
                        'Traffic_Density': df['Traffic_Density'],
                        'Temperature_C': [weather['temp']] * len(df),
                        'Humidity_Pct': [weather['humidity']] * len(df),
                        'Passenger_Load': df['Passenger_Load'],
                        'Distance_KM': df.get('Distance_KM', config.DEFAULT_DISTANCE_KM).fillna(config.DEFAULT_DISTANCE_KM),
                        'Dep_Hour': df['Dep_Hour'],
                        'Day_of_Week': [dt.weekday()] * len(df),
                        'Weather_Traffic_Index': df['Traffic_Density'].map(
                            {'Low': 1, 'Medium': 2, 'High': 3, 'Very High': 4}
                        ).fillna(2) * (2 if weather['is_rainy'] else 1),
                        'Month': [dt.month] * len(df),
                        'Is_Weekend': [1 if dt.weekday() >= 5 else 0] * len(df)
                    })

                    pred_data = pred_data[model_features]

                    # Encode categorical features
                    if self.encoders:
                        for col, le in self.encoders.items():
                            if col in pred_data.columns:
                                mapping = {str(c): i for i, c in enumerate(le.classes_)}
                                pred_data[col] = pred_data[col].astype(str).map(mapping).fillna(0).astype(float)

                    pred_data = pred_data.apply(pd.to_numeric, errors='coerce').fillna(0)
                    base_delays = self.model.predict(pred_data)
                    df['Delay'] = [self._apply_noise(d, results[i].get('Service_ID'), date_str)
                                   for i, d in enumerate(base_delays)]

                except Exception as e:
                    print(f"ML batch error: {e}")
                    df['Delay'] = df.apply(
                        lambda row: self._apply_noise(int(row['Passenger_Load'] / 4), row.get('Service_ID'), date_str),
                        axis=1
                    )
            else:
                df['Delay'] = df.apply(
                    lambda row: self._apply_noise(5, row.get('Service_ID'), date_str), axis=1
                )

            # Update prediction results
            for i, row in df.iterrows():
                delay = int(row['Delay'])
                p = results[i]['prediction']
                p['predicted_delay'] = delay
                p['status_text'] = "ON TIME" if delay <= 10 else ("MINOR DELAY" if delay <= 20 else "MAJOR DELAY")
                p['risk_level'] = "Low" if delay <= 10 else ("Medium" if delay <= 20 else "High")
                p['weather'] = weather
                p['traffic'] = row['Traffic_Density']
                p['load'] = row['Passenger_Load']
                p['reason'] = self._get_reason(delay, weather, row['Traffic_Density'], event_flag,
                                               results[i].get('Transport_Type'))

                # Calculate predicted arrival
                base_dt = datetime.strptime(f"{date_str} {results[i]['Scheduled_Departure']}", "%Y-%m-%d %H:%M")
                try:
                    arr_dt = datetime.strptime(f"{date_str} {results[i]['Scheduled_Arrival']}", "%Y-%m-%d %H:%M")
                    dur = int((arr_dt - base_dt).total_seconds() / 60)
                except (ValueError, TypeError):
                    dur = 30

                p['predicted_arrival'] = (base_dt + timedelta(minutes=dur + delay)).strftime("%H:%M")
                p['is_live'] = is_today and (base_dt <= now <= base_dt + timedelta(minutes=dur + delay))

        except Exception as e:
            print(f"Batch processing error: {e}")

        return results


# Singleton — imported by app.py and other modules
ENGINE = TransportEngine()
