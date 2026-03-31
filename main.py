"""
main.py — HyderTrax ML Pipeline
==================================
Complete backend pipeline that orchestrates all data processing,
analysis, modeling, and deployment steps in sequence.

Usage:
    python main.py              # Run full pipeline
    python main.py --regen      # Force regenerate all data
    python main.py --skip-eda   # Skip EDA visualization step
    python main.py --tune       # Include hyperparameter tuning
    python main.py --validate   # Include cross-validation

Pipeline Steps:
    1. Data Generation      → Synthetic Hyderabad transport data
    2. Data Cleaning        → Remove duplicates, handle missing values
    3. Feature Engineering  → Create derived features for ML
    4. EDA & Visualization  → 12 plots + insights report
    5. Model Training       → Train & compare 3 models (XGBoost wins)
    6. Model Evaluation     → MAE, RMSE, R2, feature importance
    7. Hyperparameter Tune  → RandomizedSearchCV (optional)
    8. Cross Validation     → 5-fold stability check (optional)
    9. Deployment Database  → SQLite DB for web app
"""

import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# ── Setup ───────────────────────────────────────────────────────────────

sys.path.insert(0, str(Path(__file__).parent))
import config


# ── Utility ─────────────────────────────────────────────────────────────

class PipelineTimer:
    """Track execution time for each pipeline step."""

    def __init__(self):
        self.steps = []
        self.start_time = time.time()

    def start_step(self, name):
        self._current = {"name": name, "start": time.time(), "status": "RUNNING"}

    def end_step(self, status="DONE"):
        self._current["end"] = time.time()
        self._current["duration"] = self._current["end"] - self._current["start"]
        self._current["status"] = status
        self.steps.append(self._current)

    def print_summary(self):
        total = time.time() - self.start_time

        print(f"\n{'='*70}")
        print("  PIPELINE EXECUTION SUMMARY")
        print(f"{'='*70}")
        print(f"  {'#':<4} {'Step':<35} {'Time':>10} {'Status':>10}")
        print(f"  {'-'*4} {'-'*35} {'-'*10} {'-'*10}")

        for i, step in enumerate(self.steps, 1):
            dur = step['duration']
            if dur >= 60:
                time_str = f"{dur/60:.1f} min"
            else:
                time_str = f"{dur:.1f} sec"

            status_icon = "DONE" if step['status'] == "DONE" else "SKIP" if step['status'] == "SKIPPED" else "FAIL"
            print(f"  {i:<4} {step['name']:<35} {time_str:>10} {status_icon:>10}")

        print(f"  {'-'*4} {'-'*35} {'-'*10} {'-'*10}")
        if total >= 60:
            print(f"  {'':4} {'TOTAL':<35} {total/60:.1f} min")
        else:
            print(f"  {'':4} {'TOTAL':<35} {total:.1f} sec")
        print(f"{'='*70}")


