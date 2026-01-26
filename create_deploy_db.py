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
    
    if not os.path.exists(source_path):
        print(f"❌ Source file not found: {source_path}")
        return

    try:
        # Load only top N rows to keep DB small for Git/Render
        df = pd.read_csv(source_path, nrows=limit)
        print(f"📈 Loaded {len(df)} rows.")

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
