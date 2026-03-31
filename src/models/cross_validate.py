"""
cross_validate.py — K-Fold Cross Validation
=============================================
Validates XGBoost model stability using 5-fold cross validation.
Reports per-fold MAE scores and standard deviation.
"""

import pandas as pd
import os
import sys
import joblib
from pathlib import Path
from sklearn.model_selection import cross_val_score
from xgboost import XGBRegressor

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config


def validate_model():
    """Run 5-fold cross validation on a sample of the dataset."""
    data_path = str(config.FEATURES_DATA_FILE)
    encoder_path = str(config.LABEL_ENCODERS_PATH)

    print("Running 5-fold cross validation...")

    df = pd.read_csv(data_path).sample(20000, random_state=config.RANDOM_STATE)
    encoders = joblib.load(encoder_path)

    features = config.MODEL_FEATURES.copy()
    X = df[features].copy()
    y = df[config.TARGET_VARIABLE]

    for col, le in encoders.items():
        if col in X.columns:
            X[col] = le.transform(X[col])

    model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6,
                         random_state=config.RANDOM_STATE)
    scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_absolute_error')

    print(f"MAE per fold : {-scores}")
    print(f"Average MAE  : {-scores.mean():.2f}")
    print(f"Std Dev      : {scores.std():.2f}")


if __name__ == "__main__":
    validate_model()
