# 📊 EDA Report — Hyderabad Public Transport Delay Prediction

> Generated on: 2026-03-31 21:27:50

---

## 1. Dataset Overview

| Metric | Value |
|--------|-------|
| Total Records | 300,000 |
| Total Features | 29 |
| Memory Usage | 289.77 MB |
| Missing Values | 0 |
| Duplicate Rows | 0 |

## 2. Target Variable Analysis (Delay_Minutes)

| Statistic | Value |
|-----------|-------|
| Mean | 15.52 min |
| Median | 7.0 min |
| Std Deviation | 24.63 min |
| Min | 0 min |
| Max | 120 min |
| Skewness | 2.47 |
| Kurtosis | 5.69 |

### Delay Category Distribution
- **On Time (≤10 min):** 61.8%
- **Minor Delay (11-20 min):** 19.7%
- **Major Delay (>20 min):** 18.5%

## 3. Transport Type Analysis

| Transport Type | Avg Delay (min) |
|---------------|----------------|
| Bus | 15.76 |
| Metro | 15.56 |
| Train | 15.25 |

**Highest Average Delay:** Bus

## 4. Peak Hour Impact

- **Peak Hour Avg Delay:** 19.32 min
- **Off-Peak Avg Delay:** 12.77 min

## 5. Weather Impact

- **Worst Weather Condition:** Rainy
- **Avg Delay in Worst Weather:** 19.15 min

## 6. Traffic Density Impact

| Traffic Level | Avg Delay (min) |
|--------------|----------------|
| High | 19.24 |
| Low | 12.87 |
| Medium | 15.4 |

## 7. Temporal Patterns

- **Worst Hour of Day:** 17:00
- **Delay at Worst Hour:** 19.7 min

## 8. Holiday Impact

- **Holiday Avg Delay:** 15.79 min
- **Non-Holiday Avg Delay:** 15.42 min

## 9. Top Features Correlated with Delay

| Feature | Correlation |
|---------|------------|
| Is_Peak_Hour | 0.131 |
| Passenger_Load | 0.096 |
| Weather_Traffic_Index | 0.09 |
| Event_Scheduled | 0.046 |
| Day_of_Week | 0.008 |

## 10. Passenger Load Correlation

- **Passenger Load ↔ Delay Correlation:** 0.096

---

## Visualizations Generated

All figures are saved in `reports/figures/`:

1. `01_delay_distribution.png` — Delay histogram, KDE, and box plot
2. `02_delay_by_transport.png` — Box + Violin plots by transport type
3. `03_peak_hour_impact.png` — Peak vs off-peak comparison
4. `04_weather_impact.png` — Average delay by weather condition
5. `05_traffic_impact.png` — Violin plot by traffic density
6. `06_correlation_heatmap.png` — Feature correlation matrix
7. `07_hourly_delay_pattern.png` — Hour-of-day delay analysis
8. `08_day_of_week.png` — Day-of-week delay comparison
9. `09_holiday_impact.png` — Holiday vs non-holiday analysis
10. `10_top_delayed_routes.png` — Top 10 most delayed routes
11. `11_delay_categories.png` — Pie chart of delay categories
12. `12_passenger_vs_delay.png` — Passenger load vs delay scatter