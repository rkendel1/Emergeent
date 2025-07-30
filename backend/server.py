from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# AI Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    background: str
    experience: List[str]
    interests: List[str]
    skills: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileCreate(BaseModel):
    name: str
    background: str
    experience: List[str]
    interests: List[str]
    skills: List[str]

class Idea(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    stage: str  # suggested, deep_dive, iterating, considering, building
    ai_feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = []
    priority: str = "medium"  # low, medium, high

class IdeaCreate(BaseModel):
    user_id: str
    title: str
    description: str
    stage: str = "suggested"
    tags: List[str] = []
    priority: str = "medium"

class IdeaUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    stage: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None

class AIIdeaRequest(BaseModel):
    user_id: str
    count: int = 5

class AIFeedbackRequest(BaseModel):
    idea_id: str
    stage: str

# AI Helper Functions
async def generate_ideas_with_ai(user_profile: UserProfile, count: int = 5) -> List[str]:
    """Generate ideas using Gemini based on user profile"""
    try:
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=f"idea_generation_{user_profile.id}_{datetime.now().isoformat()}",
            system_message=f"""You are an expert idea generator and innovation consultant. Generate innovative, actionable business/project ideas based on the user's profile.

User Profile:
- Background: {user_profile.background}
- Experience: {', '.join(user_profile.experience)}
- Interests: {', '.join(user_profile.interests)}
- Skills: {', '.join(user_profile.skills)}

Generate {count} innovative ideas that:
1. Leverage the user's existing skills and experience
2. Align with their interests
3. Have potential for development from spark to MVP to funded product
4. Are specific and actionable
5. Range from simple solutions to ambitious ventures

Format each idea as:
TITLE: [Concise, compelling title]
DESCRIPTION: [2-3 sentences describing the core concept, target audience, and value proposition]

Generate exactly {count} ideas."""
        ).with_model("gemini", "gemini-2.0-flash")

        user_message = UserMessage(
            text=f"Generate {count} innovative ideas based on my profile. Focus on practical, implementable concepts that can evolve from initial spark to full product."
        )

        response = await chat.send_message(user_message)
        
        # Debug: Print the raw response
        print(f"DEBUG - Raw AI response: {response}")
        
        # Parse the response to extract individual ideas
        ideas = []
        lines = response.split('\n')
        current_idea = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('TITLE:'):
                if current_idea:
                    ideas.append(current_idea)
                current_idea = {'title': line[6:].strip(), 'description': ''}
            elif line.startswith('DESCRIPTION:'):
                current_idea['description'] = line[12:].strip()
            elif line and 'title' in current_idea and not line.startswith('TITLE:'):
                current_idea['description'] += ' ' + line
        
        if current_idea:
            ideas.append(current_idea)
        
        print(f"DEBUG - Parsed ideas: {ideas}")
        return ideas[:count]
        
    except Exception as e:
        print(f"AI idea generation error: {e}")
        # Fallback ideas based on user profile
        return [
            {
                "title": f"Solution for {user_profile.interests[0] if user_profile.interests else 'productivity'}",
                "description": f"Innovative approach leveraging {user_profile.skills[0] if user_profile.skills else 'technology'} to solve common challenges."
            }
        ]

async def get_ai_feedback(idea: Idea, stage: str) -> str:
    """Get AI feedback for idea based on current stage"""
    try:
        stage_prompts = {
            "suggested": "Provide initial feedback on this idea's potential. Focus on market opportunity, feasibility, and initial next steps.",
            "deep_dive": "Analyze this idea deeply. Discuss target market, competitive landscape, technical requirements, and business model options.",
            "iterating": "Suggest specific improvements and iterations for this idea. Focus on refinement, feature prioritization, and addressing potential weaknesses.",
            "considering": "Evaluate this idea for implementation. Discuss resource requirements, timeline, risks, and go-to-market strategy.",
            "building": "Provide guidance for building this idea. Focus on MVP development, key metrics, user validation, and scaling strategies."
        }

        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=f"feedback_{idea.id}_{stage}_{datetime.now().isoformat()}",
            system_message=f"""You are an experienced startup advisor and product development expert. Provide thoughtful, actionable feedback for ideas in different stages of development.

Current Stage: {stage}
Focus: {stage_prompts.get(stage, 'General feedback')}

Provide specific, actionable advice that helps move the idea forward."""
        ).with_model("gemini", "gemini-2.0-flash")

        user_message = UserMessage(
            text=f"""Idea: {idea.title}
Description: {idea.description}
Current Stage: {stage}
Tags: {', '.join(idea.tags)}

Please provide detailed feedback appropriate for the {stage} stage."""
        )

        response = await chat.send_message(user_message)
        return response
        
    except Exception as e:
        print(f"AI feedback error: {e}")
        return f"Unable to generate AI feedback at this time. Consider: What are the next steps for moving this idea forward in the {stage} stage?"

