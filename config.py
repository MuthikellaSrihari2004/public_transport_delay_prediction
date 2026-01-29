"""
Central Configuration for HyderTrax Transport Delay Prediction System

This module contains all configuration constants, paths, and settings.
All other modules should import from this file instead of using hardcoded paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# PROJECT PATHS
# ============================================================================

# Root directory of the project
PROJECT_ROOT = Path(__file__).parent.absolute()

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# Model directories
MODELS_DIR = PROJECT_ROOT / "models"

# Report directories
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Source code directories
SRC_DIR = PROJECT_ROOT / "src"
DATA_SRC_DIR = SRC_DIR / "data"
DATABASE_SRC_DIR = SRC_DIR / "database"
MODELS_SRC_DIR = SRC_DIR / "models"
VISUALIZATION_SRC_DIR = SRC_DIR / "visualization"

# Template and static directories
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
CSS_DIR = STATIC_DIR / "css"

# ============================================================================
# FILE PATHS
# ============================================================================

# Data files
RAW_DATA_FILE = RAW_DATA_DIR / "hyderabad_transport_raw.csv"
CLEANED_DATA_FILE = PROCESSED_DATA_DIR / "hyderabad_transport_cleaned.csv"
FEATURES_DATA_FILE = PROCESSED_DATA_DIR / "hyderabad_transport_features.csv"

# Database
DB_PATH = DATA_DIR / "transport.db"

# Model files
XGBOOST_MODEL_PATH = MODELS_DIR / "xgboost_delay_model.pkl"
XGBOOST_TUNED_MODEL_PATH = MODELS_DIR / "xgboost_tuned_model.pkl"
LABEL_ENCODERS_PATH = MODELS_DIR / "label_encoders.pkl"

# Report files
EDA_INSIGHTS_FILE = REPORTS_DIR / "eda_insights.md"

# ============================================================================
# DATA GENERATION SETTINGS
# ============================================================================

# Number of records to generate
DATA_GENERATION_SIZE = 100000

# Date range for synthetic data
DATA_START_DATE = "2025-01-01"
DATA_END_DATE = "2026-12-31"

# Hyderabad locations
HYDERABAD_LOCATIONS = [
    "Secunderabad", "Koti", "Mehdipatnam", "Charminar", "Hyderabad (Nampally)", 
    "Kacheguda", "Begumpet", "L.B. Nagar", "Dilsukhnagar", "Kukatpally", "Miyapur",
    "Ameerpet", "Parade Ground", "JBS", "MGBS", "Uppal",
    "Hitech City", "Gachibowli", "Madhapur", "Kondapur"
]

# Transport types
TRANSPORT_TYPES = ["Bus", "Metro", "Train"]

# Weather conditions
WEATHER_CONDITIONS = [
    "Clear", "Sunny", "Partly Cloudy", "Cloudy", "Overcast",
    "Rainy", "Light Rain", "Heavy Rain", "Drizzle",
    "Foggy", "Mist", "Mainly Clear"
]

# Traffic levels
TRAFFIC_LEVELS = ["Low", "Medium", "High", "Very High"]

# ============================================================================
# MODEL TRAINING SETTINGS
# ============================================================================

# Features to use for training
MODEL_FEATURES = [
    'Transport_Type', 'From_Location', 'To_Location', 'Weather',
    'Is_Holiday', 'Is_Peak_Hour', 'Event_Scheduled', 'Traffic_Density',
    'Temperature_C', 'Humidity_Pct', 'Passenger_Load', 'Distance_KM',
    'Dep_Hour', 'Day_of_Week', 'Weather_Traffic_Index'
]

# Optional features (if available)
OPTIONAL_FEATURES = ['Month', 'Is_Weekend']

# Target variable
TARGET_VARIABLE = 'Delay_Minutes'

# Train-test split ratio
TEST_SIZE = 0.2
RANDOM_STATE = 42

# XGBoost hyperparameters
XGBOOST_PARAMS = {
    'n_estimators': 200,
    'learning_rate': 0.05,
    'max_depth': 8,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'n_jobs': -1,
    'random_state': RANDOM_STATE
}

# ============================================================================
# API SETTINGS
# ============================================================================

# OpenWeather API
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_CITY = "Hyderabad"
OPENWEATHER_COUNTRY = "IN"

# Optional API keys
TRAFFIC_API_KEY = os.getenv("TRAFFIC_API_KEY", "")
EVENT_API_KEY = os.getenv("EVENT_API_KEY", "")
HOLIDAY_API_KEY = os.getenv("HOLIDAY_API_KEY", "")

# ============================================================================
# FLASK APPLICATION SETTINGS
# ============================================================================

# Flask configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("DEBUG", "True").lower() == "true"
FLASK_PORT = int(os.getenv("FLASK_PORT", "8000"))
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
SECRET_KEY = os.getenv("SECRET_KEY", "hyder-transit-secret-key")

# ============================================================================
# DATABASE SETTINGS
# ============================================================================

# Database configuration
DB_ECHO = False  # Set to True to see SQL queries
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10

# ============================================================================
# LOGGING SETTINGS
# ============================================================================

LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "hydertrax.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# PREDICTION ENGINE SETTINGS
# ============================================================================

# Delay categories (Standardized: 0-10, 11-20, >20)
DELAY_CATEGORY_THRESHOLDS = {
    "on_time": (0, 10),
    "minor_delay": (10, 20),
    "major_delay": (20, float('inf'))
}

# Default prediction parameters
DEFAULT_PASSENGER_LOAD = 50
DEFAULT_DISTANCE_KM = 25.0

# Speed estimates (km/h)
SPEED_ESTIMATES = {
    "Bus": 25,
    "Metro": 45,
    "Train": 60
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

from datetime import datetime, timedelta

def get_now_ist():
    """Helper to get current time in IST (UTC+5:30) for consistency across deployments"""
    import datetime as dt
    return dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)

def ensure_directories():
    """Create all necessary directories if they don't exist"""
    directories = [
        DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR,
        MODELS_DIR, REPORTS_DIR, FIGURES_DIR, LOG_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print("✅ All required directories are ready")


def get_database_uri():
    """Get database connection URI"""
    return f"sqlite:///{DB_PATH}"


def get_database_path_str():
    """Get database path as string"""
    return str(DB_PATH)


def validate_environment():
    """Validate that all required environment variables and files exist"""
    issues = []
    
    # Check for API key
    if not OPENWEATHER_API_KEY:
        issues.append("⚠️  OPENWEATHER_API_KEY not set in .env file")
    
    # Check for model files (only if models should exist)
    if XGBOOST_MODEL_PATH.exists() and not LABEL_ENCODERS_PATH.exists():
        issues.append("❌ Model file exists but label encoders are missing")
    
    if issues:
        print("\n".join(issues))
        return False
    
    print("✅ Environment validation passed")
    return True


def print_config_summary():
    """Print a summary of current configuration"""
    print("=" * 70)
    print("         HYDERTRAX CONFIGURATION SUMMARY")
    print("=" * 70)
    print(f"Project Root:     {PROJECT_ROOT}")
    print(f"Database:         {DB_PATH}")
    print(f"Raw Data:         {RAW_DATA_FILE}")
    print(f"Processed Data:   {FEATURES_DATA_FILE}")
    print(f"Model Path:       {XGBOOST_MODEL_PATH}")
    print(f"Flask Debug:      {FLASK_DEBUG}")
    print(f"Flask Port:       {FLASK_PORT}")
    print(f"Log Level:        {LOG_LEVEL}")
    print("=" * 70)


# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # When run directly, print configuration and validate
    print_config_summary()
    ensure_directories()
    validate_environment()
