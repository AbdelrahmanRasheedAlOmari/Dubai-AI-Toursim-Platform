import sqlite3
import json
from datetime import datetime, timedelta
import random

class SampleDataGenerator:
    def __init__(self):
        self.db_name = "dubai_tourism.db"
        self.attractions = [
            {
                "title": "Burj Khalifa Observation Deck",
                "description": "Experience breathtaking views from the world's tallest building",
                "location": "Downtown Dubai",
                "price_range": (200, 400)
            },
            {
                "title": "Desert Safari Adventure",
                "description": "Thrilling dune bashing and traditional desert experience",
                "location": "Dubai Desert Conservation Reserve",
                "price_range": (300, 600)
            },
            {
                "title": "Dubai Mall Shopping",
                "description": "Explore the world's largest shopping mall",
                "location": "Downtown Dubai",
                "price_range": (0, 0)
            },
            {
                "title": "Palm Jumeirah Tour",
                "description": "Visit the iconic man-made island",
                "location": "Palm Jumeirah",
                "price_range": (150, 300)
            },
            {
                "title": "Dubai Marina Yacht Tour",
                "description": "Luxury yacht cruise along Dubai Marina",
                "location": "Dubai Marina",
                "price_range": (400, 800)
            },
            {
                "title": "Gold Souk Visit",
                "description": "Traditional market featuring gold jewelry",
                "location": "Deira",
                "price_range": (0, 0)
            },
            {
                "title": "Atlantis Aquaventure",
                "description": "Exciting water park adventures",
                "location": "Palm Jumeirah",
                "price_range": (250, 450)
            },
            {
                "title": "Dubai Frame Visit",
                "description": "Iconic architectural landmark with city views",
                "location": "Zabeel Park",
                "price_range": (150, 250)
            }
        ]
        
        self.preferences = [
            "shopping and luxury experiences",
            "cultural and traditional activities",
            "adventure and outdoor activities",
            "family-friendly attractions",
            "beach and water activities",
            "architectural landmarks",
            "desert experiences",
            "fine dining and entertainment"
        ]
        
        self.group_types = [
            "solo traveler",
            "couple on honeymoon",
            "family with 2 kids",
            "group of 4 friends",
            "business traveler",
            "family of 5",
            "couple celebrating anniversary",
            "group of 6 colleagues"
        ]

    def generate_itinerary(self, num_days):
        itinerary = []
        used_attractions = set()
        
        for day in range(1, num_days + 1):
            activities = []
            day_attractions = random.sample(self.attractions, 3)  # 3 activities per day
            
            for idx, attraction in enumerate(day_attractions):
                time = f"{9 + idx*3:02d}:00 AM" if idx < 2 else f"{3 + idx:02d}:00 PM"
                price = random.randint(*attraction["price_range"])
                
                activity = (
                    f"- TIME: {time}\n"
                    f"- TITLE: {attraction['title']}\n"
                    f"- DESCRIPTION: {attraction['description']}\n"
                    f"- LOCATION: {attraction['location']}\n"
                    f"- PRICE: AED {price} per person"
                )
                activities.append(activity)
            
            itinerary.append({
                "day": day,
                "activities": activities
            })
        
        recommendations = [
            "Weather Considerations: Best to visit outdoor attractions in the morning",
            "Cultural Etiquette: Dress modestly when visiting traditional areas",
            "Transportation Tips: Use the Dubai Metro for convenient travel",
            "Must-Try Experiences: Don't miss the traditional Arabian dining"
        ]
        
        return {"itinerary": itinerary, "recommendations": recommendations}

    def generate_sample_data(self, num_records=100):
        """Generate sample interaction records"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Generate records over the last 60 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        for _ in range(num_records):
            # Generate random date
            random_days = random.randint(0, 60)
            interaction_date = end_date - timedelta(days=random_days)
            
            # Generate random data
            duration = random.randint(2, 7)
            budget = random.randint(1000, 10000)
            preferences = random.sample(self.preferences, random.randint(1, 3))
            group_info = random.choice(self.group_types)
            
            # Generate itinerary
            itinerary = self.generate_itinerary(duration)
            
            # Store in database
            cursor.execute('''
                INSERT INTO interactions (
                    session_id,
                    travel_dates,
                    duration,
                    group_info,
                    preferences,
                    budget,
                    conversation_history,
                    generated_itinerary,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"sample_session_{_}",
                (interaction_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                str(duration),
                group_info,
                ", ".join(preferences),
                f"USD {budget}",
                json.dumps(["Sample conversation"]),
                json.dumps(itinerary),
                interaction_date.strftime("%Y-%m-%d %H:%M:%S")
            ))
        
        conn.commit()
        conn.close()
        print(f"Generated {num_records} sample records")

if __name__ == "__main__":
    generator = SampleDataGenerator()
    generator.generate_sample_data(num_records=100)  # Generate 100 sample records 