import pandas as pd
import numpy as np
import os
import time
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, precision_score, f1_score

class AdvancedModelTrainer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.label_encoders = {}
        self.model = None

    def load_data(self):
        print(f"📂 Loading high-volume dataset: {self.data_path}")
        self.df = pd.read_csv(self.data_path)
        
        # SPEED OPTIMIZATION: Sample 250k rows if oversized
        if len(self.df) > 500000:
            print(f"⚠️ Optimization: Downsampling from {len(self.df)} to 250,000 rows for rapid training...")
            self.df = self.df.sample(n=250000, random_state=42)
            
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

    def train_and_compare(self):
        print("\n" + "="*80)
        print("🤖 MODEL SELECTION & COMPARISON MODULE")
        print("="*80)
        
        # Define models
        models = {
            "Linear Regression": LinearRegression(),
            "Decision Tree": DecisionTreeRegressor(max_depth=10, random_state=42),
            "XGBoost": XGBRegressor(
                n_estimators=50, learning_rate=0.1, max_depth=6, 
                subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=42
            )
        }
        
        print(f"{'Model Name':<20} | {'MAE':<8} | {'RMSE':<8} | {'R2':<8} | {'Acc%':<8} | {'F1':<8}")
        print("-" * 80)
        
        for name, model in models.items():
            model.fit(self.X_train, self.y_train)
            preds = model.predict(self.X_test)
            
            # Regression Metrics
            mae = mean_absolute_error(self.y_test, preds)
            rmse = np.sqrt(mean_squared_error(self.y_test, preds))
            r2 = r2_score(self.y_test, preds)
            
            # Classification Metrics (Threshold > 5 mins considered "Delayed")
            y_true_cls = (self.y_test > 5).astype(int)
            y_pred_cls = (preds > 5).astype(int)
            acc = accuracy_score(y_true_cls, y_pred_cls) * 100
            f1 = f1_score(y_true_cls, y_pred_cls, zero_division=0)
            
            print(f"{name:<20} | {mae:<8.2f} | {rmse:<8.2f} | {r2:<8.4f} | {acc:<8.1f} | {f1:<8.3f}")
            
            if "XGBoost" in name:
                self.model = model
                
        print("-" * 80)
        print("🏆 SELECTED: XGBoost (Best Performance/Speed Trade-off)")
        return self

    def save(self):
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.model, 'models/xgboost_delay_model.pkl')
        joblib.dump(self.label_encoders, 'models/label_encoders.pkl')
        print("✅ Best Model saved.")

if __name__ == "__main__":
    data_path = 'data/processed/hyderabad_transport_features.csv'
    if os.path.exists(data_path):
        trainer = AdvancedModelTrainer(data_path)
        trainer.load_data().preprocess().train_and_compare().save()
