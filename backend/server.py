from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from database import Database
from groq_client import GroqClient
from passlib.context import CryptContext
from jose import JWTError, jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database connection
db = Database()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# AI Configuration
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
groq_client = GroqClient(GROQ_API_KEY) if GROQ_API_KEY else None

# Authentication Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer
security = HTTPBearer()

# Authentication Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
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
    count: int = 5

class AIFeedbackRequest(BaseModel):
    idea_id: str
    stage: str

# Authentication Helper Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await db.get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return User(**user)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# AI Helper Functions
async def generate_ideas_with_ai(user_profile: UserProfile, count: int = 5) -> List[str]:
    """Generate ideas using GROQ based on user profile"""
    try:
        if not groq_client:
            raise ValueError("GROQ API key not configured")

        system_message = f"""You are an expert idea generator and innovation consultant. Generate innovative, actionable business/project ideas based on the user's profile.

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

        user_message = f"Generate {count} innovative ideas based on my profile. Focus on practical, implementable concepts that can evolve from initial spark to full product."

        response = await groq_client.send_message(system_message, user_message)
        
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
                if 'title' in current_idea:
                    current_idea['description'] = line[12:].strip()
            elif line and 'title' in current_idea and 'description' in current_idea and not line.startswith('TITLE:') and not line.startswith('**IDEA'):
                # Continue description but avoid bleeding into next idea
                current_idea['description'] += ' ' + line
        
        if current_idea and 'title' in current_idea and 'description' in current_idea:
            ideas.append(current_idea)
        
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
        if not groq_client:
            raise ValueError("GROQ API key not configured")

        stage_prompts = {
            "suggested": "Provide initial feedback on this idea's potential. Focus on market opportunity, feasibility, and initial next steps.",
            "deep_dive": "Analyze this idea deeply. Discuss target market, competitive landscape, technical requirements, and business model options.",
            "iterating": "Suggest specific improvements and iterations for this idea. Focus on refinement, feature prioritization, and addressing potential weaknesses.",
            "considering": "Evaluate this idea for implementation. Discuss resource requirements, timeline, risks, and go-to-market strategy.",
            "building": "Provide guidance for building this idea. Focus on MVP development, key metrics, user validation, and scaling strategies."
        }

        system_message = f"""You are an experienced startup advisor and product development expert. Provide thoughtful, actionable feedback for ideas in different stages of development.

Current Stage: {stage}
Focus: {stage_prompts.get(stage, 'General feedback')}

Provide specific, actionable advice that helps move the idea forward."""

        user_message = f"""Idea: {idea.title}
Description: {idea.description}
Current Stage: {stage}
Tags: {', '.join(idea.tags)}

