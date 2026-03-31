"""
tune_model.py — Hyperparameter Tuning
=======================================
Uses RandomizedSearchCV to find optimal XGBoost parameters.
Saves the tuned model separately from the base model.
"""

import pandas as pd
import os
import sys
import joblib
from pathlib import Path
from sklearn.model_selection import RandomizedSearchCV
from xgboost import XGBRegressor

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config


def hyperparameter_tuning():
    """Run randomized hyperparameter search on XGBoost."""
    data_path = str(config.FEATURES_DATA_FILE)
    encoder_path = str(config.LABEL_ENCODERS_PATH)

    print("Starting hyperparameter tuning...")

    df = pd.read_csv(data_path).sample(50000, random_state=config.RANDOM_STATE)
    encoders = joblib.load(encoder_path)

    features = config.MODEL_FEATURES.copy()
    X = df[features].copy()
    y = df[config.TARGET_VARIABLE]

    for col, le in encoders.items():
        if col in X.columns:
            X[col] = le.transform(X[col])

    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 6, 9],
        'learning_rate': [0.01, 0.1, 0.2],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }

    search = RandomizedSearchCV(
        XGBRegressor(random_state=config.RANDOM_STATE),
        param_distributions=param_grid,
        n_iter=10, cv=3,
        scoring='neg_mean_absolute_error',
        verbose=1, n_jobs=-1
    )

    search.fit(X, y)

    print(f"Best Parameters: {search.best_params_}")
    print(f"Best MAE: {-search.best_score_:.2f}")

    joblib.dump(search.best_estimator_, str(config.XGBOOST_TUNED_MODEL_PATH))
    print(f"Tuned model saved to: {config.XGBOOST_TUNED_MODEL_PATH}")


if __name__ == "__main__":
    hyperparameter_tuning()
