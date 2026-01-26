# Project Analysis & Architecture Overview

**Project:** Hyderabad Public Transport Delay Prediction System  
**Type:** Machine Learning Web Application  
**Date:** January 26, 2026

---

## 📋 Executive Summary

This is a comprehensive ML-powered web application that predicts public transport delays in Hyderabad. The project includes data generation, cleaning, feature engineering, model training, database management, and a Flask web interface.

### Current Status: ✅ Functional but needs organizational improvements

---

## 🏗️ Project Structure Analysis

### ✅ Properly Organized Components:

```
project/
├── data/                           # Data storage
│   ├── raw/                       # Raw generated data
│   ├── processed/                 # Cleaned & feature-engineered data
│   ├── external/                  # External data sources
│   └── transport.db              # SQLite database
│
├── src/                          # Source code (well-organized)
│   ├── data/                     # Data pipeline
│   │   ├── make_dataset.py      # Generates synthetic transport data
│   │   ├── clean_data.py        # Data cleaning pipeline
│   │   └── build_features.py    # Feature engineering
│   │
│   ├── database/                 # Database layer
│   │   ├── db_config.py         # DB initialization & schema
│   │   ├── queries.py           # Query utilities (TransportDB class)
│   │   └── migrate_data.py      # CSV to DB migration
│   │
│   ├── models/                   # ML models
│   │   ├── engine.py            # Prediction engine (TransportEngine)
│   │   ├── train_model.py       # Model training
│   │   ├── evaluate_model.py    # Model evaluation
│   │   ├── tune_model.py        # Hyperparameter tuning
│   │   ├── cross_validate.py    # Cross-validation
│   │   └── predict_terminal.py  # CLI prediction tool
│   │
│   ├── visualization/            # Visualizations
│   │   └── eda.py               # Exploratory data analysis
│   │
│   └── features/                 # Additional features
│       └── build_features.py     # Feature engineering
│
├── models/                       # Trained model artifacts
│   ├── xgboost_delay_model.pkl
│   ├── xgboost_tuned_model.pkl
│   └── label_encoders.pkl
│
├── templates/                    # Flask templates
│   ├── base.html                # Base template
│   ├── index.html               # Homepage with search
│   ├── prediction.html          # Prediction form page
│   └── schedule.html            # Service tracking page
│
├── static/                       # Static assets
│   └── css/
│       └── style.css            # Stylesheet
│
├── reports/                      # Generated reports
│   ├── figures/                 # EDA visualizations
│   └── eda_insights.md         # Analysis report
│
├── app.py                       # Main Flask application
├── requirements.txt             # Dependencies
└── README.md                    # Documentation
```

---

## 🔍 Identified Issues & Solutions

### 🔴 Issue 1: Duplicate Feature Engineering Code
**Location:** `src/data/build_features.py` AND `src/features/build_features.py`

**Problem:** Two separate files doing the same thing causes confusion

**Solution:** Keep one canonical version

---

### 🔴 Issue 2: Missing __init__.py Files
**Problem:** Python packages require `__init__.py` for proper module imports

**Files Needed:**
- `src/__init__.py`
- `src/data/__init__.py`
- `src/database/__init__.py`
- `src/models/__init__.py`
- `src/visualization/__init__.py`
- `src/features/__init__.py`

---

### 🔴 Issue 3: Database Schema Mismatch
**Problem:** Column name inconsistencies between:
- Database schema (snake_case): `from_location`, `to_location`
- Data files (PascalCase): `From_Location`, `To_Location`

**Impact:** Migration and query issues

---

### 🔴 Issue 4: Hardcoded Paths
**Problem:** Scattered hardcoded paths throughout the codebase

**Solution:** Centralized configuration file

---

### 🔴 Issue 5: No Main Pipeline Script
**Problem:** No single entry point to run the entire pipeline

**Solution:** Create `main.py` orchestrator

---

### 🔴 Issue 6: Missing Integration Tests
**Problem:** No way to verify end-to-end functionality

---

### 🔴 Issue 7: Environment Configuration
**Problem:** `.env.example` exists but no `.env` file

**Solution:** Create proper `.env` file

---

## 🔄 Data Flow Architecture

```
1. DATA GENERATION
   ├── src/data/make_dataset.py
   └── Output: data/raw/hyderabad_transport_raw.csv

2. DATA CLEANING
   ├── src/data/clean_data.py
   └── Output: data/processed/hyderabad_transport_cleaned.csv

3. FEATURE ENGINEERING
   ├── src/data/build_features.py
   └── Output: data/processed/hyderabad_transport_features.csv

4. MODEL TRAINING
   ├── src/models/train_model.py
   └── Output: models/xgboost_delay_model.pkl
              models/label_encoders.pkl

5. MODEL EVALUATION
   ├── src/models/evaluate_model.py
   └── Generates performance metrics

6. DATABASE MIGRATION
   ├── src/database/db_config.py (init schema)
   ├── src/database/migrate_data.py (load data)
   └── Output: data/transport.db

7. WEB APPLICATION
   ├── app.py (Flask server)
   ├── src/models/engine.py (Prediction engine)
   └── src/database/queries.py (DB queries)
```

---

## 🎯 API Endpoints

