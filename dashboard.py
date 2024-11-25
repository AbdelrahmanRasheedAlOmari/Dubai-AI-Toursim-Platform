import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analyze_interactions import InteractionAnalyzer
from forecast_demand import DemandForecaster
import json
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

class DashboardApp:
    def __init__(self):
        self.analyzer = InteractionAnalyzer()
        self.forecaster = DemandForecaster()
        
    def run(self):
        st.set_page_config(page_title="Dubai Tourism Analytics", layout="wide")
        
        # Header
        st.title("Dubai Tourism Analytics Dashboard")
        
        # Sidebar for navigation
        page = st.sidebar.selectbox(
            "Select Analysis",
            ["Overview", "Real-Time Analytics", "Demand Forecast", "User Preferences", 
             "Group Analysis", "Seasonal Trends"]
        )
        
        try:
            # Load data
            with st.spinner('Loading data...'):
                df = self.analyzer.extract_data()
                df = self.analyzer.transform_data(df)
            
            if page == "Overview":
                self.show_overview(df)
            elif page == "Real-Time Analytics":
                self.show_realtime_analytics(df)
            elif page == "Demand Forecast":
                self.show_demand_forecast(df)
            elif page == "User Preferences":
                self.show_preference_analysis(df)
            elif page == "Group Analysis":
                self.show_group_analysis(df)
            else:
                self.show_seasonal_analysis(df)
                
        except Exception as e:
            st.error(f"Error loading dashboard: {str(e)}")
            st.write("Please try again or contact support if the error persists.")

    def show_overview(self, df):
        st.header("Key Metrics Overview")
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Interactions", f"{len(df):,}")
        with col2:
            st.metric("Average Budget", f"${df['budget_value'].mean():,.2f}")
        with col3:
            st.metric("Average Duration", f"{df['duration_days'].mean():.1f} days")
        with col4:
            st.metric("Average Group Size", f"{df['group_size'].mean():.1f}")

        # Recent trends
        st.subheader("Recent Activity")
        recent_df = df.sort_values('created_at').tail(30)
        fig = px.line(recent_df, x='created_at', y='budget_value',
                     title="Recent Booking Trends")
        st.plotly_chart(fig, use_container_width=True)

        # Top preferences summary
        preferences_list = []
        for prefs in df['preferences'].dropna():
            preferences_list.extend([p.strip() for p in prefs.split(',')])
        pref_counts = pd.Series(preferences_list).value_counts().head(5)
        
        st.subheader("Top User Preferences")
        fig = px.bar(x=pref_counts.index, y=pref_counts.values)
        st.plotly_chart(fig, use_container_width=True)

    def show_demand_forecast(self, df):
        st.header("Demand Forecast")
        
        try:
            # Add caching to the data loading instead
            @st.cache_data(ttl=3600)
            def load_forecast_data():
                forecaster = DemandForecaster()
                return forecaster.extract_attraction_data()
            
            # Load forecast data using cached function
            with st.spinner('Loading forecast data...'):
                df_forecast = load_forecast_data()
            
            # Select attraction
            attractions = df_forecast['attraction'].unique()
            selected_attraction = st.selectbox(
                "Select Attraction",
                attractions,
                help="Choose an attraction to see its demand forecast"
            )
            
            # Add caching to the forecast generation
            @st.cache_data(ttl=3600)
            def generate_forecast(attraction):
                forecaster = DemandForecaster()
                model = forecaster.train_forecast_model(df_forecast, attraction)
                return forecaster.generate_forecast(model)
            
            # Generate forecast with progress bar
            with st.spinner('Generating forecast...'):
                forecast = generate_forecast(selected_attraction)
            
            # Plot forecast
            fig = go.Figure()
            
            # Actual values
            actual_data = df_forecast[df_forecast['attraction'] == selected_attraction]
            fig.add_trace(go.Scatter(
                x=actual_data['ds'],
                y=actual_data['y'],
                name='Actual Demand',
                mode='markers'
            ))
            
            # Forecast
            fig.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat'],
                name='Forecast',
                mode='lines'
            ))
            
            # Confidence interval
            fig.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat_upper'],
                fill=None,
                mode='lines',
                line_color='rgba(0,100,255,0.2)',
                showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat_lower'],
                fill='tonexty',
                mode='lines',
                line_color='rgba(0,100,255,0.2)',
                name='Confidence Interval'
            ))
            
            # Update layout
            fig.update_layout(
                title=f'Demand Forecast for {selected_attraction}',
                xaxis_title='Date',
                yaxis_title='Number of Visits',
                hovermode='x unified',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Current Demand",
                    f"{actual_data['y'].mean():.1f} visits/day"
                )
            with col2:
                st.metric(
                    "Forecasted Demand",
                    f"{forecast['yhat'].mean():.1f} visits/day"
                )
            with col3:
                trend = "Increasing" if forecast['trend'].is_monotonic_increasing else "Decreasing"
                st.metric("Trend", trend)
                
        except Exception as e:
            st.error(f"Error generating forecast: {str(e)}")

    def show_preference_analysis(self, df):
        st.header("User Preferences Analysis")
        
        # Process preferences
        preferences_list = []
        for prefs in df['preferences'].dropna():
            preferences_list.extend([p.strip() for p in prefs.split(',')])
        
        pref_counts = pd.Series(preferences_list).value_counts()
        
        # Top Preferences
        st.subheader("Top User Preferences")
        fig = px.bar(x=pref_counts.index, y=pref_counts.values)
        st.plotly_chart(fig, use_container_width=True)
        
        # Preferences by Budget
        st.subheader("Average Budget by Preference")
        preference_budgets = self.analyzer.analyze_preference_correlations(df)
        avg_budgets = preference_budgets['avg_budget_by_preference']
        fig = px.bar(x=list(avg_budgets.keys()), y=list(avg_budgets.values()))
        st.plotly_chart(fig, use_container_width=True)

    def show_group_analysis(self, df):
        st.header("Group Analysis")
        
        group_patterns = self.analyzer.analyze_group_patterns(df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Group Size Distribution
            st.subheader("Group Size Distribution")
            fig = px.histogram(df, x='group_size')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Average Duration by Group
            st.subheader("Average Duration by Group Type")
            fig = px.bar(x=list(group_patterns['avg_duration'].keys()),
                        y=list(group_patterns['avg_duration'].values()))
            st.plotly_chart(fig, use_container_width=True)

    def show_seasonal_analysis(self, df):
        try:
            st.header("Seasonal Tourism Intelligence")
            st.markdown("---")

            # Convert travel_dates to datetime if not already
            df['travel_dates'] = pd.to_datetime(df['travel_dates'], format='%Y-%m-%d')
            
            # Extract month from travel_dates
            df['month'] = df['travel_dates'].dt.month
            df['month_name'] = df['travel_dates'].dt.strftime('%B')
            
            # Get seasonal trends data
            seasonal_trends = self.analyzer.analyze_seasonal_trends(df)
            
            if seasonal_trends is None:
                st.error("Error analyzing seasonal trends. Please check the data format.")
                return

            # Create main sections using tabs
            tabs = st.tabs([
                "Preference Analysis",
                "Budget Trends",
                "Group Dynamics",
                "Tourism Forecast"
            ])

            month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December']

            with tabs[0]:
                st.subheader("Tourist Preferences by Travel Month")  # Updated title
                
                # Monthly preferences analysis with sorted months
                preferences_df = pd.DataFrame(seasonal_trends['preference_counts_by_month']).fillna(0)
                preferences_df = preferences_df.reindex(month_order)
                
                # Create bar chart for top preferences by month
                monthly_pref_data = []
                for month in month_order:
                    if month in seasonal_trends['monthly_preferences']:
                        for pref, count in seasonal_trends['monthly_preferences'][month][:5]:  # Top 5 preferences
                            monthly_pref_data.append({
                                'Month': month,
                                'Preference': pref,
                                'Visitors': count
                            })
                
                monthly_pref_df = pd.DataFrame(monthly_pref_data)
                
                # Create grouped bar chart
                fig = px.bar(
                    monthly_pref_df,
                    x='Month',
                    y='Visitors',
                    color='Preference',
                    title="Top Tourist Preferences by Month",
                    barmode='group'
                )
                
                fig.update_layout(
                    height=500,
                    title_x=0.5,
                    title_font_size=20,
                    xaxis_title="Month",
                    yaxis_title="Number of Visitors",
                    xaxis={'tickangle': 45},
                    legend_title="Preference",
                    showlegend=True,
                    legend={'orientation': 'h', 'y': -0.2}  # Horizontal legend at bottom
                )
                st.plotly_chart(fig, use_container_width=True)

                # Enhanced preference insights
                st.subheader("Monthly Preference Analysis")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info("Peak Preferences by Month")
                    # Show top preferences for each month
                    for month in month_order:
                        if month in seasonal_trends['monthly_preferences']:
                            st.write(f"**{month}**")
                            for pref, count in seasonal_trends['monthly_preferences'][month][:3]:
                                st.write(f"• {pref}: {count} visitors")
                            st.write("")  # Add spacing between months

                with col2:
                    st.info("Seasonal Preference Shifts")
                    # Calculate and show significant preference changes
                    preference_shifts = []
                    for pref in preferences_df.index:
                        month_values = preferences_df.loc[pref]
                        # Skip if all values are 0 or NA
                        if month_values.sum() > 0:
                            # Use dropna() to handle NA values
                            max_month = month_values.dropna().idxmax()
                            if month_values[max_month] > 0:  # Only show if preference exists
                                preference_shifts.append(f"• {pref}: Peak in {max_month}")
                
                    if preference_shifts:
                        st.write("\n".join(preference_shifts))
                    else:
                        st.write("No significant seasonal shifts detected")

            with tabs[1]:
                st.subheader("Budget Analysis by Travel Month")  # Updated title
                
                # Monthly budget analysis with sorted months
                monthly_budget_data = pd.DataFrame({
                    'Month': list(seasonal_trends['monthly_avg_budget'].keys()),
                    'Average Budget': list(seasonal_trends['monthly_avg_budget'].values())
                })
                # Sort months chronologically
                monthly_budget_data['Month'] = pd.Categorical(
                    monthly_budget_data['Month'], 
                    categories=month_order, 
                    ordered=True
                )
                monthly_budget_data = monthly_budget_data.sort_values('Month')

                # Create budget trend visualization
                fig = px.bar(
                    monthly_budget_data,
                    x='Month',
                    y='Average Budget',
                    title="Monthly Average Tourist Budget",
                    color='Average Budget',
                    color_continuous_scale="Viridis"
                )
                fig.update_layout(
                    height=500,
                    title_x=0.5,
                    title_font_size=20,
                    xaxis_title="Month",
                    yaxis_title="Average Budget (USD)",
                    showlegend=False,
                    xaxis={'tickangle': 45}  # Angle month labels
                )
                st.plotly_chart(fig, use_container_width=True)

                # Budget insights
                col1, col2, col3 = st.columns(3)
                with col1:
                    if not monthly_budget_data['Average Budget'].isna().all():
                        peak_month = monthly_budget_data.loc[
                            monthly_budget_data['Average Budget'].dropna().idxmax()
                        ]
                        st.metric(
                            "Peak Spending Month",
                            peak_month['Month'],
                            f"${peak_month['Average Budget']:,.2f}"
                        )
                    else:
                        st.metric("Peak Spending Month", "No data", "0")

                with col2:
                    avg_budget = monthly_budget_data['Average Budget'].mean()
                    if pd.notna(avg_budget):
                        st.metric(
                            "Average Monthly Budget",
                            f"${avg_budget:,.2f}",
                            "Year-round average"
                        )
                    else:
                        st.metric("Average Monthly Budget", "No data", "0")

                with col3:
                    if len(monthly_budget_data) >= 2:
                        budget_trend = (
                            monthly_budget_data['Average Budget'].iloc[-1] - 
                            monthly_budget_data['Average Budget'].iloc[0]
                        )
                        if pd.notna(budget_trend):
                            st.metric(
                                "Budget Trend",
                                "Increasing" if budget_trend > 0 else "Decreasing",
                                f"{abs(budget_trend):,.2f} USD"
                            )
                    else:
                        st.metric("Budget Trend", "Insufficient data", "0")

            with tabs[2]:
                st.subheader("Group Size Dynamics by Travel Month")  # Updated title
                
                # Monthly group size analysis with sorted months
                group_size_data = pd.DataFrame({
                    'Month': list(seasonal_trends['monthly_group_size'].keys()),
                    'Average Group Size': list(seasonal_trends['monthly_group_size'].values())
                })
                # Sort months chronologically
                group_size_data['Month'] = pd.Categorical(
                    group_size_data['Month'], 
                    categories=month_order, 
                    ordered=True
                )
                group_size_data = group_size_data.sort_values('Month')

                # Create group size visualization
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=group_size_data['Month'],
                    y=group_size_data['Average Group Size'],
                    mode='lines+markers',
                    line=dict(width=3),
                    marker=dict(size=10)
                ))
                fig.update_layout(
                    title="Monthly Average Group Size Trends",
                    height=500,
                    title_x=0.5,
                    title_font_size=20,
                    xaxis_title="Month",
                    yaxis_title="Average Group Size",
                    showlegend=False,
                    xaxis={'tickangle': 45}  # Angle month labels
                )
                st.plotly_chart(fig, use_container_width=True)

                # Group size insights
                col1, col2 = st.columns(2)
                with col1:
                    st.info("Group Size Patterns")
                    if not group_size_data['Average Group Size'].isna().all():
                        peak_group = group_size_data.loc[
                            group_size_data['Average Group Size'].dropna().idxmax()
                        ]
                        avg_group_size = group_size_data['Average Group Size'].mean()
                        
                        st.write(f"• Peak month: {peak_group['Month']}")
                        st.write(f"• Largest average group: {peak_group['Average Group Size']:.1f} people")
                        st.write(f"• Year-round average: {avg_group_size:.1f} people")
                    else:
                        st.write("No group size data available")

                with col2:
                    st.info("Target Segments")
                    valid_data = group_size_data[group_size_data['Average Group Size'].notna()]
                    family_months = valid_data[valid_data['Average Group Size'] >= 3]['Month'].tolist()
                    if family_months:
                        st.write("Family-focused months:")
                        st.write(", ".join(family_months))
                    else:
                        st.write("No family-focused months identified")

            with tabs[3]:
                st.subheader("Future Tourism Forecast")
                
                # Prepare data for forecasting using travel_dates
                df_forecast = df.copy()
                df_forecast['ds'] = pd.to_datetime(df_forecast['travel_dates'])
                df_forecast['y'] = df_forecast['group_size']
                
                # Create and fit Prophet model
                from prophet import Prophet
                model = Prophet(yearly_seasonality=True, weekly_seasonality=False)
                model.fit(df_forecast[['ds', 'y']])
                
                # Make future dataframe
                future = model.make_future_dataframe(periods=180)  # 6 months forecast
                forecast = model.predict(future)
                
                # Create forecast visualization
                fig = go.Figure()
                
                # Historical data
                fig.add_trace(go.Scatter(
                    x=df_forecast['ds'],
                    y=df_forecast['y'],
                    name='Historical',
                    mode='lines',
                    line=dict(color='blue')
                ))
                
                # Forecast
                fig.add_trace(go.Scatter(
                    x=forecast['ds'],
                    y=forecast['yhat'],
                    name='Forecast',
                    mode='lines',
                    line=dict(color='red', dash='dash')
                ))
                
                # Confidence interval
                fig.add_trace(go.Scatter(
                    x=forecast['ds'].tolist() + forecast['ds'].tolist()[::-1],
                    y=forecast['yhat_upper'].tolist() + forecast['yhat_lower'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(255,0,0,0.2)',
                    line=dict(color='rgba(255,0,0,0)'),
                    name='Confidence Interval'
                ))
                
                fig.update_layout(
                    title="6-Month Tourism Forecast",
                    height=600,
                    title_x=0.5,
                    title_font_size=20,
                    xaxis_title="Date",
                    yaxis_title="Number of Visitors",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)

                # Forecast insights
                st.info("Forecast Insights")
                col1, col2 = st.columns(2)
                
                with col1:
                    growth_rate = ((forecast['yhat'].iloc[-1] - df_forecast['y'].iloc[-1]) / 
                                  df_forecast['y'].iloc[-1] * 100)
                    st.metric(
                        "Projected Growth",
                        f"{growth_rate:+.1f}%",
                        "Next 6 months"
                    )
                
                with col2:
                    peak_forecast = forecast['yhat'].max()
                    peak_date = forecast.loc[forecast['yhat'].idxmax(), 'ds']
                    st.metric(
                        "Peak Period",
                        peak_date.strftime('%B %Y'),
                        f"{peak_forecast:,.0f} visitors"
                    )

                # Strategic recommendations
                st.success("""
                **Strategic Recommendations:**
                1. Prepare for projected visitor increases during peak months
                2. Optimize pricing strategies for high-demand periods
                3. Develop targeted marketing campaigns for off-peak seasons
                4. Align resource allocation with forecasted demand
                """)

        except Exception as e:
            st.error(f"Error in seasonal analysis: {str(e)}")
            st.write("Please check that your data is in the correct format.")

    def show_realtime_analytics(self, df):
        st.header("Tourism Flow Analysis")
        
        # Convert travel_dates to datetime
        df['travel_dates'] = pd.to_datetime(df['travel_dates'])
        
        # Get next 30 days range
        current_date = datetime.now()
        next_30_days = current_date + timedelta(days=30)
        
        # Filter for upcoming travel dates
        upcoming_df = df[df['travel_dates'].between(current_date, next_30_days)]
        
        # Create columns for different metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Expected Visitors (Next 30 Days)")
            total_visitors = upcoming_df['group_size'].sum()
            daily_avg = total_visitors / 30
            
            st.metric(
                "Total Expected Visitors",
                f"{int(total_visitors):,}",
                f"Avg. {int(daily_avg)} per day"
            )

        with col2:
            st.subheader("Average Group Size")
            avg_group = upcoming_df['group_size'].mean()
            
            st.metric(
                "Average Group Size",
                f"{avg_group:.1f}",
                f"From {len(upcoming_df)} bookings"
            )

        with col3:
            st.subheader("Average Budget")
            avg_budget = upcoming_df['budget_value'].mean()
            
            st.metric(
                "Average Spending",
                f"${int(avg_budget):,}",
                "per booking"
            )

        # Create daily visitors visualization
        st.subheader("Daily Visitor Distribution (Next 30 Days)")
        
        daily_visitors = upcoming_df.groupby('travel_dates')['group_size'].sum().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily_visitors['travel_dates'],
            y=daily_visitors['group_size'],
            name='Expected Visitors'
        ))
        
        fig.update_layout(
            title="Expected Daily Visitors",
            xaxis_title="Date",
            yaxis_title="Number of Visitors",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Popular activities analysis
        st.subheader("Upcoming Popular Activities")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Analyze preferences for upcoming visitors
            upcoming_prefs = []
            for prefs in upcoming_df['preferences'].dropna():
                upcoming_prefs.extend([p.strip() for p in prefs.split(',')])
            
            pref_counts = pd.Series(upcoming_prefs).value_counts()
            
            fig = px.pie(
                values=pref_counts.values[:5],
                names=pref_counts.index[:5],
                title="Top 5 Planned Activities"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Group type distribution
            group_dist = upcoming_df['group_info'].value_counts()
            
            fig = px.bar(
                x=group_dist.index,
                y=group_dist.values,
                title="Visitor Group Types",
                labels={'x': 'Group Type', 'y': 'Number of Bookings'}
            )
            fig.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

        # Capacity Planning Insights
        st.subheader("Capacity Planning Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("Peak Days")
            # Find days with highest expected visitors
            peak_days = daily_visitors.nlargest(3, 'group_size')
            for _, row in peak_days.iterrows():
                st.write(f"• {row['travel_dates'].strftime('%B %d')}: {int(row['group_size'])} visitors")

        with col2:
            st.info("Visitor Mix")
            total_groups = len(upcoming_df)
            if total_groups > 0:
                family_groups = len(upcoming_df[upcoming_df['group_info'].str.contains('family', case=False, na=False)])
                business_groups = len(upcoming_df[upcoming_df['group_info'].str.contains('business', case=False, na=False)])
                
                st.write(f"• Families: {family_groups/total_groups*100:.1f}%")
                st.write(f"• Business: {business_groups/total_groups*100:.1f}%")
                st.write(f"• Others: {(total_groups-family_groups-business_groups)/total_groups*100:.1f}%")

if __name__ == "__main__":
    dashboard = DashboardApp()
    dashboard.run()