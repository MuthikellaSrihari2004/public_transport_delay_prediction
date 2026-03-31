"""
train_model.py — Model Training & Comparison
==============================================
Trains XGBoost, Decision Tree, and Linear Regression.
Compares all three and selects the best performer (XGBoost).
"""

import pandas as pd
import numpy as np
import os
import sys
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, f1_score
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config


class AdvancedModelTrainer:
    """Train and compare multiple regression models for delay prediction."""

    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.label_encoders = {}
        self.model = None

    def load_data(self):
        print(f"Loading dataset: {self.data_path}")
        self.df = pd.read_csv(self.data_path)

        # Downsample for speed if dataset is very large
        if len(self.df) > 500000:
            print(f"Downsampling from {len(self.df):,} to 250,000 rows...")
            self.df = self.df.sample(n=250000, random_state=config.RANDOM_STATE)

        print(f"Data loaded: {self.df.shape[0]:,} rows")
        return self

    def preprocess(self):
        print("Preprocessing features...")

        features = config.MODEL_FEATURES.copy()
        for feat in config.OPTIONAL_FEATURES:
            if feat in self.df.columns:
                features.append(feat)

        X = self.df[features].copy()
        y = self.df[config.TARGET_VARIABLE]

        # Encode categorical columns
        for col in X.select_dtypes(include=['object']).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            self.label_encoders[col] = le

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE
        )
        return self

    def train_and_compare(self):
        print(f"\n{'='*80}")
        print("  MODEL COMPARISON")
        print(f"{'='*80}")

        models = {
            "Linear Regression": LinearRegression(),
            "Decision Tree": DecisionTreeRegressor(max_depth=10, random_state=config.RANDOM_STATE),
            "XGBoost": XGBRegressor(
                n_estimators=50, learning_rate=0.1, max_depth=6,
                subsample=0.8, colsample_bytree=0.8,
                n_jobs=-1, random_state=config.RANDOM_STATE
            )
        }

        print(f"{'Model':<20} | {'MAE':<8} | {'RMSE':<8} | {'R2':<8} | {'Acc%':<8} | {'F1':<8}")
        print("-" * 80)

        for name, model in models.items():
            model.fit(self.X_train, self.y_train)
            preds = model.predict(self.X_test)

            # Regression metrics
            mae = mean_absolute_error(self.y_test, preds)
            rmse = np.sqrt(mean_squared_error(self.y_test, preds))
            r2 = r2_score(self.y_test, preds)

            # Classification metrics (threshold: >5 min = delayed)
            y_cls = (self.y_test > 5).astype(int)
            p_cls = (preds > 5).astype(int)
            acc = accuracy_score(y_cls, p_cls) * 100
            f1 = f1_score(y_cls, p_cls, zero_division=0)

            print(f"{name:<20} | {mae:<8.2f} | {rmse:<8.2f} | {r2:<8.4f} | {acc:<8.1f} | {f1:<8.3f}")

            if "XGBoost" in name:
                self.model = model

        print("-" * 80)
        print("Selected: XGBoost")
        return self

    def save(self):
        os.makedirs(str(config.MODELS_DIR), exist_ok=True)
        joblib.dump(self.model, str(config.XGBOOST_MODEL_PATH))
        joblib.dump(self.label_encoders, str(config.LABEL_ENCODERS_PATH))
        print(f"Model saved to: {config.XGBOOST_MODEL_PATH}")


if __name__ == "__main__":
    data_path = str(config.FEATURES_DATA_FILE)
    if os.path.exists(data_path):
        trainer = AdvancedModelTrainer(data_path)
        trainer.load_data().preprocess().train_and_compare().save()
