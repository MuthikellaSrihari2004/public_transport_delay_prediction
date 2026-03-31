"""
Comprehensive Exploratory Data Analysis (EDA) Module
=====================================================
Performs in-depth statistical analysis and generates publication-quality
visualizations for the Hyderabad Public Transport Delay dataset.

Outputs:
  - 10+ visualization figures saved to reports/figures/
  - Detailed eda_insights.md report saved to reports/
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config

# ── Plot Configuration ──────────────────────────────────────────────────
plt.rcParams.update({
    'figure.dpi': 120,
    'savefig.dpi': 150,
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'figure.figsize': (10, 6),
    'figure.facecolor': '#FAFAFA',
    'axes.facecolor': '#FAFAFA',
    'axes.grid': True,
    'grid.alpha': 0.3,
})
sns.set_palette("muted")


class EDAAnalyzer:
    """Complete EDA pipeline for transport delay prediction dataset."""

    def __init__(self, data_path=None, output_dir=None, report_path=None):
        self.data_path = data_path or str(config.FEATURES_DATA_FILE)
        self.output_dir = output_dir or str(config.FIGURES_DIR)
        self.report_path = report_path or str(config.EDA_INSIGHTS_FILE)
        self.df = None
        self.insights = {}  # Collects key findings for the report

    # ── 1. Load & Describe ──────────────────────────────────────────────
    def load_data(self):
        """Load dataset and capture basic statistics."""
        print(f"\n{'='*60}")
        print("  📊 EXPLORATORY DATA ANALYSIS (EDA)")
        print(f"{'='*60}")
        print(f"📂 Loading data from: {self.data_path}")

        if not os.path.exists(self.data_path):
            print(f"❌ Data file not found: {self.data_path}")
            return self

        self.df = pd.read_csv(self.data_path)

        # Sample if dataset is too large for fast EDA
        if len(self.df) > 500000:
            print(f"⚠️  Large dataset ({len(self.df):,} rows). Sampling 300,000 rows for EDA...")
            self.df = self.df.sample(n=300000, random_state=42)

        os.makedirs(self.output_dir, exist_ok=True)

        # Basic stats
        self.insights['total_rows'] = len(self.df)
        self.insights['total_columns'] = len(self.df.columns)
        self.insights['column_names'] = list(self.df.columns)
        self.insights['memory_mb'] = round(self.df.memory_usage(deep=True).sum() / 1024**2, 2)
        self.insights['missing_values'] = int(self.df.isnull().sum().sum())
        self.insights['duplicate_rows'] = int(self.df.duplicated().sum())

        # Target variable stats
        if 'Delay_Minutes' in self.df.columns:
            delay = self.df['Delay_Minutes']
            self.insights['delay_mean'] = round(delay.mean(), 2)
            self.insights['delay_median'] = round(delay.median(), 2)
            self.insights['delay_std'] = round(delay.std(), 2)
            self.insights['delay_min'] = int(delay.min())
            self.insights['delay_max'] = int(delay.max())
            self.insights['delay_skewness'] = round(delay.skew(), 2)
            self.insights['delay_kurtosis'] = round(delay.kurtosis(), 2)
            self.insights['on_time_pct'] = round((delay <= 10).mean() * 100, 1)
            self.insights['minor_delay_pct'] = round(((delay > 10) & (delay <= 20)).mean() * 100, 1)
            self.insights['major_delay_pct'] = round((delay > 20).mean() * 100, 1)

        print(f"✅ Loaded {self.insights['total_rows']:,} rows × {self.insights['total_columns']} columns")
        print(f"   Memory: {self.insights['memory_mb']} MB")
        print(f"   Missing: {self.insights['missing_values']} | Duplicates: {self.insights['duplicate_rows']}")
        return self

    # ── 2. Visualization Pipeline ───────────────────────────────────────
    def run_all_visualizations(self):
        """Execute all visualization methods."""
        if self.df is None:
            print("❌ No data loaded. Call load_data() first.")
            return self

        self._plot_delay_distribution()
        self._plot_delay_by_transport()
        self._plot_peak_hour_impact()
        self._plot_weather_impact()
        self._plot_traffic_impact()
        self._plot_correlation_heatmap()
        self._plot_hourly_pattern()
        self._plot_day_of_week()
        self._plot_holiday_impact()
        self._plot_top_routes()
        self._plot_delay_category_pie()
        self._plot_passenger_load_vs_delay()

        print(f"\n✨ All {12} visualizations saved to: {self.output_dir}")
        return self

    # ── Individual Plot Methods ─────────────────────────────────────────

    def _plot_delay_distribution(self):
        """1. Distribution of Delay_Minutes (Histogram + KDE)."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Histogram + KDE
        sns.histplot(self.df['Delay_Minutes'], bins=50, kde=True,
                     color='#4F46E5', edgecolor='white', ax=axes[0])
        axes[0].set_title('Distribution of Transport Delays')
        axes[0].set_xlabel('Delay (Minutes)')
        axes[0].set_ylabel('Frequency')
        axes[0].axvline(self.df['Delay_Minutes'].mean(), color='red',
                        linestyle='--', label=f"Mean: {self.df['Delay_Minutes'].mean():.1f} min")
        axes[0].axvline(self.df['Delay_Minutes'].median(), color='orange',
                        linestyle='--', label=f"Median: {self.df['Delay_Minutes'].median():.1f} min")
        axes[0].legend()

        # Box plot
        sns.boxplot(y=self.df['Delay_Minutes'], color='#4F46E5', ax=axes[1])
        axes[1].set_title('Delay Box Plot (Outlier Detection)')
        axes[1].set_ylabel('Delay (Minutes)')

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '01_delay_distribution.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 01_delay_distribution.png")

    def _plot_delay_by_transport(self):
        """2. Delay comparison across Bus, Metro, Train."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Box plot
        order = ['Bus', 'Metro', 'Train']
        colors = ['#EF4444', '#3B82F6', '#10B981']
        sns.boxplot(x='Transport_Type', y='Delay_Minutes', data=self.df,
                    order=order, palette=colors, ax=axes[0])
        axes[0].set_title('Delay Variance by Transport Type')
        axes[0].set_xlabel('Transport Type')
        axes[0].set_ylabel('Delay (Minutes)')

        # Violin plot
        sns.violinplot(x='Transport_Type', y='Delay_Minutes', data=self.df,
                       order=order, palette=colors, ax=axes[1], inner='quartile')
        axes[1].set_title('Delay Distribution Shape by Transport Type')
        axes[1].set_xlabel('Transport Type')
        axes[1].set_ylabel('Delay (Minutes)')

        # Capture insight
        avg_by_type = self.df.groupby('Transport_Type')['Delay_Minutes'].mean()
        self.insights['avg_delay_by_type'] = avg_by_type.round(2).to_dict()
        self.insights['highest_delay_type'] = avg_by_type.idxmax()

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '02_delay_by_transport.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 02_delay_by_transport.png")

    def _plot_peak_hour_impact(self):
        """3. Peak vs Non-Peak hour delay analysis."""
        fig, ax = plt.subplots(figsize=(8, 5))

        peak_data = self.df.groupby('Is_Peak_Hour')['Delay_Minutes'].agg(['mean', 'median', 'std'])
        peak_data.index = ['Off-Peak', 'Peak Hour']
        colors = ['#10B981', '#EF4444']

        bars = ax.bar(peak_data.index, peak_data['mean'], color=colors,
                      edgecolor='white', linewidth=1.5)

        # Add value labels
        for bar, val in zip(bars, peak_data['mean']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{val:.1f} min', ha='center', fontweight='bold')

        ax.set_title('Average Delay: Peak Hours vs Off-Peak')
        ax.set_ylabel('Average Delay (Minutes)')

        self.insights['peak_avg_delay'] = round(peak_data.loc['Peak Hour', 'mean'], 2)
        self.insights['offpeak_avg_delay'] = round(peak_data.loc['Off-Peak', 'mean'], 2)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '03_peak_hour_impact.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 03_peak_hour_impact.png")

    def _plot_weather_impact(self):
        """4. Average delay by weather condition."""
        if 'Weather' not in self.df.columns:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        weather_delay = self.df.groupby('Weather')['Delay_Minutes'].agg(['mean', 'count'])
        weather_delay = weather_delay.sort_values('mean', ascending=True)

        bars = ax.barh(weather_delay.index, weather_delay['mean'],
                       color=plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(weather_delay))))
        ax.set_title('Average Delay by Weather Condition')
        ax.set_xlabel('Average Delay (Minutes)')

        # Add count labels
        for bar, count in zip(bars, weather_delay['count']):
            ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
                    f'n={count:,}', va='center', fontsize=9)

        self.insights['worst_weather'] = weather_delay['mean'].idxmax()
        self.insights['worst_weather_delay'] = round(weather_delay['mean'].max(), 2)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '04_weather_impact.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 04_weather_impact.png")

    def _plot_traffic_impact(self):
        """5. Delay distribution by traffic density."""
        fig, ax = plt.subplots(figsize=(10, 6))

        order = ['Low', 'Medium', 'High', 'Very High']
        existing_order = [o for o in order if o in self.df['Traffic_Density'].unique()]

        sns.violinplot(x='Traffic_Density', y='Delay_Minutes', data=self.df,
                       order=existing_order, palette='YlOrRd', inner='quartile', ax=ax)
        ax.set_title('Delay Distribution by Traffic Density')
        ax.set_xlabel('Traffic Density')
        ax.set_ylabel('Delay (Minutes)')

        traffic_means = self.df.groupby('Traffic_Density')['Delay_Minutes'].mean()
        self.insights['avg_delay_by_traffic'] = traffic_means.round(2).to_dict()

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '05_traffic_impact.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 05_traffic_impact.png")

    def _plot_correlation_heatmap(self):
        """6. Feature correlation heatmap."""
        fig, ax = plt.subplots(figsize=(12, 10))

        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        # Filter to meaningful columns only
        skip_cols = ['id', 'Weather_Score', 'Traffic_Score']
        use_cols = [c for c in numerical_cols if c not in skip_cols]

        corr = self.df[use_cols].corr()

        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
                    center=0, linewidths=0.5, ax=ax, vmin=-1, vmax=1,
                    annot_kws={'size': 8})
        ax.set_title('Feature Correlation Heatmap')

        # Find top correlations with target
        if 'Delay_Minutes' in corr.columns:
            target_corr = corr['Delay_Minutes'].drop('Delay_Minutes').abs().sort_values(ascending=False)
            self.insights['top_correlated_features'] = target_corr.head(5).round(3).to_dict()

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '06_correlation_heatmap.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 06_correlation_heatmap.png")

    def _plot_hourly_pattern(self):
        """7. Delay pattern across hours of the day."""
        if 'Dep_Hour' not in self.df.columns:
            return

        fig, ax = plt.subplots(figsize=(12, 5))

        hourly = self.df.groupby('Dep_Hour')['Delay_Minutes'].agg(['mean', 'median', 'count'])

        ax.bar(hourly.index, hourly['mean'], color='#818CF8', alpha=0.7, label='Mean Delay')
        ax.plot(hourly.index, hourly['median'], color='#EF4444', marker='o',
                linewidth=2, label='Median Delay')

        # Highlight peak hours
        for h in range(24):
            if 8 <= h <= 11 or 17 <= h <= 20:
                ax.axvspan(h - 0.4, h + 0.4, alpha=0.08, color='red')

        ax.set_title('Delay Pattern Across Hours of Day')
        ax.set_xlabel('Hour of Day (24h)')
        ax.set_ylabel('Delay (Minutes)')
        ax.set_xticks(range(0, 24))
        ax.legend()

        self.insights['worst_hour'] = int(hourly['mean'].idxmax())
        self.insights['worst_hour_delay'] = round(hourly['mean'].max(), 2)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '07_hourly_delay_pattern.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 07_hourly_delay_pattern.png")

    def _plot_day_of_week(self):
        """8. Delay by day of week."""
        if 'Day_of_Week' not in self.df.columns:
            return

        fig, ax = plt.subplots(figsize=(10, 5))

        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily = self.df.groupby('Day_of_Week')['Delay_Minutes'].mean()

        colors = ['#3B82F6'] * 5 + ['#EF4444'] * 2  # Weekdays blue, weekends red
        bars = ax.bar(range(7), [daily.get(i, 0) for i in range(7)],
                      color=colors, edgecolor='white')
        ax.set_xticks(range(7))
        ax.set_xticklabels(day_names, rotation=45, ha='right')
        ax.set_title('Average Delay by Day of Week')
        ax.set_ylabel('Average Delay (Minutes)')

        # Value labels
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{bar.get_height():.1f}', ha='center', fontsize=9)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '08_day_of_week.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 08_day_of_week.png")

    def _plot_holiday_impact(self):
        """9. Holiday vs Non-Holiday comparison."""
        if 'Is_Holiday' not in self.df.columns:
            return

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Bar comparison
        holiday_data = self.df.groupby('Is_Holiday')['Delay_Minutes'].agg(['mean', 'median', 'std'])
        holiday_data.index = ['Non-Holiday', 'Holiday']
        colors = ['#3B82F6', '#F59E0B']

        axes[0].bar(holiday_data.index, holiday_data['mean'], color=colors, edgecolor='white')
        axes[0].set_title('Average Delay: Holiday vs Non-Holiday')
        axes[0].set_ylabel('Average Delay (Minutes)')
        for i, val in enumerate(holiday_data['mean']):
            axes[0].text(i, val + 0.2, f'{val:.1f}', ha='center', fontweight='bold')

        # Distribution shape comparison
        sns.kdeplot(data=self.df[self.df['Is_Holiday'] == 0]['Delay_Minutes'],
                    label='Non-Holiday', color='#3B82F6', ax=axes[1], fill=True, alpha=0.3)
        sns.kdeplot(data=self.df[self.df['Is_Holiday'] == 1]['Delay_Minutes'],
                    label='Holiday', color='#F59E0B', ax=axes[1], fill=True, alpha=0.3)
        axes[1].set_title('Delay Distribution: Holiday vs Non-Holiday')
        axes[1].set_xlabel('Delay (Minutes)')
        axes[1].legend()

        self.insights['holiday_avg_delay'] = round(holiday_data.loc['Holiday', 'mean'], 2)
        self.insights['nonholiday_avg_delay'] = round(holiday_data.loc['Non-Holiday', 'mean'], 2)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '09_holiday_impact.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 09_holiday_impact.png")

    def _plot_top_routes(self):
        """10. Top 10 most delayed routes."""
        if 'From_Location' not in self.df.columns:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        self.df['Route'] = self.df['From_Location'] + ' → ' + self.df['To_Location']
        route_delay = self.df.groupby('Route')['Delay_Minutes'].agg(['mean', 'count'])
        route_delay = route_delay[route_delay['count'] >= 50]  # Min sample size
        top_routes = route_delay.sort_values('mean', ascending=True).tail(10)

        bars = ax.barh(top_routes.index, top_routes['mean'],
                       color=plt.cm.Reds(np.linspace(0.3, 0.9, len(top_routes))))
        ax.set_title('Top 10 Most Delayed Routes (min 50 samples)')
        ax.set_xlabel('Average Delay (Minutes)')

        for bar, count in zip(bars, top_routes['count']):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    f'n={count:,}', va='center', fontsize=8)

        self.df.drop(columns=['Route'], inplace=True)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '10_top_delayed_routes.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 10_top_delayed_routes.png")

    def _plot_delay_category_pie(self):
        """11. Pie chart of delay categories."""
        fig, ax = plt.subplots(figsize=(8, 8))

        delay = self.df['Delay_Minutes']
        categories = {
            'On Time (≤10 min)': (delay <= 10).sum(),
            'Minor Delay (11-20 min)': ((delay > 10) & (delay <= 20)).sum(),
            'Major Delay (>20 min)': (delay > 20).sum(),
        }

        colors = ['#10B981', '#F59E0B', '#EF4444']
        explode = (0.02, 0.02, 0.05)

        wedges, texts, autotexts = ax.pie(
            categories.values(), labels=categories.keys(), autopct='%1.1f%%',
            colors=colors, explode=explode, shadow=True, startangle=90,
            textprops={'fontsize': 11}
        )
        for autotext in autotexts:
            autotext.set_fontweight('bold')

        ax.set_title('Delay Category Distribution', fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '11_delay_categories.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 11_delay_categories.png")

    def _plot_passenger_load_vs_delay(self):
        """12. Scatter: Passenger Load vs Delay relationship."""
        fig, ax = plt.subplots(figsize=(10, 6))

        # Sample for scatter (too many points makes it unreadable)
        sample = self.df.sample(n=min(5000, len(self.df)), random_state=42)

        scatter = ax.scatter(sample['Passenger_Load'], sample['Delay_Minutes'],
                             c=sample['Delay_Minutes'], cmap='RdYlGn_r',
                             alpha=0.4, s=15, edgecolors='none')
        plt.colorbar(scatter, label='Delay (min)')

        # Add trendline
        z = np.polyfit(sample['Passenger_Load'], sample['Delay_Minutes'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(sample['Passenger_Load'].min(), sample['Passenger_Load'].max(), 100)
        ax.plot(x_line, p(x_line), color='#EF4444', linewidth=2, linestyle='--', label='Trend')

        ax.set_title('Passenger Load vs Delay')
        ax.set_xlabel('Passenger Load (%)')
        ax.set_ylabel('Delay (Minutes)')
        ax.legend()

        corr_val = self.df['Passenger_Load'].corr(self.df['Delay_Minutes'])
        self.insights['passenger_delay_corr'] = round(corr_val, 3)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '12_passenger_vs_delay.png'), bbox_inches='tight')
        plt.close()
        print("  ✅ 12_passenger_vs_delay.png")

    # ── 3. Report Generation ────────────────────────────────────────────
    def generate_report(self):
        """Generate a comprehensive markdown EDA report."""
        if not self.insights:
            print("❌ No insights collected. Run analysis first.")
            return self

        report_lines = [
            "# 📊 EDA Report — Hyderabad Public Transport Delay Prediction",
            f"\n> Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 1. Dataset Overview",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Records | {self.insights.get('total_rows', 'N/A'):,} |",
            f"| Total Features | {self.insights.get('total_columns', 'N/A')} |",
            f"| Memory Usage | {self.insights.get('memory_mb', 'N/A')} MB |",
            f"| Missing Values | {self.insights.get('missing_values', 'N/A')} |",
            f"| Duplicate Rows | {self.insights.get('duplicate_rows', 'N/A')} |",
            "",
            "## 2. Target Variable Analysis (Delay_Minutes)",
            "",
            f"| Statistic | Value |",
            f"|-----------|-------|",
            f"| Mean | {self.insights.get('delay_mean', 'N/A')} min |",
            f"| Median | {self.insights.get('delay_median', 'N/A')} min |",
            f"| Std Deviation | {self.insights.get('delay_std', 'N/A')} min |",
            f"| Min | {self.insights.get('delay_min', 'N/A')} min |",
            f"| Max | {self.insights.get('delay_max', 'N/A')} min |",
            f"| Skewness | {self.insights.get('delay_skewness', 'N/A')} |",
            f"| Kurtosis | {self.insights.get('delay_kurtosis', 'N/A')} |",
            "",
            "### Delay Category Distribution",
            f"- **On Time (≤10 min):** {self.insights.get('on_time_pct', 'N/A')}%",
            f"- **Minor Delay (11-20 min):** {self.insights.get('minor_delay_pct', 'N/A')}%",
            f"- **Major Delay (>20 min):** {self.insights.get('major_delay_pct', 'N/A')}%",
            "",
            "## 3. Transport Type Analysis",
            "",
        ]

        # Add transport type breakdown
        if 'avg_delay_by_type' in self.insights:
            report_lines.append("| Transport Type | Avg Delay (min) |")
            report_lines.append("|---------------|----------------|")
            for t_type, delay in self.insights['avg_delay_by_type'].items():
                report_lines.append(f"| {t_type} | {delay} |")
            report_lines.append("")
            report_lines.append(f"**Highest Average Delay:** {self.insights.get('highest_delay_type', 'N/A')}")
            report_lines.append("")

        # Peak Hour Analysis
        report_lines.extend([
            "## 4. Peak Hour Impact",
            "",
            f"- **Peak Hour Avg Delay:** {self.insights.get('peak_avg_delay', 'N/A')} min",
            f"- **Off-Peak Avg Delay:** {self.insights.get('offpeak_avg_delay', 'N/A')} min",
            "",
        ])

        # Weather Impact
        report_lines.extend([
            "## 5. Weather Impact",
            "",
            f"- **Worst Weather Condition:** {self.insights.get('worst_weather', 'N/A')}",
            f"- **Avg Delay in Worst Weather:** {self.insights.get('worst_weather_delay', 'N/A')} min",
            "",
        ])

        # Traffic Impact
        if 'avg_delay_by_traffic' in self.insights:
            report_lines.append("## 6. Traffic Density Impact")
            report_lines.append("")
            report_lines.append("| Traffic Level | Avg Delay (min) |")
            report_lines.append("|--------------|----------------|")
            for level, delay in self.insights['avg_delay_by_traffic'].items():
                report_lines.append(f"| {level} | {delay} |")
            report_lines.append("")

        # Hourly Pattern
        report_lines.extend([
            "## 7. Temporal Patterns",
            "",
            f"- **Worst Hour of Day:** {self.insights.get('worst_hour', 'N/A')}:00",
            f"- **Delay at Worst Hour:** {self.insights.get('worst_hour_delay', 'N/A')} min",
            "",
        ])

        # Holiday
        report_lines.extend([
            "## 8. Holiday Impact",
            "",
            f"- **Holiday Avg Delay:** {self.insights.get('holiday_avg_delay', 'N/A')} min",
            f"- **Non-Holiday Avg Delay:** {self.insights.get('nonholiday_avg_delay', 'N/A')} min",
            "",
        ])

        # Feature Correlations
        if 'top_correlated_features' in self.insights:
            report_lines.append("## 9. Top Features Correlated with Delay")
            report_lines.append("")
            report_lines.append("| Feature | Correlation |")
            report_lines.append("|---------|------------|")
            for feat, corr in self.insights['top_correlated_features'].items():
                report_lines.append(f"| {feat} | {corr} |")
            report_lines.append("")

        # Passenger Load
        report_lines.extend([
            "## 10. Passenger Load Correlation",
            "",
            f"- **Passenger Load ↔ Delay Correlation:** {self.insights.get('passenger_delay_corr', 'N/A')}",
            "",
        ])

        # Visualizations Reference
        report_lines.extend([
            "---",
            "",
            "## Visualizations Generated",
            "",
            "All figures are saved in `reports/figures/`:",
            "",
            "1. `01_delay_distribution.png` — Delay histogram, KDE, and box plot",
            "2. `02_delay_by_transport.png` — Box + Violin plots by transport type",
            "3. `03_peak_hour_impact.png` — Peak vs off-peak comparison",
            "4. `04_weather_impact.png` — Average delay by weather condition",
            "5. `05_traffic_impact.png` — Violin plot by traffic density",
            "6. `06_correlation_heatmap.png` — Feature correlation matrix",
            "7. `07_hourly_delay_pattern.png` — Hour-of-day delay analysis",
            "8. `08_day_of_week.png` — Day-of-week delay comparison",
            "9. `09_holiday_impact.png` — Holiday vs non-holiday analysis",
            "10. `10_top_delayed_routes.png` — Top 10 most delayed routes",
            "11. `11_delay_categories.png` — Pie chart of delay categories",
            "12. `12_passenger_vs_delay.png` — Passenger load vs delay scatter",
        ])

        # Write report
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
        with open(self.report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        print(f"\n📝 EDA Report saved to: {self.report_path}")
        return self


# ── Public API ──────────────────────────────────────────────────────────

def perform_eda(data_path=None, output_dir=None):
    """Run the complete EDA pipeline. Called by main.py or standalone."""
    analyzer = EDAAnalyzer(data_path=data_path, output_dir=output_dir)
    analyzer.load_data()
    if analyzer.df is not None:
        analyzer.run_all_visualizations()
        analyzer.generate_report()
    return analyzer


def main():
    perform_eda()


if __name__ == "__main__":
    main()
