# Dubai Tourism AI Assistant & Analytics Dashboard

<p align="center">
  <img src="'/Users/abdelrahmanalomari/Desktop/Screenshot 2024-11-25 at 5.12.41 PM.png'" alt="Dubai Tourism AI" width="200"/>
</p>

An advanced AI-powered tourism platform combining an intelligent chatbot for personalized travel planning with comprehensive analytics for tourism insights in Dubai.

## 🌟 Features

### AI Travel Assistant
- **Intelligent Conversation**: Natural language processing for human-like interactions
- **Personalized Itineraries**: Custom travel plans based on preferences, budget, and duration
- **Hotel Recommendations**: Smart hotel suggestions matching user requirements
- **Activity Planning**: Curated activities with detailed pricing and timing
- **Cultural Insights**: Local tips and cultural recommendations
- **Multi-language Support**: Assistance in English, Russian, and Chinese

### Analytics Dashboard
- **Real-time Tourism Analytics**: Live tracking of tourism patterns
- **Seasonal Trend Analysis**: Comprehensive seasonal tourism data
- **Preference Mapping**: Tourist preference visualization
- **Budget Analysis**: Spending pattern insights
- **Group Dynamics**: Visitor group size and type analysis
- **Predictive Analytics**: Future tourism trend forecasting

## 🛠 Technology Stack
### Backend
- **FastAPI**: High-performance API framework
- **LangChain**: AI chain operations and prompt management
- **OpenAI GPT-4**: Natural language processing
- **SQLite**: Data persistence
- **Python**: Core backend language
  
### Frontend
- **HTML/CSS/JavaScript**: Core frontend technologies
- **TailwindCSS**: Utility-first CSS framework
- **Lucide Icons**: Modern icon system

  
### Analytics
- **Streamlit**: Dashboard interface
- **Plotly**: Interactive visualizations
- **Pandas & NumPy**: Data processing
- **Prophet**: Time series forecasting

### Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/dubai-tourism-ai.git
cd dubai-tourism-ai

### Running the Application

1. Start the AI Travel Assistant:
```bash
python main.py

The chatbot will be available at http://localhost:8080

###2. Launch the Analytics Dashboard:
streamlit run dashboard.py


The dashboard will open automatically in your default browser at http://localhost:8501

###Prerequisites
Before running the application, ensure you have installed all required dependencies:

pip install -r requirements.txt
Note: Make sure you have set up your environment variables in .env file with your API keys before running the application.