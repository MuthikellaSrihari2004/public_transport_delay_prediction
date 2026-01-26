import pandas as pd
import numpy as np
import os

class FeatureEngineer:
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.df = None

    def load_data(self):
        print(f"Loading cleaned data from {self.input_path}...")
        self.df = pd.read_csv(self.input_path)
        return self

    def create_features(self):
        print("⚡ Generating synthetic features...")
        
        # 1. Weather-Traffic Index (Interaction Feature)
        # Map categorical to numeric weights
        weather_map = {
            'Clear': 1, 'Sunny': 1, 'Mainly Clear': 1, 
            'Partly Cloudy': 2, 'Cloudy': 2, 'Overcast': 3, 
            'Foggy': 4, 'Mist': 4, 
            'Rainy': 5, 'Light Rain': 5, 'Drizzle': 5, 'Heavy Rain': 6
        }
        
        traffic_map = {
            'Low': 1, 
            'Medium': 2, 
            'High': 3, 
            'Very High': 4
        }
        
        # Apply mapping
        self.df['Weather_Score'] = self.df['Weather'].map(weather_map).fillna(2)
        self.df['Traffic_Score'] = self.df['Traffic_Density'].map(traffic_map).fillna(2)
        
        # Interaction: Bad weather * High traffic = Exponential Delay Risk
        self.df['Weather_Traffic_Index'] = self.df['Weather_Score'] * self.df['Traffic_Score']
        
        # 2. Extract Temporal Features
        if 'Date' in self.df.columns:
            self.df['Date'] = pd.to_datetime(self.df['Date'])
            self.df['Month'] = self.df['Date'].dt.month
            self.df['Day_of_Week'] = self.df['Date'].dt.dayofweek
            self.df['Is_Weekend'] = (self.df['Day_of_Week'] >= 5).astype(int)
        
        # 3. Departure Hour
        # Safe extraction from HH:MM string
        def extract_hour(t_str):
            try:
                return int(str(t_str).split(':')[0])
            except:
                return 8 # Default to morning peak
        
        self.df['Dep_Hour'] = self.df['Scheduled_Departure'].apply(extract_hour)
        
        return self

    def save_features(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        self.df.to_csv(self.output_path, index=False)
        print(f"✅ Feature set saved to: {self.output_path}")
        print(f"   Columns: {list(self.df.columns)[-5:]} ...")

if __name__ == "__main__":
    input_file = 'data/processed/hyderabad_transport_cleaned.csv'
    output_file = 'data/processed/hyderabad_transport_features.csv'
    
    if os.path.exists(input_file):
        fe = FeatureEngineer(input_file, output_file)
        fe.load_data().create_features().save_features()
    else:
        print(f"❌ Error: Input file not found {input_file}. Run clean_data.py first.")
