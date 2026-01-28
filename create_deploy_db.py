
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
    the processed dataset equally across transport modes.
    """
    source_path = config.FEATURES_DATA_FILE
    target_path = config.DB_PATH
    
    print(f"🚀 Creating balanced deployment DB from {source_path}...")
    
    if os.path.exists(target_path):
        print(f"🧹 Removing existing database at {target_path}...")
        os.remove(target_path)
    
    if not os.path.exists(source_path):
        print(f"❌ Source file not found: {source_path}")
        return

    try:
        full_df = pd.read_csv(source_path)
        
        # Determine unique modes
        modes = full_df['Transport_Type'].unique()
        limit_per_mode = limit // len(modes)
        
        print(f"📊 Detected modes: {list(modes)}")
        print(f"📈 Sampling {limit_per_mode} latest records for each mode...")
        
        sampled_dfs = []
        for mode in modes:
            mode_df = full_df[full_df['Transport_Type'] == mode].tail(limit_per_mode)
            sampled_dfs.append(mode_df)
            
        df = pd.concat(sampled_dfs).sort_values(['Date', 'Scheduled_Departure'])
        
        # Ensure ID column is unique and starts from 1
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
        df.insert(0, 'id', range(1, len(df) + 1))

        # Create/Replace DB
        db_url = f'sqlite:///{os.path.abspath(target_path)}'
        engine = create_engine(db_url)
        
        df.to_sql('schedules', con=engine, if_exists='replace', index=False)
        
        print(f"✅ Successfully created {target_path} with {len(df)} records.")
        print(f"💾 DB Size: {os.path.getsize(target_path) / (1024*1024):.2f} MB")
        
        # Verification snippet
        print("\n🔍 Verification of records per mode:")
        print(df['Transport_Type'].value_counts())
        
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    create_deployment_db()
