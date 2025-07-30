"""
Mock GROQ client for testing during development
"""

class MockGroqClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "llama3-8b-8192"

    async def send_message(self, system_message: str, user_message: str) -> str:
        """Mock GROQ response"""
        if "Generate" in user_message and "ideas" in user_message:
            return """TITLE: EcoTrack - Smart Carbon Footprint Monitor
DESCRIPTION: A mobile app that automatically tracks daily activities and calculates real-time carbon emissions with gamified reduction challenges and community leaderboards.

TITLE: HealthMind - AI Mental Wellness Companion  
DESCRIPTION: An AI-powered mental health platform offering personalized mindfulness exercises, mood tracking, and crisis intervention for young professionals.

TITLE: LocalLink - Neighborhood Skills Exchange
DESCRIPTION: A hyperlocal platform connecting neighbors to share skills, tools, and services, reducing consumption while building community resilience."""
        
        elif "feedback" in system_message.lower():
            return """This is a compelling idea with strong market potential. The carbon tracking space is growing rapidly as consumers become more environmentally conscious. 

Key strengths:
- Clear value proposition for eco-conscious users
- Gamification can drive engagement
- Mobile-first approach fits target demographic

Next steps:
1. Research existing competitors like Capture and MyClimate
2. Define MVP features (basic activity tracking + carbon calculation)
3. Identify data sources for accurate emissions calculations
4. Plan user acquisition strategy through environmental communities"""
        
        return "Mock AI response for testing purposes."

    def set_model(self, model_name: str):
        """Set the model to use"""
        self.model = model_name
        return self