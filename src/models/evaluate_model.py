"""
evaluate_model.py — Model Evaluation
======================================
Evaluates the trained XGBoost model on the dataset and
reports MAE, RMSE, R2, and feature importances.
"""

import pandas as pd
import numpy as np
import os
import sys
import joblib
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config


def evaluate_model(data_path=None, model_path=None, encoder_path=None):
    """Evaluate trained model and print performance metrics."""
    d_path = str(data_path or config.FEATURES_DATA_FILE)
    m_path = str(model_path or config.XGBOOST_MODEL_PATH)
    e_path = str(encoder_path or config.LABEL_ENCODERS_PATH)

    if not os.path.exists(m_path) or not os.path.exists(e_path):
        print("Error: Model artifacts not found. Run train_model.py first.")
        return

    if not os.path.exists(d_path):
        print(f"Error: Data not found at {d_path}")
        return

    # Load data and model
    df = pd.read_csv(d_path)
    if len(df) > 500000:
        print(f"Sampling 100,000 rows from {len(df):,} for evaluation...")
        df = df.sample(n=100000, random_state=config.RANDOM_STATE)

    model = joblib.load(m_path)
    encoders = joblib.load(e_path)

    # Prepare features
    features = config.MODEL_FEATURES.copy()
    for feat in config.OPTIONAL_FEATURES:
        if feat in df.columns:
            features.append(feat)
    features = [f for f in features if f in df.columns]

    X = df[features].copy()
    y = df[config.TARGET_VARIABLE]

    # Encode categorical features
    for col, le in encoders.items():
        if col in X.columns:
            X[col] = X[col].map(lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else 0)

    preds = model.predict(X)

    # Print metrics
    mae = mean_absolute_error(y, preds)
    rmse = np.sqrt(mean_squared_error(y, preds))
    r2 = r2_score(y, preds)

    print(f"\n{'='*50}")
    print("  MODEL EVALUATION RESULTS")
    print(f"{'='*50}")
    print(f"Records Evaluated : {len(df):,}")
    print(f"MAE               : {mae:.2f} min")
    print(f"RMSE              : {rmse:.2f} min")
    print(f"R2 Score          : {r2:.4f}")

    # Feature importance
    try:
        importance = model.feature_importances_
        feat_imp = pd.Series(importance, index=X.columns).sort_values(ascending=False)
        print(f"\nTop 10 Feature Importances:")
        print(feat_imp.head(10).to_string())
    except Exception:
        pass

    print(f"{'='*50}")


if __name__ == "__main__":
    evaluate_model()