def print_banner():
    """Display pipeline startup banner."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print("=" * 70)
    print("  HYDERTRAX — ML Pipeline")
    print("  Hyderabad Public Transport Delay Prediction System")
    print(f"  Started: {now}")
    print("=" * 70)


def print_step_header(step_num, total, title):
    """Print a formatted step header."""
    print(f"\n{'─'*70}")
    print(f"  STEP {step_num}/{total}: {title}")
    print(f"{'─'*70}")


# ── Pipeline Steps ──────────────────────────────────────────────────────

def step_data_generation(timer, force_regen=False):
    """Step 1: Generate synthetic transport data."""
    timer.start_step("Data Generation")

    raw_path = str(config.RAW_DATA_FILE)

    if os.path.exists(raw_path) and not force_regen:
        size_mb = os.path.getsize(raw_path) / (1024 * 1024)
        print(f"  Raw data already exists ({size_mb:.1f} MB). Skipping.")
        print(f"  Use --regen flag to force regeneration.")
        timer.end_step("SKIPPED")
        return True

    try:
        from src.data.make_dataset import generate_hyderabad_data
        generate_hyderabad_data()
        timer.end_step("DONE")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        timer.end_step("FAILED")
        return False


def step_data_cleaning(timer):
    """Step 2: Clean raw data (duplicates, missing values, types)."""
    timer.start_step("Data Cleaning")

    raw_path = str(config.RAW_DATA_FILE)
    cleaned_path = str(config.CLEANED_DATA_FILE)

    if not os.path.exists(raw_path):
        print(f"  ERROR: Raw data not found at {raw_path}")
        timer.end_step("FAILED")
        return False

    try:
        from src.data.clean_data import DataCleaningPipeline

        pipeline = DataCleaningPipeline(raw_path)
        pipeline.load_data() \
                .remove_duplicates() \
                .handle_missing_values() \
                .fix_data_types() \
                .get_report() \
                .save_cleaned_data(cleaned_path)

        timer.end_step("DONE")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        timer.end_step("FAILED")
        return False


def step_feature_engineering(timer):
    """Step 3: Create derived features from cleaned data."""
    timer.start_step("Feature Engineering")

    cleaned_path = str(config.CLEANED_DATA_FILE)
    features_path = str(config.FEATURES_DATA_FILE)

    if not os.path.exists(cleaned_path):
        print(f"  ERROR: Cleaned data not found at {cleaned_path}")
        timer.end_step("FAILED")
        return False

    try:
        from src.data.build_features import FeatureEngineer

        engineer = FeatureEngineer(cleaned_path, features_path)
        engineer.load_data().create_features().save_features()

        timer.end_step("DONE")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        timer.end_step("FAILED")
        return False


def step_eda(timer):
    """Step 4: Run exploratory data analysis and generate visualizations."""
    timer.start_step("EDA & Visualization")

    features_path = str(config.FEATURES_DATA_FILE)

    if not os.path.exists(features_path):
        print(f"  ERROR: Features data not found at {features_path}")
        timer.end_step("FAILED")
        return False

    try:
        from src.visualization.eda import perform_eda
        perform_eda(data_path=features_path)

        # Count generated figures
        fig_count = len([f for f in os.listdir(str(config.FIGURES_DIR))
                        if f.endswith('.png')]) if os.path.exists(str(config.FIGURES_DIR)) else 0
        print(f"  Generated {fig_count} visualization(s)")
        print(f"  Report: {config.EDA_INSIGHTS_FILE}")

        timer.end_step("DONE")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        timer.end_step("FAILED")
        return False


def step_model_training(timer):
    """Step 5: Train and compare ML models (LR, DT, XGBoost)."""
    timer.start_step("Model Training & Comparison")

    features_path = str(config.FEATURES_DATA_FILE)

    if not os.path.exists(features_path):
        print(f"  ERROR: Features data not found at {features_path}")
        timer.end_step("FAILED")
        return False

    try:
        from src.models.train_model import AdvancedModelTrainer

        trainer = AdvancedModelTrainer(features_path)
        trainer.load_data().preprocess().train_and_compare().save()

        print(f"  Model saved: {config.XGBOOST_MODEL_PATH}")
        print(f"  Encoders saved: {config.LABEL_ENCODERS_PATH}")

        timer.end_step("DONE")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        timer.end_step("FAILED")
        return False


def step_model_evaluation(timer):
    """Step 6: Evaluate trained model performance."""
    timer.start_step("Model Evaluation")

    if not os.path.exists(str(config.XGBOOST_MODEL_PATH)):
        print(f"  ERROR: Trained model not found. Run training first.")
        timer.end_step("FAILED")
        return False

    try:
        from src.models.evaluate_model import evaluate_model
        evaluate_model(data_path=str(config.FEATURES_DATA_FILE))

        timer.end_step("DONE")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        timer.end_step("FAILED")
        return False


def step_hyperparameter_tuning(timer):
    """Step 7 (Optional): Tune XGBoost hyperparameters."""
    timer.start_step("Hyperparameter Tuning")

    if not os.path.exists(str(config.LABEL_ENCODERS_PATH)):
        print(f"  ERROR: Label encoders not found. Run training first.")
        timer.end_step("FAILED")
        return False

    try:
        from src.models.tune_model import hyperparameter_tuning
        hyperparameter_tuning()

        print(f"  Tuned model saved: {config.XGBOOST_TUNED_MODEL_PATH}")

        timer.end_step("DONE")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        timer.end_step("FAILED")
        return False


def step_cross_validation(timer):
    """Step 8 (Optional): Run k-fold cross validation."""
    timer.start_step("Cross Validation (5-fold)")

    if not os.path.exists(str(config.LABEL_ENCODERS_PATH)):
        print(f"  ERROR: Label encoders not found. Run training first.")
        timer.end_step("FAILED")
        return False

    try:
        from src.models.cross_validate import validate_model
        validate_model()

        timer.end_step("DONE")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        timer.end_step("FAILED")
        return False


def step_deployment_database(timer, limit=30000):
    """Step 9: Create SQLite deployment database for web app."""
    timer.start_step("Deployment Database")

    if not os.path.exists(str(config.FEATURES_DATA_FILE)):
        print(f"  ERROR: Features data not found.")
        timer.end_step("FAILED")
        return False

    try:
        from create_deploy_db import create_deployment_db
        create_deployment_db(limit=limit)

        if os.path.exists(str(config.DB_PATH)):
            size_mb = os.path.getsize(str(config.DB_PATH)) / (1024 * 1024)
            print(f"  Database size: {size_mb:.1f} MB")

        timer.end_step("DONE")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        timer.end_step("FAILED")
        return False


# ── Main Pipeline ───────────────────────────────────────────────────────

def run_pipeline(args):
    """Execute the complete ML pipeline."""

    print_banner()
    config.ensure_directories()

    timer = PipelineTimer()

    # Determine which optional steps to include
    include_tune = args.tune
    include_validate = args.validate
    skip_eda = args.skip_eda

    # Calculate total steps
    total_steps = 6  # core steps (1-6 minus EDA + DB)
    if not skip_eda:
        total_steps += 1
    if include_tune:
        total_steps += 1
    if include_validate:
        total_steps += 1
    total_steps += 1  # deployment DB is always last

    step = 0

    # ── Step 1: Data Generation ──
    step += 1
    print_step_header(step, total_steps, "DATA GENERATION")
    if not step_data_generation(timer, force_regen=args.regen):
        if not os.path.exists(str(config.RAW_DATA_FILE)):
            print("\n  FATAL: Cannot continue without raw data.")
            timer.print_summary()
            return

    # ── Step 2: Data Cleaning ──
    step += 1
    print_step_header(step, total_steps, "DATA CLEANING")
    if not step_data_cleaning(timer):
        print("\n  FATAL: Cannot continue without cleaned data.")
        timer.print_summary()
        return

    # ── Step 3: Feature Engineering ──
    step += 1
    print_step_header(step, total_steps, "FEATURE ENGINEERING")
    if not step_feature_engineering(timer):
        print("\n  FATAL: Cannot continue without features.")
        timer.print_summary()
        return

    # ── Step 4: EDA (Optional) ──
    if not skip_eda:
        step += 1
        print_step_header(step, total_steps, "EXPLORATORY DATA ANALYSIS")
        step_eda(timer)  # Non-fatal — pipeline continues even if EDA fails

    # ── Step 5: Model Training ──
    step += 1
    print_step_header(step, total_steps, "MODEL TRAINING & COMPARISON")
    if not step_model_training(timer):
        print("\n  FATAL: Cannot continue without trained model.")
        timer.print_summary()
        return

    # ── Step 6: Model Evaluation ──
    step += 1
    print_step_header(step, total_steps, "MODEL EVALUATION")
    step_model_evaluation(timer)  # Non-fatal

    # ── Step 7: Hyperparameter Tuning (Optional) ──
    if include_tune:
        step += 1
        print_step_header(step, total_steps, "HYPERPARAMETER TUNING")
        step_hyperparameter_tuning(timer)

    # ── Step 8: Cross Validation (Optional) ──
    if include_validate:
        step += 1
        print_step_header(step, total_steps, "CROSS VALIDATION")
        step_cross_validation(timer)

    # ── Step 9: Deployment Database ──
    step += 1
    print_step_header(step, total_steps, "DEPLOYMENT DATABASE")
    step_deployment_database(timer)

    # ── Summary ──
    timer.print_summary()

    print(f"\n  Output Files:")
    print(f"    Model          : {config.XGBOOST_MODEL_PATH}")
    print(f"    Encoders       : {config.LABEL_ENCODERS_PATH}")
    print(f"    Database       : {config.DB_PATH}")
    if not skip_eda:
        print(f"    EDA Report     : {config.EDA_INSIGHTS_FILE}")
        print(f"    EDA Figures    : {config.FIGURES_DIR}/")
    if include_tune:
        print(f"    Tuned Model    : {config.XGBOOST_TUNED_MODEL_PATH}")

    print(f"\n  Next: Run 'python app.py' to start the web application.")
    print(f"        Open http://localhost:{config.FLASK_PORT} in your browser.")
    print(f"{'='*70}\n")


# ── CLI Entry Point ─────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="HyderTrax ML Pipeline — Train models and prepare deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    Run full pipeline (7 steps)
  python main.py --regen            Force regenerate all data from scratch
  python main.py --skip-eda         Skip EDA visualization step
  python main.py --tune --validate  Include tuning and cross-validation
  python main.py --regen --tune     Full pipeline + tuning with fresh data
        """
    )
    parser.add_argument('--regen', action='store_true',
                        help='Force regenerate raw data even if it exists')
    parser.add_argument('--skip-eda', action='store_true',
                        help='Skip the EDA visualization step')
    parser.add_argument('--tune', action='store_true',
                        help='Include hyperparameter tuning (slower)')
    parser.add_argument('--validate', action='store_true',
                        help='Include 5-fold cross validation')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args)
