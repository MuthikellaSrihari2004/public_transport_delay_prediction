
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import config

# Import pipeline components
from src.data.make_dataset import generate_hyderabad_data
from src.data.clean_data import DataCleaningPipeline
from src.data.build_features import FeatureEngineer
from src.models.train_model import AdvancedModelTrainer
from src.models.evaluate_model import evaluate_model
from create_deploy_db import create_deployment_db

def run_pipeline(force_regen=False):
    """
    Main entry point for the HyderTrax ML Pipeline.
    Orchestrates data generation, cleaning, feature engineering, 
    model training, and deployment database creation.
    """
    print("="*70)
    print("🚀 HYDERTRAX: ELITE ML PIPELINE (INTEGRATED VERSION)")
    print("="*70)
    start_global = time.time()

    # --- STEP 1: DATA GENERATION ---
    print("\n[STEP 1/6] 🏗️ DATA GENERATION")
    raw_path = config.RAW_DATA_FILE
    if not os.path.exists(raw_path) or force_regen:
        print("📡 Generating fresh synthetic transport data for Hyderabad...")
        generate_hyderabad_data()
    else:
        print(f"✅ Raw data already exists at {raw_path}. Skipping generation.")

    # --- STEP 2: DATA CLEANING ---
    print("\n[STEP 2/6] 🧹 DATA CLEANING")
    cleaned_path = config.CLEANED_DATA_FILE
    
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
    print("\n[STEP 3/6] 🛠️  FEATURE ENGINEERING")
    features_path = config.FEATURES_DATA_FILE
    
    engineer = FeatureEngineer(cleaned_path, features_path)
    engineer.load_data().create_features().save_features()

    # --- STEP 4: MODEL TRAINING ---
    print("\n[STEP 4/6] 🤖 MODEL TRAINING & SELECTION")
    # Using the optimized trainer (downsampling + model comparison)
    trainer = AdvancedModelTrainer(features_path)
    trainer.load_data().preprocess().train_and_compare().save()

    # --- STEP 5: EVALUATION ---
    print("\n[STEP 5/6] 📊 MODEL EVALUATION")
    evaluate_model(data_path=features_path)

    # --- STEP 6: BALANCED DEPLOYMENT DB ---
    print("\n[STEP 6/6] 🗄️  DEPLOYMENT DATABASE CREATION")
    # We use create_deployment_db to create a balanced, fast database
    # instead of a massive one that slows down the app.
    create_deployment_db(limit=30000) 

    print("\n" + "="*70)
    print(f"🏁 PIPELINE COMPLETED SUCCESSFULLY in {time.time() - start_global:.2f} seconds.")
    print("="*70)
    print("🚀 SYSTEM STATUS: READY")
    print("💡 Command to start Web UI:      python app.py")
    print("💡 Command to start Terminal UI: python src/models/predict_terminal.py")
    print("="*70)

if __name__ == "__main__":
    # Check for command line flags
    regen = "--regen" in sys.argv
    run_pipeline(force_regen=regen)
