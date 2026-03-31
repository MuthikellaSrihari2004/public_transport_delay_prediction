"""
create_deploy_db.py — Deployment Database Builder
===================================================
Creates a lightweight SQLite database by sampling equally
across transport modes from the processed feature dataset.
"""

import pandas as pd
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).parent.absolute()))
import config


def create_deployment_db(limit=20000):
    """Create a balanced deployment database from the feature dataset."""
    source = str(config.FEATURES_DATA_FILE)
    target = str(config.DB_PATH)

    print(f"Creating deployment database...")

    if os.path.exists(target):
        os.remove(target)

    if not os.path.exists(source):
        print(f"Error: Source file not found: {source}")
        return

    try:
        df = pd.read_csv(source)

        # Sample equally across transport modes
        modes = df['Transport_Type'].unique()
        per_mode = limit // len(modes)

        print(f"Modes: {list(modes)}, {per_mode} records each")

        sampled = pd.concat([
            df[df['Transport_Type'] == mode].tail(per_mode)
            for mode in modes
        ]).sort_values(['Date', 'Scheduled_Departure'])

        # Ensure unique IDs
        if 'id' in sampled.columns:
            sampled = sampled.drop(columns=['id'])
        sampled.insert(0, 'id', range(1, len(sampled) + 1))

        # Write to SQLite
        engine = create_engine(f'sqlite:///{os.path.abspath(target)}')
        sampled.to_sql('schedules', con=engine, if_exists='replace', index=False)

        print(f"Database created: {target} ({len(sampled):,} records, "
              f"{os.path.getsize(target) / (1024*1024):.1f} MB)")
        print(sampled['Transport_Type'].value_counts().to_string())

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    create_deployment_db()