# API Routes

# User Profile Routes
@api_router.post("/profiles", response_model=UserProfile)
async def create_profile(profile_data: UserProfileCreate):
    profile = UserProfile(**profile_data.dict())
    await db.user_profiles.insert_one(profile.dict())
    return profile

@api_router.get("/profiles/{user_id}", response_model=UserProfile)
async def get_profile(user_id: str):
    profile = await db.user_profiles.find_one({"id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile(**profile)

@api_router.get("/profiles", response_model=List[UserProfile])
async def get_all_profiles():
    profiles = await db.user_profiles.find().to_list(1000)
    return [UserProfile(**profile) for profile in profiles]

# Ideas Routes
@api_router.post("/ideas", response_model=Idea)
async def create_idea(idea_data: IdeaCreate):
    idea = Idea(**idea_data.dict())
    await db.ideas.insert_one(idea.dict())
    return idea

@api_router.get("/ideas/user/{user_id}", response_model=List[Idea])
async def get_user_ideas(user_id: str):
    ideas = await db.ideas.find({"user_id": user_id}).to_list(1000)
    return [Idea(**idea) for idea in ideas]

@api_router.get("/ideas/{idea_id}", response_model=Idea)
async def get_idea(idea_id: str):
    idea = await db.ideas.find_one({"id": idea_id})
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return Idea(**idea)

@api_router.put("/ideas/{idea_id}", response_model=Idea)
async def update_idea(idea_id: str, update_data: IdeaUpdate):
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await db.ideas.update_one(
        {"id": idea_id}, 
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    updated_idea = await db.ideas.find_one({"id": idea_id})
    return Idea(**updated_idea)

@api_router.delete("/ideas/{idea_id}")
async def delete_idea(idea_id: str):
    result = await db.ideas.delete_one({"id": idea_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Idea not found")
    return {"message": "Idea deleted successfully"}

# AI-powered Routes
@api_router.post("/ideas/generate")
async def generate_ideas(request: AIIdeaRequest):
    # Get user profile
    profile = await db.user_profiles.find_one({"id": request.user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    user_profile = UserProfile(**profile)
    
    # Generate ideas using AI
    generated_ideas = await generate_ideas_with_ai(user_profile, request.count)
    
    # Save generated ideas to database
    created_ideas = []
    for idea_data in generated_ideas:
        idea = Idea(
            user_id=request.user_id,
            title=idea_data.get('title', 'Generated Idea'),
            description=idea_data.get('description', 'AI-generated idea description'),
            stage="suggested",
            tags=["ai-generated"]
        )
        await db.ideas.insert_one(idea.dict())
        created_ideas.append(idea)
    
    return {"generated_ideas": created_ideas, "count": len(created_ideas)}

@api_router.post("/ideas/feedback")
async def get_idea_feedback(request: AIFeedbackRequest):
    # Get the idea
    idea = await db.ideas.find_one({"id": request.idea_id})
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    idea_obj = Idea(**idea)
    
    # Generate AI feedback
    feedback = await get_ai_feedback(idea_obj, request.stage)
    
    # Update idea with feedback
    await db.ideas.update_one(
        {"id": request.idea_id},
        {"$set": {"ai_feedback": feedback, "updated_at": datetime.utcnow()}}
    )
    
    return {"feedback": feedback}

@api_router.get("/ideas/stages/{stage}")
async def get_ideas_by_stage(stage: str):
    ideas = await db.ideas.find({"stage": stage}).to_list(1000)
    return [Idea(**idea) for idea in ideas]

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()