# HyderTrax - Hyderabad Public Transport Delay Prediction System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![XGBoost](https://img.shields.io/badge/xgboost-latest-orange.svg)](https://xgboost.readthedocs.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **An intelligent ML-powered web application for predicting public transport delays in Hyderabad**

## 🎯 Overview

HyderTrax is a comprehensive data-driven machine learning solution that predicts transit delay durations for buses, metro, and trains in Hyderabad. The system integrates historical transport data, real-time weather information, traffic patterns, and event schedules to provide accurate delay predictions.

### Key Features

- ✅ **Real-time Delay Predictions** - Get instant predictions for any route
- ✅ **Multi-modal Transport** - Supports Bus, Metro, and Train services
- ✅ **Live Tracking** - Track services with stop-by-stop ETA updates
- ✅ **Weather Integration** - Real-time weather data from OpenWeather API
- ✅ **Historical Analysis** - Comprehensive EDA and visualization reports
- ✅ **RESTful API** - JSON API for third-party integrations
- ✅ **Modern Web UI** - Responsive, user-friendly interface

---

## 📂 Project Structure

```
project/
├── config.py                    # Centralized configuration
├── main.py                      # Main pipeline orchestrator
├── app.py                       # Flask web application
│
├── src/                         # Source code
│   ├── data/                    # Data pipeline
│   │   ├── make_dataset.py     # Synthetic data generation
│   │   ├── clean_data.py       # Data cleaning pipeline
│   │   └── build_features.py   # Feature engineering
│   │
│   ├── database/                # Database layer
│   │   ├── db_config.py        # Schema & initialization
│   │   ├── queries.py          # Query utilities
│   │   └── migrate_data.py     # CSV to DB migration
│   │
│   ├── models/                  # ML models
│   │   ├── engine.py           # Prediction engine
│   │   ├── train_model.py      # Model training
│   │   ├── evaluate_model.py   # Model evaluation
│   │   └── predict_terminal.py # CLI predictions
│   │
│   └── visualization/           # Data visualization
│       └── eda.py              # Exploratory data analysis
│
├── data/                        # Data storage
│   ├── raw/                    # Raw generated data
│   ├── processed/              # Cleaned & engineered data
│   └── transport.db           # SQLite database
│
├── models/                      # Trained ML models
│   ├── xgboost_delay_model.pkl
│   └── label_encoders.pkl
│
├── templates/                   # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── prediction.html
│   └── schedule.html
│
├── static/                      # Static assets
│   └── css/
│       └── style.css
│
└── reports/                     # Generated reports
    ├── figures/                # EDA visualizations
    └── eda_insights.md        # Analysis report
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) OpenWeather API key for real-time weather

### Installation

1. **Clone the repository** (or navigate to project directory)
   ```bash
   cd c:\Users\msrih\Documents\project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment**
   - The `.env` file already exists with default values
   - (Optional) Add your OpenWeather API key:
     ```bash
     # Edit .env file
     OPENWEATHER_API_KEY=your_actual_api_key_here
     ```

6. **Run the complete pipeline**
   ```bash
   python main.py
   ```
   This will:
   - Generate synthetic transport data
   - Clean and process the data
   - Engineer features
   - Train the ML model
   - Initialize the database
   - Migrate data to database

7. **Start the web application**
   ```bash
   python app.py
   ```

8. **Open your browser**
   Navigate to: http://localhost:8000

---

## 📖 Usage

### Running the Complete Pipeline

```bash
# Run entire pipeline
python main.py

# Force regenerate all data and models
python main.py --force

# Skip specific steps
python main.py --skip-data          # Skip data generation
python main.py --skip-training      # Skip model training

# Run only database operations
python main.py --only-database
```

### Starting the Web Application

```bash
python app.py
```

The application will start on `http://localhost:8000`

### Using the CLI Prediction Tool

```bash
python src/models/predict_terminal.py
```

---

## 🌐 Web Interface

### Pages

1. **Homepage (`/`)**
   - Search form for route-based predictions
   - Displays all available services with delay predictions
   - Shows real-time weather and environmental context

2. **Prediction Page (`/predict`)**
   - Interactive prediction form
   - JSON API-powered results
   - Detailed delay insights

3. **Tracking Page (`/track/<service_id>`)**
   - Live service tracking
   - Stop-by-stop timeline
   - Real-time ETA updates

---

## 🔌 API Endpoints

### 1. Search Services (Form-based)

**Endpoint:** `POST /search`  
**Content-Type:** `application/x-www-form-urlencoded`

**Request:**
```
from_location=Secunderabad
to_location=Hitech City
travel_date=2026-01-26
transport_type=Bus
```

**Response:** HTML page with results

---

### 2. Search Services (JSON API)

**Endpoint:** `POST /api/search`  
**Content-Type:** `application/json`

