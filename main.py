
import os
import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import pipeline components
from src.data.make_dataset import generate_hyderabad_data
from src.data.clean_data import DataCleaningPipeline
from src.data.build_features import FeatureEngineer
from src.models.train_model import AdvancedModelTrainer
from src.models.evaluate_model import evaluate_model
from src.database.migrate_data import migrate_csv_to_database

def run_pipeline():
    print("="*60)
    print("🚀 HYDERTRAX: ML PIPELINE EXECUTION")
    print("="*60)
    start_global = time.time()

    # --- STEP 1: DATA GENERATION ---
    print("\n--- STEP 1: DATA GENERATION ---")
    # This is critical to generate 2026 data
    generate_hyderabad_data()

    # --- STEP 2: DATA CLEANING ---
    print("\n--- STEP 2: DATA CLEANING ---")
    raw_path = 'data/raw/hyderabad_transport_raw.csv'
    cleaned_path = 'data/processed/hyderabad_transport_cleaned.csv'
    
    if not os.path.exists(raw_path):
        print(f"❌ Error: Raw data not found at {raw_path}.")
        return

    cleaner = DataCleaningPipeline(raw_path)
    cleaner.load_data() \
           .remove_duplicates() \
           .handle_missing_values() \
           .fix_data_types() \
           .get_report() \
           .save_cleaned_data(cleaned_path)

    # --- STEP 3: FEATURE ENGINEERING ---
    print("\n--- STEP 3: FEATURE ENGINEERING ---")
    features_path = 'data/processed/hyderabad_transport_features.csv'
    
    engineer = FeatureEngineer(cleaned_path, features_path)
    engineer.load_data().create_features().save_features()

    # --- STEP 4: MODEL TRAINING ---
    print("\n--- STEP 4: MODEL TRAINING & SELECTION ---")
    # Using the optimized trainer (downsampling + model comparison)
    trainer = AdvancedModelTrainer(features_path)
    trainer.load_data().preprocess().train_and_compare().save()

    # --- STEP 5: EVALUATION ---
    print("\n--- STEP 5: MODEL EVALUATION ---")
    evaluate_model(data_path=features_path)

    # --- STEP 6: DATABASE MIGRATION ---
    print("\n--- STEP 6: DATABASE MIGRATION ---")
    migrate_csv_to_database(csv_path=features_path)

    print("\n" + "="*60)
    print(f"✅ PIPELINE COMPLETED SUCCESSFULLY in {time.time() - start_global:.2f} seconds.")
    print("="*60)
    print("You can now run 'python app.py' to start the web dashboard")

if __name__ == "__main__":
    run_pipeline()
