import pandas as pd
import joblib
from sklearn.model_selection import RandomizedSearchCV
from xgboost import XGBRegressor

def hyperparameter_tuning(data_path, encoder_path):
    print("--- Hyperparameter Tuning (Randomized Search) ---")
    df = pd.read_csv(data_path).sample(50000) # Sample for faster tuning
    encoders = joblib.load(encoder_path)
    
    features = ['Transport_Type', 'From_Location', 'To_Location', 'Weather', 
                'Is_Holiday', 'Is_Peak_Hour', 'Event_Scheduled', 'Traffic_Density',
                'Temperature_C', 'Humidity_Pct', 'Passenger_Load', 'Distance_KM',
                'Dep_Hour', 'Day_of_Week', 'Weather_Traffic_Index']
    
    X = df[features].copy()
    y = df['Delay_Minutes']
    
    for col, le in encoders.items():
        X[col] = le.transform(X[col])
        
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 6, 9],
        'learning_rate': [0.01, 0.1, 0.2],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }
    
    xgb = XGBRegressor(random_state=42)
    random_search = RandomizedSearchCV(xgb, param_distributions=param_grid, 
                                      n_iter=10, cv=3, scoring='neg_mean_absolute_error', 
                                      verbose=1, n_jobs=-1)
    
    random_search.fit(X, y)
    
    print(f"Best Parameters: {random_search.best_params_}")
    print(f"Best Score (MAE): {-random_search.best_score_:.2f}")
    
    # Save the best model
    joblib.dump(random_search.best_estimator_, 'models/xgboost_tuned_model.pkl')
    print("✅ Tuned model saved to models/xgboost_tuned_model.pkl")

if __name__ == "__main__":
    hyperparameter_tuning('data/processed/hyderabad_transport_features.csv', 
                          'models/label_encoders.pkl')
