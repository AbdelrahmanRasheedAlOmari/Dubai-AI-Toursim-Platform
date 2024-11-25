import sqlite3
import pandas as pd
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
import numpy as np

class InteractionAnalyzer:
    def __init__(self):
        self.db_name = "dubai_tourism.db"
        
    def extract_data(self):
        """Extract data from SQLite database"""
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query("""
            SELECT * FROM interactions
        """, conn)
        conn.close()
        return df
    
    def transform_data(self, df):
        """Transform and clean the data"""
        # Convert timestamps
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Parse JSON strings
        df['conversation_history'] = df['conversation_history'].apply(json.loads)
        df['generated_itinerary'] = df['generated_itinerary'].apply(json.loads)
        
        # Extract budget as float
        df['budget_value'] = df['budget'].str.extract(r'(\d+)').astype(float)
        
        # Extract duration as integer (improved parsing)
        def extract_duration(duration_str):
            if pd.isna(duration_str):
                return None
            # Extract numbers from strings like "5 days" or "7 Days"
            match = re.search(r'(\d+)', str(duration_str))
            if match:
                return int(match.group(1))
            return None
        
        df['duration_days'] = df['duration'].apply(extract_duration)
        
        # Extract group size from group_info
        def extract_group_size(group_info):
            if pd.isna(group_info):
                return 1
            # Extract numbers from strings like "family with 2 kids" or "group of 4 friends"
            numbers = re.findall(r'\d+', str(group_info))
            if numbers:
                # If "family with X kids", add 2 parents
                if 'family' in str(group_info).lower():
                    return int(numbers[0]) + 2
                # Otherwise return the number found
                return int(numbers[0])
            # Default values for common cases
            if 'solo' in str(group_info).lower():
                return 1
            if 'couple' in str(group_info).lower():
                return 2
            return 1  # Default to 1 if no size can be determined
        
        df['group_size'] = df['group_info'].apply(extract_group_size)
        
        return df
    
    def analyze_preferences(self, df):
        """Analyze user preferences in detail"""
        # Extract all preferences
        all_preferences = []
        for prefs in df['preferences'].dropna():
            all_preferences.extend([p.strip() for p in prefs.split(',')])
        
        # Count preferences
        preference_counts = Counter(all_preferences)
        
        # Calculate percentages
        total_preferences = sum(preference_counts.values())
        preference_percentages = {k: (v/total_preferences)*100 for k, v in preference_counts.items()}
        
        # Analyze preferences by group type
        preferences_by_group = {}
        for _, row in df.iterrows():
            if pd.notna(row['group_info']) and pd.notna(row['preferences']):
                group = row['group_info']
                prefs = [p.strip() for p in row['preferences'].split(',')]
                if group not in preferences_by_group:
                    preferences_by_group[group] = []
                preferences_by_group[group].extend(prefs)
        
        # Convert to percentage for each group
        preferences_by_group_pct = {}
        for group, prefs in preferences_by_group.items():
            total = len(prefs)
            counts = Counter(prefs)
            preferences_by_group_pct[group] = {k: (v/total)*100 for k, v in counts.items()}
        
        return {
            'preference_counts': dict(preference_counts),
            'preference_percentages': preference_percentages,
            'preferences_by_group': preferences_by_group_pct
        }
    
    def visualize_preferences(self, preference_data):
        """Create visualizations for preference analysis"""
        # 1. Overall Preference Distribution
        plt.figure(figsize=(12, 6))
        preferences = preference_data['preference_counts']
        plt.bar(preferences.keys(), preferences.values())
        plt.title('Distribution of User Preferences')
        plt.xlabel('Preferences')
        plt.ylabel('Number of Users')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('preference_distribution.png')
        plt.close()
        
        # 2. Preferences by Group Type
        group_preferences = preference_data['preferences_by_group']
        plt.figure(figsize=(15, 8))
        
        # Create a DataFrame for easier plotting
        group_pref_data = []
        for group, prefs in group_preferences.items():
            for pref, pct in prefs.items():
                group_pref_data.append({
                    'Group': group,
                    'Preference': pref,
                    'Percentage': pct
                })
        
        group_pref_df = pd.DataFrame(group_pref_data)
        
        # Create heatmap
        pivot_table = group_pref_df.pivot(index='Group', columns='Preference', values='Percentage')
        sns.heatmap(pivot_table, annot=True, fmt='.1f', cmap='YlOrRd')
        plt.title('Preferences by Group Type (Percentage)')
        plt.tight_layout()
        plt.savefig('preferences_by_group_heatmap.png')
        plt.close()
        
        # 3. Top Preferences Pie Chart
        plt.figure(figsize=(10, 10))
        top_preferences = dict(sorted(preference_data['preference_percentages'].items(), 
                                   key=lambda x: x[1], reverse=True)[:5])
        plt.pie(top_preferences.values(), labels=top_preferences.keys(), autopct='%1.1f%%')
        plt.title('Top 5 User Preferences')
        plt.axis('equal')
        plt.savefig('top_preferences_pie.png')
        plt.close()

    def analyze_preference_correlations(self, df):
        """Analyze correlations between preferences and other factors"""
        correlations = {}
        
        # Analyze preference vs budget
        budget_by_preference = {}
        for _, row in df.iterrows():
            if pd.notna(row['preferences']) and pd.notna(row['budget_value']):
                prefs = [p.strip() for p in row['preferences'].split(',')]
                for pref in prefs:
                    if pref not in budget_by_preference:
                        budget_by_preference[pref] = []
                    budget_by_preference[pref].append(row['budget_value'])
        
        # Calculate average budget for each preference
        correlations['avg_budget_by_preference'] = {
            pref: sum(budgets)/len(budgets) 
            for pref, budgets in budget_by_preference.items()
        }
        
        # Visualize budget vs preference correlation
        plt.figure(figsize=(12, 6))
        avg_budgets = correlations['avg_budget_by_preference']
        plt.bar(avg_budgets.keys(), avg_budgets.values())
        plt.title('Average Budget by Preference')
        plt.xlabel('Preference')
        plt.ylabel('Average Budget (USD)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('budget_by_preference.png')
        plt.close()
        
        return correlations

    def analyze_group_patterns(self, df):
        """Analyze patterns in group types and their behaviors"""
        group_patterns = {}
        
        # Average duration by group type
        group_duration = df.groupby('group_info')['duration_days'].mean()
        group_patterns['avg_duration'] = group_duration.to_dict()
        
        # Average budget by group type
        group_budget = df.groupby('group_info')['budget_value'].mean()
        group_patterns['avg_budget'] = group_budget.to_dict()
        
        # Most common preferences by group type
        group_preferences = {}
        for group in df['group_info'].unique():
            group_df = df[df['group_info'] == group]
            all_prefs = []
            for prefs in group_df['preferences'].dropna():
                all_prefs.extend([p.strip() for p in prefs.split(',')])
            group_preferences[group] = Counter(all_prefs).most_common(3)
        
        group_patterns['top_preferences'] = group_preferences
        
        return group_patterns

    def analyze_seasonal_trends(self, df):
        """Analyze seasonal trends based on travel dates"""
        try:
            # First, clean and standardize the date format
            def standardize_date(date_str):
                try:
                    # If it's already in YYYY-MM-DD format
                    return pd.to_datetime(date_str, format='%Y-%m-%d')
                except:
                    try:
                        # If it's in text format like "2nd november"
                        # Remove ordinal indicators and convert to datetime
                        date_str = str(date_str).lower()
                        date_str = date_str.replace('st ', ' ').replace('nd ', ' ').replace('rd ', ' ').replace('th ', ' ')
                        # Add year if not present
                        if '2024' not in date_str:
                            date_str += ' 2024'
                        return pd.to_datetime(date_str, format='%B %d %Y')
                    except:
                        print(f"Could not parse date: {date_str}")
                        return pd.NaT

            # Convert dates using the custom function
            df['travel_dates'] = df['travel_dates'].apply(standardize_date)
            
            # Remove rows with invalid dates
            df = df[df['travel_dates'].notna()]
            
            # Extract month information
            df['month'] = df['travel_dates'].dt.month
            df['month_name'] = df['travel_dates'].dt.strftime('%B')
            seasonal_trends = {}
            
            # Monthly booking counts by travel date
            monthly_bookings = df.groupby('month_name')['travel_dates'].count()
            seasonal_trends['monthly_bookings'] = monthly_bookings.to_dict()
            
            # Monthly average budget by travel date
            # Remove the '$' sign and convert to float
            df['budget_clean'] = df['budget'].str.replace('$', '').str.replace(',', '').astype(float)
            monthly_budget = df.groupby('month_name')['budget_clean'].mean()
            seasonal_trends['monthly_avg_budget'] = monthly_budget.to_dict()
            
            # Monthly average group size by travel date
            monthly_group_size = df.groupby('month_name')['group_size'].mean()
            seasonal_trends['monthly_group_size'] = monthly_group_size.to_dict()
            
            # Monthly preferences analysis by travel date
            monthly_preferences = {}
            preference_counts_by_month = {}
            
            for month in df['month_name'].unique():
                month_df = df[df['month_name'] == month]
                all_prefs = []
                for prefs in month_df['preferences'].dropna():
                    all_prefs.extend([p.strip() for p in prefs.split(',')])
                monthly_preferences[month] = Counter(all_prefs).most_common(5)
                preference_counts_by_month[month] = dict(Counter(all_prefs))
            
            seasonal_trends['monthly_preferences'] = monthly_preferences
            seasonal_trends['preference_counts_by_month'] = preference_counts_by_month
            
            return seasonal_trends
            
        except Exception as e:
            print(f"Error in analyze_seasonal_trends: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def visualize_group_patterns(self, group_patterns):
        """Create visualizations for group patterns"""
        # 1. Average Duration by Group Type
        plt.figure(figsize=(12, 6))
        groups = list(group_patterns['avg_duration'].keys())
        durations = list(group_patterns['avg_duration'].values())
        plt.bar(groups, durations)
        plt.title('Average Trip Duration by Group Type')
        plt.xlabel('Group Type')
        plt.ylabel('Average Duration (Days)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('group_duration.png')
        plt.close()
        
        # 2. Average Budget by Group Type
        plt.figure(figsize=(12, 6))
        budgets = list(group_patterns['avg_budget'].values())
        plt.bar(groups, budgets)
        plt.title('Average Budget by Group Type')
        plt.xlabel('Group Type')
        plt.ylabel('Average Budget (USD)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('group_budget.png')
        plt.close()

    def visualize_seasonal_trends(self, seasonal_trends):
        """Create enhanced visualizations for seasonal trends"""
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December']
        
        # 1. Preferences by Month Heatmap
        plt.figure(figsize=(15, 8))
        
        # Prepare data for heatmap
        all_preferences = set()
        for prefs in seasonal_trends['preference_counts_by_month'].values():
            all_preferences.update(prefs.keys())
        
        heatmap_data = []
        for month in month_order:
            if month in seasonal_trends['preference_counts_by_month']:
                month_prefs = seasonal_trends['preference_counts_by_month'][month]
                for pref in all_preferences:
                    heatmap_data.append({
                        'Month': month,
                        'Preference': pref,
                        'Count': month_prefs.get(pref, 0)
                    })
        
        heatmap_df = pd.DataFrame(heatmap_data)
        heatmap_pivot = heatmap_df.pivot(index='Month', columns='Preference', values='Count')
        heatmap_pivot = heatmap_pivot.reindex(month_order)
        
        sns.heatmap(heatmap_pivot, 
                    cmap='YlOrRd',
                    annot=True,
                    fmt='.0f',
                    cbar_kws={'label': 'Number of Preferences'})
        plt.title('Preferences Distribution by Month')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('monthly_preferences_heatmap.png')
        plt.close()
        
        # 2. Monthly Budget Trends
        plt.figure(figsize=(12, 6))
        monthly_budgets = pd.Series(seasonal_trends['monthly_avg_budget'])
        monthly_budgets = monthly_budgets.reindex(month_order)
        
        sns.barplot(x=monthly_budgets.index, 
                    y=monthly_budgets.values,
                    palette='viridis')
        plt.title('Average Budget by Month')
        plt.xlabel('Month')
        plt.ylabel('Average Budget (USD)')
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on top of bars
        for i, v in enumerate(monthly_budgets.values):
            plt.text(i, v, f'${v:,.0f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('monthly_budget_trends.png')
        plt.close()
        
        # 3. Monthly Group Size Trends
        plt.figure(figsize=(12, 6))
        monthly_group_sizes = pd.Series(seasonal_trends['monthly_group_size'])
        monthly_group_sizes = monthly_group_sizes.reindex(month_order)
        
        sns.lineplot(x=monthly_group_sizes.index,
                     y=monthly_group_sizes.values,
                     marker='o',
                     linewidth=2,
                     markersize=10)
        plt.title('Average Group Size by Month')
        plt.xlabel('Month')
        plt.ylabel('Average Group Size')
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on points
        for i, v in enumerate(monthly_group_sizes.values):
            plt.text(i, v, f'{v:.1f}', ha='center', va='bottom')
        
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig('monthly_group_size_trends.png')
        plt.close()
        
        # 4. Forecast Visualization
        self.visualize_seasonal_forecast(seasonal_trends['monthly_bookings'])

    def visualize_seasonal_forecast(self, monthly_bookings):
        """Create forecast visualization for monthly trends"""
        plt.figure(figsize=(15, 8))
        
        # Convert data to time series
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December']
        ts_data = pd.Series(monthly_bookings).reindex(month_order)
        
        # Plot historical data
        plt.plot(range(len(ts_data)), ts_data.values, 
                 marker='o', label='Historical Data', linewidth=2)
        
        # Simple moving average forecast
        window_size = 3
        ma_forecast = ts_data.rolling(window=window_size, center=True).mean()
        
        # Extend forecast for next 6 months
        last_values = ts_data.values[-window_size:]
        forecast_values = [np.mean(last_values)]
        for _ in range(5):  # Forecast next 5 months
            last_values = np.append(last_values[1:], forecast_values[-1])
            forecast_values.append(np.mean(last_values))
        
        # Plot forecast
        forecast_x = range(len(ts_data)-1, len(ts_data) + len(forecast_values)-1)
        plt.plot(forecast_x, forecast_values, 
                 '--', label='Forecast', linewidth=2, color='red')
        
        # Add confidence interval (simple approach)
        std_dev = ts_data.std()
        upper_bound = np.array(forecast_values) + std_dev
        lower_bound = np.array(forecast_values) - std_dev
        plt.fill_between(forecast_x, lower_bound, upper_bound, 
                         alpha=0.2, color='red', label='Confidence Interval')
        
        plt.title('Monthly Visitors Forecast')
        plt.xlabel('Month')
        plt.ylabel('Number of Visitors')
        plt.legend()
        
        # Customize x-axis labels
        all_months = month_order + [f'Next {i+1}' for i in range(len(forecast_values)-1)]
        plt.xticks(range(len(all_months)), 
                   all_months,
                   rotation=45,
                   ha='right')
        
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig('seasonal_forecast.png')
        plt.close()

    def generate_preference_report(self):
        """Generate a complete preference analysis report"""
        print("Starting preference analysis...")
        
        # Extract and transform data
        df = self.extract_data()
        df = self.transform_data(df)
        
        # Analyze preferences
        preference_data = self.analyze_preferences(df)
        correlations = self.analyze_preference_correlations(df)
        
        # Generate visualizations
        self.visualize_preferences(preference_data)
        
        # Print report
        print("\nPreference Analysis Results:")
        print("--------------------------")
        print("\nTop 5 Preferences:")
        top_5 = dict(sorted(preference_data['preference_counts'].items(), 
                          key=lambda x: x[1], reverse=True)[:5])
        for pref, count in top_5.items():
            print(f"- {pref}: {count} users ({preference_data['preference_percentages'][pref]:.1f}%)")
        
        print("\nPreferences by Group Type:")
        for group, prefs in preference_data['preferences_by_group'].items():
            print(f"\n{group}:")
            top_group_prefs = dict(sorted(prefs.items(), key=lambda x: x[1], reverse=True)[:3])
            for pref, pct in top_group_prefs.items():
                print(f"- {pref}: {pct:.1f}%")
        
        print("\nAverage Budget by Top Preferences:")
        for pref, avg_budget in dict(sorted(correlations['avg_budget_by_preference'].items(), 
                                          key=lambda x: x[1], reverse=True)[:5]).items():
            print(f"- {pref}: ${avg_budget:,.2f}")
        
        print("\nGenerated visualization files:")
        print("- preference_distribution.png")
        print("- preferences_by_group_heatmap.png")
        print("- top_preferences_pie.png")
        print("- budget_by_preference.png")
        
        return {
            'preference_data': preference_data,
            'correlations': correlations
        }

    def generate_extended_report(self):
        """Generate an extended analysis report including group patterns and seasonal trends"""
        print("Starting extended analysis...")
        
        # Extract and transform data
        df = self.extract_data()
        df = self.transform_data(df)
        
        # Generate key metrics visualizations
        self.visualize_key_metrics(df)
        
        # Basic preference analysis
        preference_data = self.analyze_preferences(df)
        correlations = self.analyze_preference_correlations(df)
        
        # Additional analyses
        group_patterns = self.analyze_group_patterns(df)
        seasonal_trends = self.analyze_seasonal_trends(df)
        
        # Generate all visualizations
        self.visualize_preferences(preference_data)
        self.visualize_group_patterns(group_patterns)
        self.visualize_seasonal_trends(seasonal_trends)
        
        # Print extended report
        print("\nExtended Analysis Results:")
        print("========================")
        
        print("\nGroup Pattern Analysis:")
        print("---------------------")
        for group, patterns in group_patterns['top_preferences'].items():
            print(f"\n{group}:")
            print(f"Average Duration: {group_patterns['avg_duration'][group]:.1f} days")
            print(f"Average Budget: ${group_patterns['avg_budget'][group]:,.2f}")
            print("Top Preferences:")
            for pref, count in patterns:
                print(f"- {pref}: {count} occurrences")
        
        print("\nSeasonal Trends:")
        print("---------------")
        for month in sorted(seasonal_trends['monthly_bookings'].keys()):
            print(f"\nMonth {month}:")
            print(f"Bookings: {seasonal_trends['monthly_bookings'][month]}")
            print(f"Average Budget: ${seasonal_trends['monthly_avg_budget'].get(month, 0):,.2f}")
            if month in seasonal_trends['monthly_preferences']:
                print("Top Preferences:")
                for pref, count in seasonal_trends['monthly_preferences'][month]:
                    print(f"- {pref}: {count} occurrences")
        
        print("\nKey Metrics:")
        print("-----------")
        print(f"Total Interactions: {len(df)}")
        print(f"Average Budget: ${df['budget_value'].mean():,.2f}")
        print(f"Average Duration: {df['duration_days'].mean():.1f} days")
        print(f"Average Group Size: {df['group_size'].mean():.1f} people")
        
        print("\nGenerated visualization files:")
        print("- key_metrics_summary.png")
        print("- top_preferences_count.png")
        print("- distributions.png")
        print("- preference_distribution.png")
        print("- preferences_by_group_heatmap.png")
        print("- top_preferences_pie.png")
        print("- budget_by_preference.png")
        print("- group_duration.png")
        print("- group_budget.png")
        print("- monthly_bookings.png")
        print("- monthly_budget.png")
        
        return {
            'preference_data': preference_data,
            'correlations': correlations,
            'group_patterns': group_patterns,
            'seasonal_trends': seasonal_trends
        }

    def visualize_key_metrics(self, df):
        """Create visualizations for key metrics"""
        # 1. Key Metrics Summary Box
        plt.figure(figsize=(12, 6))
        plt.text(0.5, 0.8, f"Total Interactions: {len(df)}", 
                 horizontalalignment='center', fontsize=14)
        plt.text(0.5, 0.6, f"Average Budget: ${df['budget_value'].mean():,.2f}", 
                 horizontalalignment='center', fontsize=14)
        plt.text(0.5, 0.4, f"Average Duration: {df['duration_days'].mean():.1f} days", 
                 horizontalalignment='center', fontsize=14)
        plt.text(0.5, 0.2, f"Average Group Size: {df['group_size'].mean():.1f} people", 
                 horizontalalignment='center', fontsize=14)
        plt.axis('off')
        plt.title('Key Metrics Summary', pad=20, fontsize=16)
        plt.savefig('key_metrics_summary.png')
        plt.close()

        # 2. Top Preferences Bar Chart with Percentages
        preferences_list = []
        for prefs in df['preferences'].dropna():
            preferences_list.extend([p.strip() for p in prefs.split(',')])
        
        top_preferences = pd.Series(preferences_list).value_counts().head(5)
        total_prefs = len(preferences_list)
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(top_preferences.index, top_preferences.values)
        plt.title('Top 5 User Preferences')
        plt.xlabel('Preferences')
        plt.ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        
        # Add percentage labels on top of each bar
        for bar in bars:
            height = bar.get_height()
            percentage = (height/total_prefs) * 100
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{percentage:.1f}%',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('top_preferences_count.png')
        plt.close()

        # 3. Distribution Plots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Budget Distribution
        sns.histplot(data=df, x='budget_value', bins=20, ax=ax1)
        ax1.set_title('Budget Distribution')
        ax1.set_xlabel('Budget (USD)')
        ax1.set_ylabel('Count')
        
        # Duration Distribution
        sns.histplot(data=df, x='duration_days', bins=range(1, int(df['duration_days'].max()) + 2), ax=ax2)
        ax2.set_title('Trip Duration Distribution')
        ax2.set_xlabel('Number of Days')
        ax2.set_ylabel('Count')
        
        plt.tight_layout()
        plt.savefig('distributions.png')
        plt.close()

if __name__ == "__main__":
    analyzer = InteractionAnalyzer()
    analyzer.generate_extended_report() 