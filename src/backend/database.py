"""
MongoDB database configuration and setup for Mergington High School API
"""

from pymongo import MongoClient
from argon2 import PasswordHasher

# Mock collection class for when MongoDB is not available
class MockCollection:
    def __init__(self, initial_data=None):
        self._data = initial_data or {}
    
    def find(self, query=None):
        if query is None:
            for key, value in self._data.items():
                yield {"_id": key, **value}
        else:
            # Simple query handling for day filter
            for key, value in self._data.items():
                if self._matches_query(value, query):
                    yield {"_id": key, **value}
    
    def find_one(self, query):
        if isinstance(query, dict) and "_id" in query:
            item_id = query["_id"]
            if item_id in self._data:
                return {"_id": item_id, **self._data[item_id]}
        return None
    
    def insert_one(self, document):
        if "_id" in document:
            item_id = document.pop("_id")
            self._data[item_id] = document
            return type('Result', (), {'acknowledged': True})()
        return type('Result', (), {'acknowledged': False})()
    
    def update_one(self, query, update):
        if isinstance(query, dict) and "_id" in query:
            item_id = query["_id"]
            if item_id in self._data:
                if "$push" in update:
                    for field, value in update["$push"].items():
                        if field in self._data[item_id]:
                            self._data[item_id][field].append(value)
                        else:
                            self._data[item_id][field] = [value]
                if "$pull" in update:
                    for field, value in update["$pull"].items():
                        if field in self._data[item_id] and value in self._data[item_id][field]:
                            self._data[item_id][field].remove(value)
                return type('Result', (), {'modified_count': 1})()
        return type('Result', (), {'modified_count': 0})()
    
    def count_documents(self, query=None):
        return len(self._data)
    
    def _matches_query(self, value, query):
        # Handle complex MongoDB query syntax
        for field, condition in query.items():
            if field == "schedule_details.days":
                if "schedule_details" in value and "days" in value["schedule_details"]:
                    if isinstance(condition, dict) and "$in" in condition:
                        # Handle $in operator: check if any day in condition["$in"] is in value["schedule_details"]["days"]
                        requested_days = condition["$in"]
                        activity_days = value["schedule_details"]["days"]
                        if not any(day in activity_days for day in requested_days):
                            return False
                    elif isinstance(condition, str):
                        # Handle direct string comparison
                        if condition not in value["schedule_details"]["days"]:
                            return False
                else:
                    return False
            elif field == "schedule_details.start_time":
                if "schedule_details" in value and "start_time" in value["schedule_details"]:
                    activity_start = value["schedule_details"]["start_time"]
                    if isinstance(condition, dict) and "$gte" in condition:
                        if activity_start < condition["$gte"]:
                            return False
                    elif isinstance(condition, str):
                        if activity_start < condition:
                            return False
                else:
                    return False
            elif field == "schedule_details.end_time":
                if "schedule_details" in value and "end_time" in value["schedule_details"]:
                    activity_end = value["schedule_details"]["end_time"]
                    if isinstance(condition, dict) and "$lte" in condition:
                        if activity_end > condition["$lte"]:
                            return False
                    elif isinstance(condition, str):
                        if activity_end > condition:
                            return False
                else:
                    return False
        return True

# Try to connect to MongoDB, fallback to mock if not available
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=1000)
    # Test connection
    client.admin.command('ping')
    db = client['mergington_high']
    activities_collection = db['activities']
    teachers_collection = db['teachers']
    print("Connected to MongoDB successfully")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    print("Using mock database for development")
    activities_collection = MockCollection()
    teachers_collection = MockCollection()

# Methods
def hash_password(password):
    """Hash password using Argon2"""
    ph = PasswordHasher()
    return ph.hash(password)

def init_database():
    """Initialize database if empty"""

    # Initialize activities if empty
    try:
        if activities_collection.count_documents({}) == 0:
            for name, details in initial_activities.items():
                activities_collection.insert_one({"_id": name, **details})
                
        # Initialize teacher accounts if empty
        if teachers_collection.count_documents({}) == 0:
            for teacher in initial_teachers:
                teachers_collection.insert_one({"_id": teacher["username"], **teacher})
    except Exception as e:
        print(f"Database initialization error: {e}")
        # For mock collections, initialize directly
        if hasattr(activities_collection, '_data'):
            activities_collection._data = initial_activities.copy()
        if hasattr(teachers_collection, '_data'):
            teachers_data = {}
            for teacher in initial_teachers:
                teachers_data[teacher["username"]] = {k: v for k, v in teacher.items() if k != "username"}
            teachers_collection._data = teachers_data

# Initial database if empty
initial_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Mondays and Fridays, 3:15 PM - 4:45 PM",
        "schedule_details": {
            "days": ["Monday", "Friday"],
            "start_time": "15:15",
            "end_time": "16:45"
        },
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 7:00 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "07:00",
            "end_time": "08:00"
        },
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Morning Fitness": {
        "description": "Early morning physical training and exercises",
        "schedule": "Mondays, Wednesdays, Fridays, 6:30 AM - 7:45 AM",
        "schedule_details": {
            "days": ["Monday", "Wednesday", "Friday"],
            "start_time": "06:30",
            "end_time": "07:45"
        },
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and compete in basketball tournaments",
        "schedule": "Wednesdays and Fridays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Wednesday", "Friday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore various art techniques and create masterpieces",
        "schedule": "Thursdays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Thursday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Monday", "Wednesday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and prepare for math competitions",
        "schedule": "Tuesdays, 7:15 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "07:15",
            "end_time": "08:00"
        },
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Friday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "amelia@mergington.edu"]
    },
    "Weekend Robotics Workshop": {
        "description": "Build and program robots in our state-of-the-art workshop",
        "schedule": "Saturdays, 10:00 AM - 2:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "10:00",
            "end_time": "14:00"
        },
        "max_participants": 15,
        "participants": ["ethan@mergington.edu", "oliver@mergington.edu"]
    },
    "Science Olympiad": {
        "description": "Weekend science competition preparation for regional and state events",
        "schedule": "Saturdays, 1:00 PM - 4:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "13:00",
            "end_time": "16:00"
        },
        "max_participants": 18,
        "participants": ["isabella@mergington.edu", "lucas@mergington.edu"]
    },
    "Sunday Chess Tournament": {
        "description": "Weekly tournament for serious chess players with rankings",
        "schedule": "Sundays, 2:00 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Sunday"],
            "start_time": "14:00",
            "end_time": "17:00"
        },
        "max_participants": 16,
        "participants": ["william@mergington.edu", "jacob@mergington.edu"]
    },
    "Manga Maniacs": {
        "description": "Explore the fantastic stories of the most interesting characters from Japanese Manga (graphic novels).",
        "schedule": "Tuesdays, 7:00 PM - 8:30 PM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "19:00",
            "end_time": "20:30"
        },
        "max_participants": 15,
        "participants": []
    }
}

initial_teachers = [
    {
        "username": "mrodriguez",
        "display_name": "Ms. Rodriguez",
        "password": hash_password("art123"),
        "role": "teacher"
     },
    {
        "username": "mchen",
        "display_name": "Mr. Chen",
        "password": hash_password("chess456"),
        "role": "teacher"
    },
    {
        "username": "principal",
        "display_name": "Principal Martinez",
        "password": hash_password("admin789"),
        "role": "admin"
    }
]

