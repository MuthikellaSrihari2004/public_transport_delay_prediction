import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from pathlib import Path

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config

# Set Plotting Style
plt.style.use('ggplot')
sns.set_palette("viridis")

def perform_eda(data_path=None, output_dir=None):
    """Perform Exploratory Data Analysis and save visualizations"""
    source_path = data_path or str(config.FEATURES_DATA_FILE)
    target_dir = output_dir or str(config.FIGURES_DIR)
    
    print(f"🚀 Starting Exploratory Data Analysis on: {source_path}")
    
    if not os.path.exists(source_path):
        print(f"❌ Error: Data file not found at {source_path}")
        return

    # Create output directory
    os.makedirs(target_dir, exist_ok=True)
    
    # Load Data
    df = pd.read_csv(source_path)
    print(f"📊 Dataset loaded with {df.shape[0]} rows and {df.shape[1]} columns.")
    
    # 1. Distribution of Target Variable (delay_minutes)
    plt.figure(figsize=(10, 6))
    sns.histplot(df['delay_minutes'], bins=50, kde=True, color='#38bdf8')
    plt.title('Distribution of Transport Delays in Hyderabad', fontsize=15, fontweight='bold')
    plt.xlabel('Delay (Minutes)')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(target_dir, 'delay_distribution.png'))
    plt.close()
    print("✅ Saved: delay_distribution.png")
    
    # 2. Delay vs Transport Type
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='transport_type', y='delay_minutes', data=df, palette='Set2')
    plt.title('Delay Variance by Transport Type', fontsize=15, fontweight='bold')
    plt.savefig(os.path.join(target_dir, 'delay_by_transport.png'))
    plt.close()
    print("✅ Saved: delay_by_transport.png")
    
    # 3. Peak Hour Impact
    plt.figure(figsize=(10, 6))
    sns.barplot(x='is_peak_hour', y='delay_minutes', data=df, estimator=np.mean)
    plt.title('Average Delay: Peak Hours vs Non-Peak Hours', fontsize=15, fontweight='bold')
    plt.xticks([0, 1], ['Off-Peak', 'Peak Hour'])
    plt.savefig(os.path.join(target_dir, 'peak_hour_impact.png'))
    plt.close()
    print("✅ Saved: peak_hour_impact.png")
    
    # 4. Correlation Heatmap (Numerical Features)
    plt.figure(figsize=(12, 10))
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    corr = df[numerical_cols].corr()
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', linewidths=0.5)
    plt.title('Feature Correlation Heatmap', fontsize=15, fontweight='bold')
    plt.savefig(os.path.join(target_dir, 'correlation_heatmap.png'))
    plt.close()
    print("✅ Saved: correlation_heatmap.png")
    
    # 5. Delay by Traffic Density
    plt.figure(figsize=(10, 6))
    sns.violinplot(x='traffic_density', y='delay_minutes', data=df)
    plt.title('Delay Distribution by Traffic Density', fontsize=15, fontweight='bold')
    plt.savefig(os.path.join(target_dir, 'traffic_impact.png'))
    plt.close()
    print("✅ Saved: traffic_impact.png")
    
    # 6. Weather Impact on Delays
    if 'weather' in df.columns:
        plt.figure(figsize=(12, 6))
        mean_delay_weather = df.groupby('weather')['delay_minutes'].mean().sort_values(ascending=False)
        sns.barplot(x=mean_delay_weather.index, y=mean_delay_weather.values)
        plt.title('Average Delay by Weather Condition', fontsize=15, fontweight='bold')
        plt.xticks(rotation=45)
        plt.savefig(os.path.join(target_dir, 'weather_impact.png'))
        plt.close()
        print("✅ Saved: weather_impact.png")
    
    print(f"\n✨ EDA Complete! All figures saved in {target_dir}")

def main():
    perform_eda()

if __name__ == "__main__":
    main()