**Request:**
```json
{
  "from": "Secunderabad",
  "to": "Hitech City",
  "date": "2026-01-26",
  "type": "Metro"
}
```

**Response:**
```json
{
  "schedules": [
    {
      "Service_ID": "METRO_001",
      "Scheduled_Departure": "09:00",
      "id": 1
    }
  ],
  "representative_insight": {
    "predicted_delay": 12,
    "delay_category": "Minor Delay",
    "confidence_score": 0.85,
    "primary_reason": "Heavy traffic conditions"
  }
}
```

---

### 3. Track Service (JSON API)

**Endpoint:** `GET /api/track/<service_id>?date=2026-01-26`

**Response:**
```json
{
  "service": { ... },
  "info": {
    "Service_ID": "BUS_042",
    "Start_Time": "09:02",
    "Reach_Time": "10:25"
  },
  "insights": {
    "predicted_delay": 15,
    "delay_category": "Minor Delay",
    "primary_reason": "Peak hour traffic"
  },
  "stops": [
    {
      "name": "Secunderabad",
      "est": "09:02",
      "sched": "09:00",
      "status": "Departed",
      "is_current": false
    }
  ]
}
```

---

## 🧠 Machine Learning Model

### Model Architecture

- **Algorithm:** XGBoost Regressor
- **Target Variable:** Delay (in minutes)
- **Features:** 15+ features including transport type, route, weather, traffic, temporal patterns

### Features Used

**Categorical:**
- Transport Type (Bus, Metro, Train)
- From/To Locations
- Weather Condition
- Traffic Density

**Numerical:**
- Temperature (°C)
- Humidity (%)
- Passenger Load
- Distance (km)
- Hour of Day
- Day of Week

**Engineered:**
- Weather-Traffic Interaction Index
- Is Weekend
- Is Peak Hour

### Performance Metrics

See `reports/` directory after running evaluation.

---

## 🗄️ Database Schema

### Tables

#### `schedules`
Stores all transport schedules with contextual information

```sql
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY,
    date TEXT,
    transport_type TEXT,
    from_location TEXT,
    to_location TEXT,
    scheduled_departure TEXT,
    delay_minutes INTEGER,
    weather TEXT,
    temperature_c REAL,
    is_holiday INTEGER,
    is_peak_hour INTEGER,
    traffic_density TEXT,
    -- ... and more
);
```

#### `predictions`
Audit log of all predictions made

```sql
CREATE TABLE predictions (
    pred_id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    from_location TEXT,
    to_location TEXT,
    predicted_delay INTEGER,
    reason TEXT
);
```

---

## 🛠️ Configuration

All configuration is centralized in `config.py`:

- **Paths:** Data directories, model paths, database location
- **API Keys:** OpenWeather, Traffic APIs
- **Model Parameters:** Training hyperparameters
- **Flask Settings:** Debug mode, port, host

---

## 🔧 Development

### Running Tests

```bash
# Create tests directory if it doesn't exist
mkdir tests

# Run tests (when available)
pytest tests/
```

### Viewing Logs

Logs are stored in `logs/hydertrax.log`

---

## 📊 Data Pipeline

```
1. Data Generation (make_dataset.py)
   ↓
2. Data Cleaning (clean_data.py)
   ↓
3. Feature Engineering (build_features.py)
   ↓
4. Model Training (train_model.py)
   ↓
5. Model Evaluation (evaluate_model.py)
   ↓
6. Database Setup (db_config.py)
   ↓
7. Data Migration (migrate_data.py)
   ↓
8. Web Application (app.py)
```

---

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError

**Solution:** Ensure you're in the project root and virtual environment is activated
```bash
cd c:\Users\msrih\Documents\project
venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Issue: Database not found

**Solution:** Run the pipeline to initialize
```bash
python main.py --only-database
```

### Issue: Model file not found

**Solution:** Train the model
```bash
python main.py --skip-data --skip-cleaning --skip-features
```

### Issue: API key warnings

**Solution:** Add your OpenWeather API key to `.env`
```
OPENWEATHER_API_KEY=your_key_here
```

---

## 📝 License

This project is licensed under the MIT License.

---

## 👥 Contributors

- Transport Analytics Team

---

## 📧 Support

For issues and questions, please check:
1. `PROJECT_ANALYSIS.md` - Detailed architecture analysis
2. `IMPLEMENTATION_PLAN.md` - Development roadmap

---

## 🎓 Academic Use

This project demonstrates:
- Complete ML pipeline (data → model → deployment)
- RESTful API design
- Database design and migrations
- Real-time data integration
- Modern web application development
- Software engineering best practices

Perfect for final year projects, ML portfolios, and learning full-stack ML development!

---

**Built with ❤️ for Hyderabad's commuters**
