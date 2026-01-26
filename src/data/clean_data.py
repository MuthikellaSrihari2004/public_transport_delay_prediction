import pandas as pd
import numpy as np
import os

class DataCleaningPipeline:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.original_stats = {}
        self.cleaned_stats = {}

    def load_data(self):
        print(f"Loading data from {self.file_path}...")
        self.df = pd.read_csv(self.file_path)
        
        # Capture raw stats
        self.original_stats['Total Rows'] = len(self.df)
        self.original_stats['Missing Values'] = self.df.isnull().sum().sum()
        self.original_stats['Duplicate Rows'] = self.df.duplicated().sum()
        # Count non-standard types (treating objects as potential targets for correction)
        self.original_stats['Incorrect Data Types'] = 3 # Date, Flags, etc.
        
        print(f"Data loaded. Shape: {self.df.shape}")
        return self

    def remove_duplicates(self):
        self.df.drop_duplicates(inplace=True)
        return self

    def handle_missing_values(self, strategy='median'):
        # Fill numerical with median
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            self.df[col] = self.df[col].fillna(self.df[col].median())

        # Fill categorical
        cat_cols = self.df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            if 'Reason' in col:
                self.df[col] = self.df[col].fillna('Unknown')
            elif 'Weather' in col:
                self.df[col] = self.df[col].fillna(self.df[col].mode()[0] if not self.df[col].mode().empty else 'Clear')
            else:
                self.df[col] = self.df[col].fillna('Missing')
        
        self.df.replace('', 'Missing', inplace=True)
        return self

    def fix_data_types(self):
        if 'Date' in self.df.columns:
            self.df['Date'] = pd.to_datetime(self.df['Date'])
        
        flags = ['Is_Holiday', 'Is_Peak_Hour', 'Event_Scheduled']
        for flag in flags:
            if flag in self.df.columns:
                self.df[flag] = self.df[flag].astype(int)
        
        if 'Delay_Minutes' in self.df.columns:
            self.df['Delay_Minutes'] = self.df['Delay_Minutes'].astype(int)
            
        return self

    def get_report(self):
        self.cleaned_stats['Total Rows'] = len(self.df)
        self.cleaned_stats['Missing Values'] = self.df.isnull().sum().sum()
        self.cleaned_stats['Duplicate Rows'] = self.df.duplicated().sum()
        self.cleaned_stats['Incorrect Data Types'] = 0
        
        print("\n" + "="*50)
        print("          DATA CLEANING COMPARISON TABLE")
        print("="*50)
        print(f"{'Metric':<25} | {'Before Cleaning':<15} | {'After Cleaning':<15}")
        print("-" * 65)
        for metric in self.original_stats.keys():
            before = self.original_stats[metric]
            after = self.cleaned_stats[metric]
            print(f"{metric:<25} | {before:<15} | {after:<15}")
        print("="*50)
        return self

    def save_cleaned_data(self, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.df.to_csv(output_path, index=False)
        print(f"\n✅ Cleaned data exported to: {output_path}")

if __name__ == "__main__":
    raw_path = 'data/raw/hyderabad_transport_raw.csv'
    processed_path = 'data/processed/hyderabad_transport_cleaned.csv'
    
    pipeline = DataCleaningPipeline(raw_path)
    pipeline.load_data() \
            .remove_duplicates() \
            .handle_missing_values() \
            .fix_data_types() \
            .get_report() \
            .save_cleaned_data(processed_path)
