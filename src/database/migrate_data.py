import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import os
import sys
from pathlib import Path

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config

def migrate_csv_to_database(csv_path=None, db_path=None):
    """Migrate feature-engineered CSV data to the SQLite database"""
    source_path = csv_path or str(config.FEATURES_DATA_FILE)
    target_path = db_path or str(config.DB_PATH)
    
    print(f"🚀 Migrating data from {source_path} to {target_path}...")
    
    if not os.path.exists(source_path):
        print(f"❌ Error: Source file not found: {source_path}")
        return False
        
    try:
        # Load data
        df = pd.read_csv(source_path)
        print(f"📈 Loaded {len(df)} records for migration.")
        
        # Add a unique ID if it doesn't exist
        if 'id' not in df.columns:
            df.insert(0, 'id', range(1, len(df) + 1))
            
        # Create SQLAlchemy engine
        # We use sqlite:///{path} format
        db_url = f'sqlite:///{os.path.abspath(target_path)}'
        engine = create_engine(db_url)
        
        # Load to SQL - 'replace' starts fresh, 'append' adds to existing
        # Using 'replace' for the schedules table to ensure consistent state
        df.to_sql('schedules', con=engine, if_exists='replace', index=False)
        
        print(f"✅ Migration complete! {len(df)} rows inserted into 'schedules' table.")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

# For backward compatibility if any script still uses the old name
def migrate_csv_to_db(csv_path, db_path='data/transport.db'):
    return migrate_csv_to_database(csv_path, db_path)

if __name__ == "__main__":
    migrate_csv_to_database()
