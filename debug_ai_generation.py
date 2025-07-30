#!/usr/bin/env python3
"""
Debug AI Idea Generation
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BASE_URL}/api"

async def debug_ai_generation():
    async with aiohttp.ClientSession() as session:
        # First create a test profile
        profile_data = {
            "name": "Debug User",
            "background": "Software engineer with AI experience",
            "experience": ["Python", "AI/ML", "Web development"],
            "interests": ["Technology", "Innovation", "Startups"],
            "skills": ["Python", "FastAPI", "React"]
        }
        
        print("Creating test profile...")
        async with session.post(f"{API_BASE}/profiles", json=profile_data) as response:
            if response.status == 200:
                profile = await response.json()
                user_id = profile['id']
                print(f"✅ Profile created with ID: {user_id}")
            else:
                print(f"❌ Failed to create profile: {response.status}")
                return
        
        # Test AI idea generation with detailed response
        ai_request = {
            "user_id": user_id,
            "count": 2
        }
        
        print("\nTesting AI idea generation...")
        async with session.post(f"{API_BASE}/ideas/generate", json=ai_request) as response:
            print(f"Response status: {response.status}")
            response_data = await response.json()
            print(f"Response data: {json.dumps(response_data, indent=2, default=str)}")
            
            if 'generated_ideas' in response_data:
                ideas = response_data['generated_ideas']
                print(f"Number of ideas generated: {len(ideas)}")
                for i, idea in enumerate(ideas):
                    print(f"Idea {i+1}: {idea.get('title', 'No title')} - {idea.get('description', 'No description')[:100]}...")
            else:
                print("No 'generated_ideas' key in response")

if __name__ == "__main__":
    asyncio.run(debug_ai_generation())