import pandas as pd
import joblib
from sklearn.model_selection import cross_val_score
from xgboost import XGBRegressor

def validate_model(data_path, encoder_path):
    print("--- Cross Validation ---")
    df = pd.read_csv(data_path).sample(20000) # Sample for speed
    encoders = joblib.load(encoder_path)
    
    features = ['Transport_Type', 'From_Location', 'To_Location', 'Weather', 
                'Is_Holiday', 'Is_Peak_Hour', 'Event_Scheduled', 'Traffic_Density',
                'Temperature_C', 'Humidity_Pct', 'Passenger_Load', 'Distance_KM',
                'Dep_Hour', 'Day_of_Week', 'Weather_Traffic_Index']
    
    X = df[features].copy()
    y = df['Delay_Minutes']
    
    for col, le in encoders.items():
        X[col] = le.transform(X[col])
        
    model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6)
    
    scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_absolute_error')
    
    print(f"MAE Scores across 5 folds: {-scores}")
    print(f"Average MAE: {-scores.mean():.2f}")
    print(f"Standard Deviation: {scores.std():.2f}")

if __name__ == "__main__":
    validate_model('data/processed/hyderabad_transport_features.csv', 
                    'models/label_encoders.pkl')
