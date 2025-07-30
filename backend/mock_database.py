"""
Mock Database for testing during development
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

class MockDatabase:
    def __init__(self):
        self.users = {}
        self.user_profiles = {}
        self.ideas = {}

    async def connect(self):
        """Mock connection"""
        print("Connected to mock database")

    async def disconnect(self):
        """Mock disconnection"""
        print("Disconnected from mock database")

    async def create_tables(self):
        """Mock table creation"""
        print("Mock tables created")

    # User Authentication Operations
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        self.users[user_data['id']] = user_data
        return user_data

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        for user in self.users.values():
            if user['email'] == email:
                return user
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.users.get(user_id)

    # User Profile Operations
    async def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user profile"""
        self.user_profiles[profile_data['id']] = profile_data
        return profile_data

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user ID"""
        for profile in self.user_profiles.values():
            if profile.get('user_id') == user_id:
                return profile
        return None

    async def get_profile_by_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by profile ID"""
        return self.user_profiles.get(profile_id)

    async def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Get all user profiles"""
        return list(self.user_profiles.values())

    # Ideas Operations
    async def create_idea(self, idea_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new idea"""
        self.ideas[idea_data['id']] = idea_data
        return idea_data

    async def get_idea(self, idea_id: str) -> Optional[Dict[str, Any]]:
        """Get idea by ID"""
        return self.ideas.get(idea_id)

    async def get_user_ideas(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all ideas for a user"""
        return [idea for idea in self.ideas.values() if idea['user_id'] == user_id]

    async def update_idea(self, idea_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an idea"""
        if idea_id in self.ideas:
            self.ideas[idea_id].update(update_data)
            self.ideas[idea_id]['updated_at'] = datetime.utcnow()
            return True
        return False

    async def delete_idea(self, idea_id: str) -> bool:
        """Delete an idea"""
        if idea_id in self.ideas:
            del self.ideas[idea_id]
            return True
        return False

    async def get_ideas_by_stage(self, stage: str) -> List[Dict[str, Any]]:
        """Get ideas by stage"""
        return [idea for idea in self.ideas.values() if idea['stage'] == stage]