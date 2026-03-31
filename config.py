"""
config.py — Central Configuration
===================================
All paths, settings, and constants for the HyderTrax system.
Every module imports from here instead of using hardcoded values.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Project Paths ───────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.absolute()

# Data
DATA_DIR        = PROJECT_ROOT / "data"
RAW_DATA_DIR    = DATA_DIR / "raw"
PROCESSED_DIR   = DATA_DIR / "processed"

# Models
MODELS_DIR      = PROJECT_ROOT / "models"

# Reports
REPORTS_DIR     = PROJECT_ROOT / "reports"
FIGURES_DIR     = REPORTS_DIR / "figures"

# ── File Paths ──────────────────────────────────────────────────────────

RAW_DATA_FILE      = RAW_DATA_DIR / "hyderabad_transport_raw.csv"
CLEANED_DATA_FILE  = PROCESSED_DIR / "hyderabad_transport_cleaned.csv"
FEATURES_DATA_FILE = PROCESSED_DIR / "hyderabad_transport_features.csv"

DB_PATH              = DATA_DIR / "transport.db"
XGBOOST_MODEL_PATH   = MODELS_DIR / "xgboost_delay_model.pkl"
XGBOOST_TUNED_MODEL_PATH = MODELS_DIR / "xgboost_tuned_model.pkl"
LABEL_ENCODERS_PATH  = MODELS_DIR / "label_encoders.pkl"
EDA_INSIGHTS_FILE    = REPORTS_DIR / "eda_insights.md"

# ── Data Generation ────────────────────────────────────────────────────

HYDERABAD_LOCATIONS = [
    "Secunderabad", "Koti", "Mehdipatnam", "Charminar", "Ameerpet",
    "Hitech City", "Gachibowli", "Miyapur", "Uppal", "L.B. Nagar",
    "Kukatpally", "Dilsukhnagar", "Begumpet", "Madhapur", "Kondapur",
    "Hyderabad (Nampally)", "Kacheguda", "Parade Ground", "JBS", "MGBS"
]

TRANSPORT_TYPES = ["Bus", "Metro", "Train"]

WEATHER_CONDITIONS = [
    "Clear", "Sunny", "Partly Cloudy", "Cloudy", "Overcast",
    "Rainy", "Light Rain", "Heavy Rain", "Drizzle",
    "Foggy", "Mist", "Mainly Clear"
]

TRAFFIC_LEVELS = ["Low", "Medium", "High", "Very High"]

# ── Model Training ─────────────────────────────────────────────────────

MODEL_FEATURES = [
    'Transport_Type', 'From_Location', 'To_Location', 'Weather',
    'Is_Holiday', 'Is_Peak_Hour', 'Event_Scheduled', 'Traffic_Density',
    'Temperature_C', 'Humidity_Pct', 'Passenger_Load', 'Distance_KM',
    'Dep_Hour', 'Day_of_Week', 'Weather_Traffic_Index'
]

OPTIONAL_FEATURES = ['Month', 'Is_Weekend']
TARGET_VARIABLE   = 'Delay_Minutes'
TEST_SIZE         = 0.2
RANDOM_STATE      = 42

XGBOOST_PARAMS = {
    'n_estimators': 200,
    'learning_rate': 0.05,
    'max_depth': 8,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'n_jobs': -1,
    'random_state': RANDOM_STATE
}

# ── API Keys ────────────────────────────────────────────────────────────

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
TRAFFIC_API_KEY     = os.getenv("TRAFFIC_API_KEY", "")
EVENT_API_KEY       = os.getenv("EVENT_API_KEY", "")

# ── Flask Settings ──────────────────────────────────────────────────────

FLASK_DEBUG  = os.getenv("DEBUG", "True").lower() == "true"
FLASK_PORT   = int(os.getenv("FLASK_PORT", "8000"))
SECRET_KEY   = os.getenv("SECRET_KEY", "hyder-transit-secret-key")

# ── Prediction Settings ────────────────────────────────────────────────

DELAY_CATEGORIES = {
    "on_time":      (0, 10),
    "minor_delay":  (10, 20),
    "major_delay":  (20, float('inf'))
}

DEFAULT_DISTANCE_KM = 25.0

SPEED_ESTIMATES = {
    "Bus":   25,
    "Metro": 45,
    "Train": 60
}

# ── Utility Functions ───────────────────────────────────────────────────

def get_now_ist():
    """Get current time in IST (UTC+5:30)."""
    return datetime.utcnow() + timedelta(hours=5, minutes=30)


def ensure_directories():
    """Create all required directories."""
    for d in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DIR, MODELS_DIR,
              REPORTS_DIR, FIGURES_DIR]:
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_directories()
    print(f"Project Root : {PROJECT_ROOT}")
    print(f"Database     : {DB_PATH}")
    print(f"Model        : {XGBOOST_MODEL_PATH}")
    print(f"Features     : {FEATURES_DATA_FILE}")