Please provide detailed feedback appropriate for the {stage} stage."""

        response = await groq_client.send_message(system_message, user_message)
        return response
        
    except Exception as e:
        print(f"AI feedback error: {e}")
        return f"Unable to generate AI feedback at this time. Consider: What are the next steps for moving this idea forward in the {stage} stage?"

# API Routes

# Authentication Routes
@api_router.post("/auth/signup", response_model=Token)
async def signup(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(email=user_data.email)
    user_dict = user.dict()
    user_dict['password_hash'] = hashed_password
    
    await db.create_user(user_dict)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.get_user_by_email(user_data.email)
    if not user or not verify_password(user_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# User Profile Routes
@api_router.post("/profiles", response_model=UserProfile)
async def create_profile(profile_data: UserProfileCreate, current_user: User = Depends(get_current_active_user)):
    profile = UserProfile(user_id=current_user.id, **profile_data.dict())
    await db.create_profile(profile.dict())
    return profile

@api_router.get("/profiles/me", response_model=UserProfile)
async def get_my_profile(current_user: User = Depends(get_current_active_user)):
    profile = await db.get_profile(current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile(**profile)

@api_router.get("/profiles/{profile_id}", response_model=UserProfile)
async def get_profile_by_id(profile_id: str, current_user: User = Depends(get_current_active_user)):
    profile = await db.get_profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile(**profile)

# Ideas Routes
@api_router.post("/ideas", response_model=Idea)
async def create_idea(idea_data: IdeaCreate, current_user: User = Depends(get_current_active_user)):
    # Override user_id with current authenticated user
    idea = Idea(user_id=current_user.id, **{k: v for k, v in idea_data.dict().items() if k != 'user_id'})
    await db.create_idea(idea.dict())
    return idea

@api_router.get("/ideas", response_model=List[Idea])
async def get_my_ideas(current_user: User = Depends(get_current_active_user)):
    ideas = await db.get_user_ideas(current_user.id)
    return [Idea(**idea) for idea in ideas]

@api_router.get("/ideas/{idea_id}", response_model=Idea)
async def get_idea(idea_id: str, current_user: User = Depends(get_current_active_user)):
    idea = await db.get_idea(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    # Ensure user can only access their own ideas
    if idea['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return Idea(**idea)

@api_router.put("/ideas/{idea_id}", response_model=Idea)
async def update_idea(idea_id: str, update_data: IdeaUpdate, current_user: User = Depends(get_current_active_user)):
    # Check if idea exists and belongs to user
    idea = await db.get_idea(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    if idea['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    success = await db.update_idea(idea_id, update_dict)
    
    if not success:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    updated_idea = await db.get_idea(idea_id)
    return Idea(**updated_idea)

@api_router.delete("/ideas/{idea_id}")
async def delete_idea(idea_id: str, current_user: User = Depends(get_current_active_user)):
    # Check if idea exists and belongs to user
    idea = await db.get_idea(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    if idea['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = await db.delete_idea(idea_id)
    if not success:
        raise HTTPException(status_code=404, detail="Idea not found")
    return {"message": "Idea deleted successfully"}

# AI-powered Routes
@api_router.post("/ideas/generate")
async def generate_ideas(request: AIIdeaRequest, current_user: User = Depends(get_current_active_user)):
    # Override user_id with current authenticated user
    profile = await db.get_profile(current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please create a profile first.")
    
    user_profile = UserProfile(**profile)
    
    # Generate ideas using AI
    generated_ideas = await generate_ideas_with_ai(user_profile, request.count)
    
    # Save generated ideas to database
    created_ideas = []
    for idea_data in generated_ideas:
        idea = Idea(
            user_id=current_user.id,
            title=idea_data.get('title', 'Generated Idea'),
            description=idea_data.get('description', 'AI-generated idea description'),
            stage="suggested",
            tags=["ai-generated"]
        )
        await db.create_idea(idea.dict())
        created_ideas.append(idea)
    
    return {"generated_ideas": created_ideas, "count": len(created_ideas)}

@api_router.post("/ideas/feedback")
async def get_idea_feedback(request: AIFeedbackRequest, current_user: User = Depends(get_current_active_user)):
    # Get the idea and verify ownership
    idea = await db.get_idea(request.idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    if idea['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    idea_obj = Idea(**idea)
    
    # Generate AI feedback
    feedback = await get_ai_feedback(idea_obj, request.stage)
    
    # Update idea with feedback
    await db.update_idea(request.idea_id, {"ai_feedback": feedback})
    
    return {"feedback": feedback}

@api_router.get("/ideas/stages/{stage}")
async def get_ideas_by_stage(stage: str, current_user: User = Depends(get_current_active_user)):
    # Get all user's ideas first, then filter by stage
    ideas = await db.get_user_ideas(current_user.id)
    filtered_ideas = [idea for idea in ideas if idea['stage'] == stage]
    return [Idea(**idea) for idea in filtered_ideas]

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

@app.on_event("startup")
async def startup_db():
    await db.connect()

@app.on_event("shutdown")
async def shutdown_db():
    await db.disconnect()