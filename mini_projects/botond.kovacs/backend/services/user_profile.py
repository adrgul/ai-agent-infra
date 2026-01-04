import os
import json
from pydantic import BaseModel

# Define the UserProfile model
class UserProfile(BaseModel):
    user_id: str
    language: str = "hu"
    default_city: str = "Budapest"

class UserProfileService:
    def __init__(self, base_dir="data/users"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def get_user_profile_path(self, user_id: str) -> str:
        return os.path.join(self.base_dir, f"{user_id}.json")

    def load_or_create_user_profile(self, user_id: str) -> UserProfile:
        path = self.get_user_profile_path(user_id)
        if os.path.exists(path):
            with open(path, "r") as file:
                data = json.load(file)
            return UserProfile(**data)
        else:
            profile = UserProfile(user_id=user_id)
            self.save_user_profile(profile)
            return profile

    def save_user_profile(self, profile: UserProfile):
        path = self.get_user_profile_path(profile.user_id)
        with open(path, "w") as file:
            json.dump(profile.dict(), file, indent=4)

    def update_user_profile(self, user_id: str, updates: dict) -> UserProfile:
        profile = self.load_or_create_user_profile(user_id)
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        self.save_user_profile(profile)
        return profile