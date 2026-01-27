import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config

def evaluate_model(data_path=None, model_path=None, encoder_path=None):
    """Evaluate trained XGBoost model on the provided dataset"""
    print("\n🔍 --- HyderTrax Model Evaluation ---")
    
    # Defaults from config
    d_path = data_path or str(config.FEATURES_DATA_FILE)
    m_path = model_path or str(config.XGBOOST_MODEL_PATH)
    e_path = encoder_path or str(config.LABEL_ENCODERS_PATH)
    
    if not os.path.exists(m_path) or not os.path.exists(e_path):
        print("❌ Error: Model artifacts not found. Run train_model.py first.")
        return
        
    if not os.path.exists(d_path):
        print(f"❌ Error: Evaluation data not found at {d_path}")
        return

    # Load artifacts
    try:
        # Optimization: Read only a sample/tail if file is huge, or read all then sample
        # Reading full CSV is slow, but random sampling requires reading. 
        # For speed, we'll read, but process only a sample.
        df = pd.read_csv(d_path)
        
        # SPEED OPTIMIZATION: Sample 100k rows if dataset > 500k
        if len(df) > 500000:
            print(f"⚠️ Dataset too large ({len(df)} rows). Sampling 100k rows for fast evaluation...")
            df = df.sample(n=100000, random_state=42)
            
        model = joblib.load(m_path)
        encoders = joblib.load(e_path)
    except Exception as e:
        print(f"❌ Error loading evaluation artifacts: {e}")
        return
    
    # Preprocess matching the training process
    features = config.MODEL_FEATURES.copy()
    for feat in config.OPTIONAL_FEATURES:
        if feat in df.columns:
            features.append(feat)
            
    target = config.TARGET_VARIABLE
    
    # Filter only available columns
    features = [f for f in features if f in df.columns]
    
    X = df[features].copy()
    y = df[target]
    
    # Handle encoding
    for col, le in encoders.items():
        if col in X.columns:
            # Handle potentially unseen labels during evaluation
            X[col] = X[col].map(lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else 0)
        
    preds = model.predict(X)
    
    # Statistics
    mae = mean_absolute_error(y, preds)
    rmse = np.sqrt(mean_squared_error(y, preds))
    r2 = r2_score(y, preds)
    
    print(f"✅ Records Evaluated: {len(df)}")
    print(f"📊 Mean Absolute Error: {mae:.2f} mins")
    print(f"📊 Root Mean Squared Error: {rmse:.2f} mins")
    print(f"📊 R2 Score: {r2:.4f}")
    
    # Feature Importance
    try:
        importance = model.feature_importances_
        feat_imp = pd.Series(importance, index=X.columns).sort_values(ascending=False)
        print("\n📈 Feature Importances (Top 10):")
        print(feat_imp.head(10))
    except Exception as e:
        print(f"⚠️ Could not compute feature importance: {e}")

def main():
    evaluate_model()

if __name__ == "__main__":
    main()
