import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))
import config

def create_deployment_db(limit=20000):
    """
    Creates a lightweight transport.db for deployment by sampling
    the processed dataset.
    """
    source_path = config.FEATURES_DATA_FILE
    target_path = config.DB_PATH
    
    print(f"🚀 Creating reduced deployment DB from {source_path}...")
    
    if os.path.exists(target_path):
        print(f"🧹 Removing existing database at {target_path}...")
        os.remove(target_path)
    
    if not os.path.exists(source_path):
        print(f"❌ Source file not found: {source_path}")
        return

    try:
        # Use random sampling for better data representation across the dataset
        # This reads the whole file and picks random records
        full_df = pd.read_csv(source_path)
        df = full_df.sample(n=min(limit, len(full_df)), random_state=42)
        print(f"📈 Randomly sampled {len(df)} rows from {len(full_df)} total records.")

        # Ensure ID column
        if 'id' not in df.columns:
            df.insert(0, 'id', range(1, len(df) + 1))

        # Create/Replace DB
        db_url = f'sqlite:///{os.path.abspath(target_path)}'
        engine = create_engine(db_url)
        
        df.to_sql('schedules', con=engine, if_exists='replace', index=False)
        
        print(f"✅ Successfully created {target_path} with {len(df)} records.")
        print(f"💾 DB Size: {os.path.getsize(target_path) / (1024*1024):.2f} MB")
        
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    create_deployment_db()
