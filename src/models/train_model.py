import pandas as pd
import numpy as np
import os
import time
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class AdvancedModelTrainer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.label_encoders = {}
        self.model = None

    def load_data(self):
        print(f"📂 Loading high-volume dataset: {self.data_path}")
        self.df = pd.read_csv(self.data_path)
        print(f"✅ Data loaded: {self.df.shape[0]} rows")
        return self

    def preprocess(self):
        print("🛠️  Preprocessing features for XGBoost...")
        
        # Core features
        features = [
            'Transport_Type', 'From_Location', 'To_Location', 'Weather', 
            'Is_Holiday', 'Is_Peak_Hour', 'Event_Scheduled', 'Traffic_Density',
            'Temperature_C', 'Humidity_Pct', 'Passenger_Load', 'Distance_KM',
            'Dep_Hour', 'Day_of_Week', 'Weather_Traffic_Index'
        ]
        
        # Add temporal features 
        optional_features = ['Month', 'Is_Weekend']
        for feat in optional_features:
            if feat in self.df.columns:
                features.append(feat)
                
        target = 'Delay_Minutes'
        
        X = self.df[features].copy()
        y = self.df[target]
        
        # Categorical Encoding
        cat_cols = X.select_dtypes(include=['object']).columns
        for col in cat_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            self.label_encoders[col] = le
            
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        return self

    def train_xgboost(self):
        print("\n🚀 Training Optimized Regressor...")
        start_time = time.time()
        
        self.model = XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=8,
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=-1,
            random_state=42
        )
        
        self.model.fit(
            self.X_train, self.y_train,
            eval_set=[(self.X_test, self.y_test)],
            verbose=False
        )
        
        print(f"✨ Training completed in {time.time() - start_time:.2f}s")
        return self

    def save(self):
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.model, 'models/xgboost_delay_model.pkl')
        joblib.dump(self.label_encoders, 'models/label_encoders.pkl')
        print("✅ Models saved.")

if __name__ == "__main__":
    data_path = 'data/processed/hyderabad_transport_features.csv'
    if os.path.exists(data_path):
        trainer = AdvancedModelTrainer(data_path)
        trainer.load_data().preprocess().train_xgboost().save()