### Flask Routes:
1. `GET /` - Homepage (search form)
2. `POST /search` - Form-based search (returns HTML)
3. `POST /api/search` - JSON API search
4. `GET /track/<service_id>` - Service tracking page
5. `GET /api/track/<service_id>` - JSON tracking data
6. `GET /predict` - Prediction form page

---

## 📊 Database Schema

### Tables:

#### 1. `schedules`
Stores all transport schedules with contextual data
```sql
- id (PRIMARY KEY)
- date, transport_type, route_id, service_id
- from_location, to_location, stops
- scheduled_departure, scheduled_arrival
- actual_departure, actual_arrival
- delay_minutes, delay_reason
- weather, temperature_c, humidity_pct
- is_holiday, is_peak_hour, event_scheduled
- traffic_density, passenger_load, distance_km
```

#### 2. `predictions`
Audit log of all predictions made
```sql
- pred_id (PRIMARY KEY)
- timestamp
- from_location, to_location, transport_type
- scheduled_time
- predicted_delay, reason
```

---

## 🧠 ML Model Architecture

### Model: XGBoost Regressor

#### Features Used:
- **Transport Type** (Bus, Metro, Train)
- **Route** (From_Location, To_Location)
- **Weather** (Clear, Rainy, Foggy, etc.)
- **Temporal** (Is_Holiday, Is_Peak_Hour, Day_of_Week, Month, Dep_Hour)
- **External** (Event_Scheduled, Traffic_Density)
- **Environmental** (Temperature_C, Humidity_Pct)
- **Operational** (Passenger_Load, Distance_KM)
- **Engineered** (Weather_Traffic_Index, Is_Weekend)

#### Target:
- `Delay_Minutes` (continuous variable)

#### Performance:
- Stored in `reports/` after evaluation

---

## 🌐 Frontend Components

### Templates:
1. **base.html** - Layout with navbar, footer
2. **index.html** - Search form + results display
3. **prediction.html** - Alternative prediction interface
4. **schedule.html** - Live tracking with stops timeline

### Styling:
- Custom CSS in `static/css/style.css`
- Responsive design
- Modern UI with gradients and animations

---

## 🔧 Technology Stack

### Backend:
- Python 3.x
- Flask (Web framework)
- SQLite (Database)
- XGBoost (ML model)

### Data Processing:
- Pandas (Data manipulation)
- NumPy (Numerical operations)
- Scikit-learn (Preprocessing, metrics)

### Visualization:
- Matplotlib
- Seaborn

### Environment:
- python-dotenv (Config management)
- Joblib (Model serialization)

---

## 🚀 Deployment Considerations

### Current Setup:
- Development server (`debug=True`)
- Port 8000
- Local SQLite database

### Production Recommendations:
1. Use production WSGI server (Gunicorn/uWSGI)
2. Consider PostgreSQL for better concurrency
3. Add API rate limiting
4. Implement caching (Redis)
5. Add authentication for admin features
6. Set up proper logging
7. Environment-based configuration

---

## 📈 Next Steps (Priority Order)

### HIGH PRIORITY:
1. ✅ Fix module structure (add `__init__.py` files)
2. ✅ Standardize column naming (snake_case everywhere)
3. ✅ Create centralized configuration
4. ✅ Build main pipeline orchestrator
5. ✅ Remove duplicate code

### MEDIUM PRIORITY:
6. ✅ Add comprehensive logging
7. ✅ Create integration tests
8. ✅ Document API endpoints
9. ✅ Add error handling

### LOW PRIORITY:
10. Performance optimization
11. UI/UX enhancements
12. Additional features (SMS alerts, etc.)

---

## 🔗 Key Dependencies Between Components

```
app.py
  │
  ├─> src/database/queries.py (TransportDB)
  ├─> src/database/db_config.py (init_db)
  └─> src/models/engine.py (ENGINE)
        │
        ├─> models/xgboost_delay_model.pkl
        └─> models/label_encoders.pkl

TransportDB
  └─> data/transport.db

TransportEngine
  ├─> OpenWeather API (real-time weather)
  └─> ML model predictions
```

---

## 📝 Configuration Files

### Required:
- `.env` - API keys and environment variables
- `requirements.txt` - Python dependencies
- Database schema (embedded in `db_config.py`)

### Current Issues:
- ❌ No `.env` file (only `.env.example`)
- ✅ `requirements.txt` complete

---

## 🎓 Educational Value

This project demonstrates:
1. Complete ML pipeline (data → model → deployment)
2. Database design and ORM patterns
3. Web application development (Flask)
4. API design (REST endpoints)
5. Real-time data integration
6. Software architecture best practices

---

## 💡 Strengths of Current Implementation

✅ Well-organized directory structure  
✅ Separation of concerns (data/models/database)  
✅ Object-oriented design (classes for each component)  
✅ Dual interface (HTML forms + JSON API)  
✅ Real-time weather integration  
✅ Feature engineering pipeline  
✅ Model versioning (multiple model files)  
✅ Responsive web design  

---

## ⚠️ Areas Needing Improvement

🔴 Module initialization (`__init__.py`)  
🔴 Column naming consistency  
🔴 Duplicate code removal  
🔴 Centralized configuration  
🔴 Error handling  
🔴 Logging system  
🔴 Testing coverage  
🔴 Documentation  
🔴 Production readiness  

---

**End of Analysis**
