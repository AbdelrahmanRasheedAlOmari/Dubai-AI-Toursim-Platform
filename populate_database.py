import sqlite3
import random
from datetime import datetime, timedelta
import json

class DatabasePopulator:
    def __init__(self):
        self.db_name = "dubai_tourism.db"
        self.preferences = [
            "Cultural Experiences", "Adventure Activities", "Luxury Shopping",
            "Desert Safaris", "Beach Activities", "Theme Parks", "Historical Sites",
            "Food Tours", "Water Sports", "Nightlife", "Architecture Tours",
            "Traditional Markets", "Wildlife Encounters", "Spa & Wellness",
            "Photography Tours", "Art Galleries", "Musical Events", "Sports Events"
        ]
        
        self.locations = [
            "Burj Khalifa", "Dubai Mall", "Palm Jumeirah", "Dubai Marina",
            "Old Dubai", "Dubai Creek", "Jumeirah Beach", "Dubai Museum",
            "Gold Souk", "Miracle Garden", "Dubai Frame", "Global Village",
            "Atlantis Aquaventure", "Desert Conservation Reserve", "La Mer",
            "Al Fahidi Historical District", "Dubai Opera", "Madinat Jumeirah"
        ]
        
        self.group_types = [
            "Solo Traveler", "Couple", "Family with 2 kids", "Family with 3 kids",
            "Group of 4 friends", "Group of 6 friends", "Extended family of 8",
            "Honeymoon couple", "Business group of 3", "Senior couple",
            "Multi-generational family of 5", "Solo business traveler"
        ]

    def generate_random_date(self):
        """Generate a random date throughout 2024"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        random_date = start_date + timedelta(days=random_number_of_days)
        return random_date

    def generate_itinerary(self):
        """Generate a random itinerary"""
        num_days = random.randint(2, 7)
        itinerary = {
            "itinerary": []
        }
        
        for day in range(num_days):
            activities = []
            num_activities = random.randint(2, 4)
            
            for _ in range(num_activities):
                location = random.choice(self.locations)
                activity = random.choice(self.preferences)
                activities.append(f"- ACTIVITY: {activity}\n- LOCATION: {location}\n- TIME: {random.choice(['Morning', 'Afternoon', 'Evening'])}")
            
            itinerary["itinerary"].append({
                "day": f"Day {day + 1}",
                "activities": activities
            })
        
        return json.dumps(itinerary)

    def generate_conversation(self):
        """Generate a random conversation history"""
        messages = [
            {"role": "user", "content": "I'm planning a trip to Dubai"},
            {"role": "assistant", "content": "I'll help you plan your perfect Dubai trip. What are your interests?"},
            {"role": "user", "content": f"I'm interested in {', '.join(random.sample(self.preferences, 3))}"}
        ]
        return json.dumps(messages)

    def populate_database(self, num_entries=1000):
        """Populate the database with random entries for future travel dates"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Set start date for travel dates (November 11, 2024)
            start_travel_date = datetime(2024, 11, 11)
            # Set end date (December 31, 2025 for example)
            end_travel_date = datetime(2025, 12, 31)
            
            # Current date for created_at
            current_date = datetime.now()
            
            seasonal_weights = {
                1: 1.2,  # High season (New Year)
                2: 1.1,  # High season
                3: 1.0,  # Moderate
                4: 0.8,  # Lower season
                5: 0.7,  # Low season (Ramadan)
                6: 0.6,  # Low season (Summer)
                7: 0.6,  # Low season (Summer)
                8: 0.7,  # Low season (Summer)
                9: 0.9,  # Starting to increase
                10: 1.0,  # Moderate
                11: 1.1,  # High season
                12: 1.3   # Peak season
            }
            
            entries_per_month = {month: int(num_entries * weight / sum(seasonal_weights.values()))
                                for month, weight in seasonal_weights.items()}
            
            for month, num_entries in entries_per_month.items():
                for _ in range(num_entries):
                    # Generate random created_at date (between now and 3 months ago)
                    random_days_ago = random.randint(0, 90)
                    created_date = current_date - timedelta(days=random_days_ago)
                    
                    # Generate random travel_dates (between Nov 11, 2024 and end date)
                    days_range = (end_travel_date - start_travel_date).days
                    random_days = random.randint(0, days_range)
                    travel_dates = start_travel_date + timedelta(days=random_days)
                    
                    group_info = random.choice(self.group_types)
                    num_preferences = random.randint(2, 5)
                    preferences = ", ".join(random.sample(self.preferences, num_preferences))
                    
                    # Adjust budgets based on travel month
                    travel_month = travel_dates.month
                    base_budget = random.randint(1000, 15000)
                    if travel_month in [12, 1, 2]:  # Peak season
                        budget = base_budget * random.uniform(1.2, 1.5)
                    elif travel_month in [6, 7, 8]:  # Low season
                        budget = base_budget * random.uniform(0.7, 0.9)
                    else:
                        budget = base_budget
                    
                    budget = f"${int(budget)}"
                    
                    # Duration tends to be longer in low season
                    if travel_month in [6, 7, 8]:
                        duration = f"{random.randint(5, 14)} days"
                    else:
                        duration = f"{random.randint(3, 10)} days"
                    
                    cursor.execute("""
                        INSERT INTO interactions (
                            created_at, travel_dates, group_info, preferences, budget, duration,
                            conversation_history, generated_itinerary
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        created_date.strftime('%Y-%m-%d %H:%M:%S'),
                        travel_dates.strftime('%Y-%m-%d'),
                        group_info,
                        preferences,
                        budget,
                        duration,
                        self.generate_conversation(),
                        self.generate_itinerary()
                    ))
            
            conn.commit()
            print(f"Successfully added entries with future travel dates starting from Nov 11, 2024")
            
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        
        finally:
            if conn:
                conn.close()
                print("Database connection closed")

if __name__ == "__main__":
    populator = DatabasePopulator()
    populator.populate_database(1000) 