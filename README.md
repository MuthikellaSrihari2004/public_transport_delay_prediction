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
- ✅ **Weather Integration** - Real-time weather data from Open-Meteo API
- ✅ **Exploratory Data Analysis** - 12+ EDA visualizations with auto-generated insights report
- ✅ **Interactive Map** - Live route map with autocomplete location search
- ✅ **RESTful API** - JSON API for third-party integrations
- ✅ **Modern Web UI** - Responsive, premium interface

---

## 📂 Project Structure

```
project/
├── config.py                    # Centralized configuration
├── main.py                      # Main pipeline orchestrator (7-step)
├── app.py                       # Flask web application
├── create_deploy_db.py          # Deployment database builder
│
├── src/                         # Source code
│   ├── data/                    # Data pipeline
│   │   ├── make_dataset.py     # Synthetic data generation
│   │   ├── clean_data.py       # Data cleaning pipeline
│   │   └── build_features.py   # Feature engineering
│   │
│   ├── database/                # Database layer
│   │   ├── db_config.py        # Schema & initialization
│   │   └── queries.py          # Query utilities
│   │
│   ├── models/                  # ML models
│   │   ├── engine.py           # Prediction engine (core)
│   │   ├── train_model.py      # Model training & comparison
│   │   ├── evaluate_model.py   # Model evaluation
│   │   ├── tune_model.py       # Hyperparameter tuning
│   │   ├── cross_validate.py   # Cross-validation
│   │   └── predict_terminal.py # CLI predictions
│   │
│   └── visualization/           # Data visualization
│       └── eda.py              # Comprehensive EDA (12 plots + report)
│
├── data/                        # Data storage
│   ├── raw/                    # Raw generated data
│   ├── processed/              # Cleaned & feature-engineered data
│   └── transport.db            # SQLite deployment database
│
├── models/                      # Trained ML models
│   ├── xgboost_delay_model.pkl
│   ├── xgboost_tuned_model.pkl
│   └── label_encoders.pkl
│
├── templates/                   # HTML templates
│   ├── base.html               # Base layout
│   ├── index.html              # Homepage + search results
│   ├── prediction.html         # Prediction page
│   ├── schedule.html           # Service tracking page
│   ├── map.html                # Interactive route map
│   └── analytics.html          # Analytics dashboard
│
├── static/css/style.css         # Stylesheet
│
├── reports/                     # Generated reports
│   ├── figures/                # EDA visualizations (12 PNG files)
│   └── eda_insights.md         # Auto-generated analysis report
│
└── documents/                   # Project documents
    ├── Research_Paper.pdf
    ├── project report.pdf
    └── project presentation.pptx
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the complete pipeline**
   ```bash
   python main.py
   ```
   This will:
   - Generate synthetic transport data
   - Clean and process the data
   - Engineer features
   - **Run Exploratory Data Analysis (EDA)**
   - Train & compare ML models
   - Evaluate model performance
   - Create deployment database

5. **Start the web application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to: http://localhost:8000

---

## 📊 Data Pipeline (7 Steps)

```
Step 1: Data Generation         → src/data/make_dataset.py
   ↓
Step 2: Data Cleaning           → src/data/clean_data.py
   ↓
Step 3: Feature Engineering     → src/data/build_features.py
   ↓
Step 4: EDA & Visualization     → src/visualization/eda.py
   ↓
Step 5: Model Training          → src/models/train_model.py
   ↓
Step 6: Model Evaluation        → src/models/evaluate_model.py
   ↓
Step 7: Deployment DB           → create_deploy_db.py
   ↓
        Web Application         → app.py
```

---

## 📊 Exploratory Data Analysis (EDA)

The EDA module (`src/visualization/eda.py`) performs comprehensive analysis:

### Visualizations Generated (12 figures)

| # | Figure | Description |
|---|--------|-------------|
| 1 | `01_delay_distribution.png` | Histogram + KDE + Box plot of delays |
| 2 | `02_delay_by_transport.png` | Box + Violin plots by transport type |
| 3 | `03_peak_hour_impact.png` | Peak vs off-peak hour comparison |
| 4 | `04_weather_impact.png` | Average delay by weather condition |
| 5 | `05_traffic_impact.png` | Violin plot by traffic density |
| 6 | `06_correlation_heatmap.png` | Feature correlation matrix |
| 7 | `07_hourly_delay_pattern.png` | Hour-of-day delay analysis |
| 8 | `08_day_of_week.png` | Day-of-week delay comparison |
| 9 | `09_holiday_impact.png` | Holiday vs non-holiday analysis |
| 10 | `10_top_delayed_routes.png` | Top 10 most delayed routes |
| 11 | `11_delay_categories.png` | Pie chart of delay categories |
| 12 | `12_passenger_vs_delay.png` | Passenger load vs delay scatter |

### Auto-Generated Report

After EDA runs, a detailed markdown report is saved to `reports/eda_insights.md` with:
- Dataset overview statistics
- Target variable analysis (mean, median, skewness, kurtosis)
- Delay category distribution
- Transport type breakdown
- Peak hour, weather, traffic, and holiday impact analysis
- Top correlated features

### Running EDA Standalone

```bash
python src/visualization/eda.py
```

---

## 🌐 Web Interface

### Pages

1. **Homepage (`/`)** - Route search with delay predictions
2. **Prediction Page (`/predict`)** - Interactive prediction form
3. **Tracking Page (`/track/<id>`)** - Live service tracking with stop timeline
4. **Map Page (`/map`)** - Interactive route map with autocomplete
5. **Analytics (`/analytics`)** - Analytics dashboard

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/search` | Search services (form-based, returns HTML) |
| `POST` | `/api/search` | Search services (JSON API) |
| `GET` | `/api/track/<id>` | Track a service (JSON) |
| `POST` | `/api/route` | Get route details (JSON) |
| `GET` | `/api/locations` | Get all locations for autocomplete |

---

## 🧠 Machine Learning Model

### Model Architecture

- **Algorithm:** XGBoost Regressor (selected via comparison with Linear Regression and Decision Tree)
- **Target Variable:** Delay (in minutes)
- **Features:** 17 features including transport type, route, weather, traffic, temporal patterns

### Features Used

| Category | Features |
|----------|----------|
| **Categorical** | Transport_Type, From/To_Location, Weather, Traffic_Density |
| **Numerical** | Temperature_C, Humidity_Pct, Passenger_Load, Distance_KM, Dep_Hour, Day_of_Week |
| **Engineered** | Weather_Traffic_Index, Is_Weekend, Is_Peak_Hour, Month |
| **Binary Flags** | Is_Holiday, Event_Scheduled |

---

## 🛠️ Configuration

All configuration is centralized in `config.py`:

- **Paths:** Data directories, model paths, database location
- **API Keys:** Weather, Traffic, Event APIs (optional)
- **Model Parameters:** XGBoost hyperparameters
- **Flask Settings:** Debug mode, port, host

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Activate venv and `pip install -r requirements.txt` |
| Database not found | Run `python main.py` to initialize |
| Model file not found | Run `python main.py` to train |
| Weather data unavailable | System uses simulated fallback automatically |

---

## 🎓 Academic Use

This project demonstrates:
- Complete ML pipeline (data → EDA → model → deployment)
- Exploratory Data Analysis with statistical visualizations
- RESTful API design
- Database design with SQLite
- Real-time external API integration
- Modern web application development
- Software engineering best practices

---

## 📝 License

This project is licensed under the MIT License.

---

**Built with ❤️ for Hyderabad's commuters**
