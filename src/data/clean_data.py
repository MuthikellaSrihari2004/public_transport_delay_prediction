"""
clean_data.py — Data Cleaning Pipeline
========================================
Removes duplicates, handles missing values, and fixes data types.
Outputs a comparison table showing before/after statistics.
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config


class DataCleaningPipeline:
    """Chain-style data cleaning: load → clean → report → save."""

    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.before_stats = {}
        self.after_stats = {}

    def load_data(self):
        print(f"Loading data from {self.file_path}...")
        self.df = pd.read_csv(self.file_path)
        self.before_stats = {
            'Total Rows': len(self.df),
            'Missing Values': int(self.df.isnull().sum().sum()),
            'Duplicate Rows': int(self.df.duplicated().sum()),
        }
        print(f"Loaded: {self.df.shape[0]:,} rows × {self.df.shape[1]} columns")
        return self

    def remove_duplicates(self):
        self.df.drop_duplicates(inplace=True)
        return self

    def handle_missing_values(self):
        # Numerical columns: fill with median
        for col in self.df.select_dtypes(include=[np.number]).columns:
            self.df[col] = self.df[col].fillna(self.df[col].median())

        # Categorical columns: fill based on context
        for col in self.df.select_dtypes(include=['object']).columns:
            if 'Reason' in col:
                self.df[col] = self.df[col].fillna('Unknown')
            elif 'Weather' in col:
                mode = self.df[col].mode()
                self.df[col] = self.df[col].fillna(mode[0] if not mode.empty else 'Clear')
            else:
                self.df[col] = self.df[col].fillna('Missing')

        # Replace empty strings
        self.df.replace('', 'Missing', inplace=True)
        return self

    def fix_data_types(self):
        if 'Date' in self.df.columns:
            self.df['Date'] = pd.to_datetime(self.df['Date'])

        for flag in ['Is_Holiday', 'Is_Peak_Hour', 'Event_Scheduled']:
            if flag in self.df.columns:
                self.df[flag] = self.df[flag].astype(int)

        if 'Delay_Minutes' in self.df.columns:
            self.df['Delay_Minutes'] = self.df['Delay_Minutes'].astype(int)

        return self

    def get_report(self):
        self.after_stats = {
            'Total Rows': len(self.df),
            'Missing Values': int(self.df.isnull().sum().sum()),
            'Duplicate Rows': int(self.df.duplicated().sum()),
        }

        print(f"\n{'='*55}")
        print("        DATA CLEANING REPORT")
        print(f"{'='*55}")
        print(f"{'Metric':<25} | {'Before':<12} | {'After':<12}")
        print("-" * 55)
        for metric in self.before_stats:
            print(f"{metric:<25} | {self.before_stats[metric]:<12} | {self.after_stats[metric]:<12}")
        print(f"{'='*55}")
        return self

    def save_cleaned_data(self, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.df.to_csv(output_path, index=False)
        print(f"Cleaned data saved to: {output_path}")


if __name__ == "__main__":
    pipeline = DataCleaningPipeline(str(config.RAW_DATA_FILE))
    pipeline.load_data() \
            .remove_duplicates() \
            .handle_missing_values() \
            .fix_data_types() \
            .get_report() \
            .save_cleaned_data(str(config.CLEANED_DATA_FILE))
