from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
import json
from database import db  # Add this at the top with your other imports

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Add root route to serve index.html
@app.get("/")
async def read_root():
    return FileResponse('static/index.html')


class UserInput(BaseModel):
    preferences: str
    duration: Optional[int] = None
    budget: Optional[float] = None


class ItineraryResponse(BaseModel):
    itinerary: List[dict]
    recommendations: List[str]
    hotel_suggestion: Optional[dict] = None


# Directly set the API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

print("OpenAI API Key loaded (first 10 chars):", OPENAI_API_KEY[:10], "...")

# Initialize LangChain components with explicit API key
try:
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4o",
        temperature=0.7,
    )

    # Enable LangChain tracing if needed
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY

except Exception as e:
    print(f"Error initializing ChatOpenAI: {str(e)}")
    raise

# Create prompt template for UAE travel expert
uae_expert_prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are Dubai Tourism's official AI guide. When generating the final itinerary, 
    you MUST follow this EXACT format:

    Hotel Suggestion:
    - NAME: [Hotel Name]
    - CATEGORY: [Luxury/Mid-range/Budget]
    - LOCATION: [Area in Dubai]
    - PRICE: AED XXX per night
    - AMENITIES: [Key amenities]
    - DESCRIPTION: [Brief description]
    - RATING: [X/5 stars]

    [Leave a blank line]

    Day 1:
    - TIME: 09:00 AM
    - TITLE: Activity Name
    - DESCRIPTION: Detailed description
    - LOCATION: Specific location
    - PRICE: AED XXX per person

    [Leave a blank line between activities]

    - TIME: 02:00 PM
    - TITLE: Next Activity
    - DESCRIPTION: Detailed description
    - LOCATION: Specific location
    - PRICE: AED XXX per person

    [Continue for each day]

    Recommendations:
    - Weather Considerations: [weather details]
    - Cultural Etiquette: [etiquette details]
    - Transportation Tips: [transport details]
    - Must-Try Experiences: [experience details]

    IMPORTANT:
    - Suggest hotel based on budget and preferences
    - Use exact format with dashes and labels
    - Leave blank line between sections
    - Include all fields for each activity
    - Use 12-hour time format (AM/PM)
    - Include AED prices
    """),
    ("human", """User Input: {preferences}
    Duration: {duration} days
    Budget: {budget} USD
    
    If this is the final stage (after budget), generate a detailed itinerary with hotel suggestion.
    Otherwise, proceed to the next question in sequence.""")
])

# Create LangChain
itinerary_chain = LLMChain(llm=llm, prompt=uae_expert_prompt)

# Add a global dictionary to store conversation state
conversation_states: Dict[str, dict] = {}


@app.post("/api/create-itinerary", response_model=ItineraryResponse)
async def create_itinerary(user_input: UserInput):
    try:
        session_id = "default_session"

        if session_id not in conversation_states:
            conversation_states[session_id] = {
                "travel_dates": None,
                "group_info": None,
                "preferences": None,
                "duration": None,
                "budget": None,
                "conversation_history": []
            }

        state = conversation_states[session_id]

        # Handle system messages (like language selection)
        if user_input.preferences.startswith("SYSTEM:"):
            return ItineraryResponse(itinerary=[{
                "day":
                0,
                "activities": [
                    "Ahlan wa sahlan! Welcome to Dubai Tourism. It is my honor to help you discover the wonders of our beloved city. When would you like to experience Dubai's magic?"
                ]
            }],
                                     recommendations=[])

        # Store the user's input in conversation history
        if not user_input.preferences.startswith("SYSTEM:"):
            state["conversation_history"].append(user_input.preferences)

        try:
            # Process user input based on current state
            if not state["travel_dates"]:
                state["travel_dates"] = user_input.preferences
                return ItineraryResponse(itinerary=[{
                    "day":
                    0,
                    "activities": [
                        "Thank you for choosing Dubai. How many days would you like to spend exploring our city?"
                    ]
                }],
                                         recommendations=[])
            elif not state["duration"]:
                state[
                    "duration"] = user_input.duration or user_input.preferences
                return ItineraryResponse(itinerary=[{
                    "day":
                    0,
                    "activities": [
                        "To ensure we create the perfect experience, may I know who will be joining you on this journey?"
                    ]
                }],
                                         recommendations=[])
            elif not state["group_info"]:
                state["group_info"] = user_input.preferences
                return ItineraryResponse(itinerary=[{
                    "day":
                    0,
                    "activities": [
                        "Dubai offers countless experiences, from traditional souks to modern marvels. What interests you most about our city?"
                    ]
                }],
                                         recommendations=[])
            elif not state["preferences"]:
                state["preferences"] = user_input.preferences
                return ItineraryResponse(itinerary=[{
                    "day":
                    0,
                    "activities": [
                        "To help tailor your experience perfectly, what budget range do you have in mind for your Dubai adventure?"
                    ]
                }],
                                         recommendations=[])
            elif not state["budget"]:
                state["budget"] = user_input.budget or user_input.preferences

                # Now generate the itinerary
                response = itinerary_chain.invoke({
                    "preferences":
                    str(state),
                    "duration":
                    state["duration"],
                    "budget":
                    state["budget"],
                    "conversation_state":
                    json.dumps(state),
                    "conversation_history":
                    "\n".join(state["conversation_history"])
                })

                # Process the response into itinerary format
                content = str(response['text'])
                days = []
                current_day = None
                current_activities = []
                hotel_suggestion = None

                # Extract hotel suggestion if present
                if "Hotel Suggestion:" in content:
                    hotel_part, rest = content.split("Day 1:", 1)
                    hotel_lines = [
                        line.strip() for line in hotel_part.split('\n')
                        if line.strip()
                    ]
                    hotel_data = {}
                    for line in hotel_lines:
                        if line.startswith('- '):
                            key, value = line[2:].split(':', 1)
                            hotel_data[key.strip()] = value.strip()
                    hotel_suggestion = hotel_data
                    content = "Day 1:" + rest

                print("Hotel Suggestion:", hotel_suggestion)  # Debug log

                # Split content into days and recommendations
                if "Recommendations:" in content:
                    main_content, rec_content = content.split(
                        "Recommendations:")
                else:
                    main_content, rec_content = content, ""

                # Process each line
                lines = main_content.split('\n')
                current_activity = []

                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_activity:
                            current_activities.append(
                                '\n'.join(current_activity))
                            current_activity = []
                        continue

                    if line.startswith("Day"):
                        # Save previous day if exists
                        if current_day and current_activities:
                            days.append({
                                "day": current_day,
                                "activities": current_activities
                            })
                        # Start new day
                        try:
                            current_day = int(line.split()[1].replace(":", ""))
                            current_activities = []
                            current_activity = []
                        except:
                            continue
                    elif line.startswith("-"):
                        # If we have a previous activity, save it
                        if current_activity:
                            current_activities.append(
                                '\n'.join(current_activity))
                            current_activity = []
                        # Start new activity
                        current_activity = [line]
                    elif current_activity:
                        # Add line to current activity
                        current_activity.append(line)

                # Add final activity and day if exists
                if current_activity:
                    current_activities.append('\n'.join(current_activity))
                if current_day and current_activities:
                    days.append({
                        "day": current_day,
                        "activities": current_activities
                    })

                # Process recommendations
                recommendations = []
                if rec_content:
                    recommendations = [
                        line.strip("- ").strip()
                        for line in rec_content.split('\n')
                        if line.strip() and line.strip().startswith("-")
                    ]

                # Debug logging
                print("Processed days:", days)
                print("Processed recommendations:", recommendations)

                # Store the interaction data
                db.store_interaction({
                    'session_id':
                    session_id,
                    'travel_dates':
                    state["travel_dates"],
                    'duration':
                    state["duration"],
                    'group_info':
                    state["group_info"],
                    'preferences':
                    state["preferences"],
                    'budget':
                    state["budget"],
                    'conversation_history':
                    state["conversation_history"],
                    'generated_itinerary': {
                        "itinerary": days,
                        "recommendations": recommendations
                    }
                })

                return ItineraryResponse(itinerary=days,
                                         recommendations=recommendations,
                                         hotel_suggestion=hotel_suggestion)
        except Exception as inner_e:
            print(f"Inner error: {str(inner_e)}")
            return ItineraryResponse(itinerary=[{
                "day":
                0,
                "activities": [
                    "I apologize, but I encountered an error processing your response. Please try again."
                ]
            }],
                                     recommendations=[],
                                     hotel_suggestion=None)

    except Exception as e:
        print(f"Error generating itinerary: {str(e)}")
        return ItineraryResponse(itinerary=[{
            "day":
            0,
            "activities":
            ["I apologize, but I encountered an error. Please try again."]
        }],
                                 recommendations=[],
                                 hotel_suggestion=None)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
