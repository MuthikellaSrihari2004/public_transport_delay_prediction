"""
build_features.py — Feature Engineering
=========================================
Creates derived features from cleaned data:
  - Weather-Traffic interaction index
  - Temporal features (month, day of week, weekend flag)
  - Departure hour extraction
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config


class FeatureEngineer:
    """Chain-style feature engineering: load → create → save."""

    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.df = None

    def load_data(self):
        print(f"Loading cleaned data from {self.input_path}...")
        self.df = pd.read_csv(self.input_path)
        return self

    def create_features(self):
        print("Creating features...")

        # Weather severity score
        weather_map = {
            'Clear': 1, 'Sunny': 1, 'Mainly Clear': 1,
            'Partly Cloudy': 2, 'Cloudy': 2, 'Overcast': 3,
            'Foggy': 4, 'Mist': 4,
            'Rainy': 5, 'Light Rain': 5, 'Drizzle': 5, 'Heavy Rain': 6
        }

        # Traffic severity score
        traffic_map = {'Low': 1, 'Medium': 2, 'High': 3, 'Very High': 4}

        self.df['Weather_Score'] = self.df['Weather'].map(weather_map).fillna(2)
        self.df['Traffic_Score'] = self.df['Traffic_Density'].map(traffic_map).fillna(2)

        # Interaction feature: bad weather × high traffic = higher delay risk
        self.df['Weather_Traffic_Index'] = self.df['Weather_Score'] * self.df['Traffic_Score']

        # Temporal features
        if 'Date' in self.df.columns:
            self.df['Date'] = pd.to_datetime(self.df['Date'])
            self.df['Month'] = self.df['Date'].dt.month
            self.df['Day_of_Week'] = self.df['Date'].dt.dayofweek
            self.df['Is_Weekend'] = (self.df['Day_of_Week'] >= 5).astype(int)

        # Departure hour
        def extract_hour(time_str):
            try:
                return int(str(time_str).split(':')[0])
            except (ValueError, IndexError):
                return 8

        self.df['Dep_Hour'] = self.df['Scheduled_Departure'].apply(extract_hour)

        print(f"New features: Weather_Traffic_Index, Month, Day_of_Week, Is_Weekend, Dep_Hour")
        return self

    def save_features(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        self.df.to_csv(self.output_path, index=False)
        print(f"Features saved to: {self.output_path}")


if __name__ == "__main__":
    input_file = str(config.CLEANED_DATA_FILE)
    output_file = str(config.FEATURES_DATA_FILE)

    if os.path.exists(input_file):
        fe = FeatureEngineer(input_file, output_file)
        fe.load_data().create_features().save_features()
    else:
        print(f"Error: {input_file} not found. Run clean_data.py first.")
