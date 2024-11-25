import sqlite3
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json

class DemandForecaster:
    def __init__(self):
        self.db_name = "dubai_tourism.db"
        
    def extract_attraction_data(self):
        """Extract and process attraction data from interactions"""
        conn = sqlite3.connect(self.db_name)
        
        # Get all interactions
        df = pd.read_sql_query("""
            SELECT created_at, generated_itinerary
            FROM interactions
            WHERE generated_itinerary IS NOT NULL
        """, conn)
        
        conn.close()
        
        # Process the data
        attraction_counts = {}
        
        for _, row in df.iterrows():
            date = pd.to_datetime(row['created_at']).date()
            itinerary = json.loads(row['generated_itinerary'])
            
            if 'itinerary' in itinerary:
                for day in itinerary['itinerary']:
                    for activity in day['activities']:
                        if isinstance(activity, str):
                            activity_lines = activity.split('\n')
                            title = None
                            for line in activity_lines:
                                if line.strip().startswith('- TITLE:'):
                                    title = line.replace('- TITLE:', '').strip()
                                    break
                            
                            if title:
                                if date not in attraction_counts:
                                    attraction_counts[date] = {}
                                if title not in attraction_counts[date]:
                                    attraction_counts[date][title] = 0
                                attraction_counts[date][title] += 1
        
        # Convert to DataFrame
        records = []
        for date, attractions in attraction_counts.items():
            for attraction, count in attractions.items():
                records.append({
                    'ds': date,
                    'attraction': attraction,
                    'y': count
                })
        
        return pd.DataFrame(records)
    
    def train_forecast_model(self, df, attraction):
        """Train Prophet model for a specific attraction"""
        # Filter data for the specific attraction
        attraction_df = df[df['attraction'] == attraction][['ds', 'y']]
        
        # Create and train Prophet model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        model.fit(attraction_df)
        
        return model
    
    def generate_forecast(self, model, periods=30):
        """Generate forecast for future periods"""
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        return forecast
    
    def plot_forecast(self, model, forecast, attraction_name):
        """Plot the forecast results"""
        plt.figure(figsize=(12, 8))
        
        # Plot actual vs predicted
        model.plot(forecast, uncertainty=True)
        plt.title(f'Demand Forecast for {attraction_name}')
        plt.xlabel('Date')
        plt.ylabel('Number of Visits')
        plt.tight_layout()
        plt.savefig(f'forecast_{attraction_name.lower().replace(" ", "_")}.png')
        plt.close()
        
        # Plot components
        plt.figure(figsize=(12, 10))
        model.plot_components(forecast)
        plt.tight_layout()
        plt.savefig(f'components_{attraction_name.lower().replace(" ", "_")}.png')
        plt.close()
    
    def analyze_top_attractions(self, n_attractions=5, forecast_days=30):
        """Analyze and forecast demand for top attractions"""
        print("Starting demand forecasting analysis...")
        
        # Extract data
        df = self.extract_attraction_data()
        
        # Get top attractions by total visits
        top_attractions = (
            df.groupby('attraction')['y']
            .sum()
            .sort_values(ascending=False)
            .head(n_attractions)
            .index
            .tolist()
        )
        
        results = {}
        
        for attraction in top_attractions:
            print(f"\nAnalyzing: {attraction}")
            
            try:
                # Train model
                model = self.train_forecast_model(df, attraction)
                
                # Generate forecast
                forecast = self.generate_forecast(model, periods=forecast_days)
                
                # Plot results
                self.plot_forecast(model, forecast, attraction)
                
                # Store results
                results[attraction] = {
                    'current_demand': df[df['attraction'] == attraction]['y'].mean(),
                    'forecast_mean': forecast.tail(forecast_days)['yhat'].mean(),
                    'forecast_trend': 'Increasing' if forecast.tail(forecast_days)['trend'].is_monotonic_increasing else 'Decreasing'
                }
                
                print(f"Generated forecast for {attraction}")
                
            except Exception as e:
                print(f"Error forecasting {attraction}: {str(e)}")
        
        # Print summary
        print("\nForecast Summary:")
        print("-----------------")
        for attraction, metrics in results.items():
            print(f"\n{attraction}:")
            print(f"Current Average Demand: {metrics['current_demand']:.2f} visits per day")
            print(f"Forecasted Average Demand: {metrics['forecast_mean']:.2f} visits per day")
            print(f"Trend: {metrics['forecast_trend']}")
        
        return results

if __name__ == "__main__":
    forecaster = DemandForecaster()
    forecaster.analyze_top_attractions() 