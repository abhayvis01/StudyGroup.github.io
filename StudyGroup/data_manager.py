import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class DataManager:
    def __init__(self, file_path='users.json'):
        self.file_path = file_path
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({"users": {}}, f)
    
    def load_data(self):
        with open(self.file_path, 'r') as f:
            return json.load(f)
    
    def save_data(self, data):
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def add_user(self, username, password):
        data = self.load_data()
        
        # Check if username already exists
        if username in data["users"]:
            return False, "Username already exists"
        
        # Create new user
        user = {
            "username": username,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "id": str(len(data["users"]) + 1)
        }
        
        data["users"][username] = user
        self.save_data(data)
        return True, "User created successfully"
    
    def verify_user(self, username, password):
        data = self.load_data()
        user = data["users"].get(username)
        
        if user and check_password_hash(user["password_hash"], password):
            return True, user
        return False, None
    
    def get_user_by_id(self, user_id):
        data = self.load_data()
        for user in data["users"].values():
            if user["id"] == str(user_id):
                return user
        return None
    
    def get_all_users(self):
        data = self.load_data()
        return list(data["users"].values())
    
    def add_meeting(self, user_id, meeting_data):
        data = self.load_data()
        
        # Find user by ID
        for username, user in data["users"].items():
            if user["id"] == str(user_id):
                # Initialize meetings list if it doesn't exist
                if "meetings" not in user:
                    user["meetings"] = []
                
                # Add new meeting
                user["meetings"].append(meeting_data)
                self.save_data(data)
                return True
        
        return False
    
    def get_meeting(self, user_id, meeting_id):
        data = self.load_data()
        
        # Find user by ID
        for user in data["users"].values():
            if user["id"] == str(user_id):
                # Search for meeting
                for meeting in user.get("meetings", []):
                    if meeting["id"] == meeting_id:
                        return meeting
        
        return None
    
    def get_user_meetings(self, user_id):
        data = self.load_data()
        
        # Find user by ID
        for user in data["users"].values():
            if user["id"] == str(user_id):
                return user.get("meetings", [])
        
        return []