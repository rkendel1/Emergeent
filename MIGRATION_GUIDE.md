# Emergeent Migration Guide

This repository has been migrated from MongoDB + Gemini API to PostgreSQL + GROQ API with full Docker support.

## Migration Changes

### Database Migration: MongoDB → PostgreSQL
- **Old**: MongoDB with AsyncIOMotorClient
- **New**: PostgreSQL with asyncpg for async operations
- **Schema**: Preserved all data models with proper PostgreSQL table structure
- **Files Changed**:
  - `backend/database.py` - New PostgreSQL database class
  - `backend/server.py` - Updated to use PostgreSQL operations
  - `backend/.env` - Updated database URL format

### AI Integration: Gemini API → GROQ API
- **Old**: `emergentintegrations.llm.chat` with Gemini API
- **New**: Custom GROQ client using httpx for HTTP requests
- **Files Changed**:
  - `backend/groq_client.py` - New GROQ API integration
  - `backend/server.py` - Updated AI functions to use GROQ
  - `backend/.env` - GROQ API key configuration

### Dockerization
- **New**: Complete Docker setup for development and production
- **Files Added**:
  - `backend/Dockerfile` - Backend containerization
  - `frontend/Dockerfile` - Frontend containerization  
  - `docker-compose.yml` - Multi-service orchestration

## Environment Setup

### 1. Environment Variables

Update your environment files:

**Backend (`backend/.env`)**:
```env
POSTGRES_URL="postgresql://username:password@localhost:5432/test_database"
GROQ_API_KEY="gsk_YOUR_GROQ_API_KEY_HERE"
```

**Frontend (`frontend/.env`)**:
```env
REACT_APP_BACKEND_URL=http://localhost:8000
WDS_SOCKET_PORT=443
```

### 2. Database Setup

Start PostgreSQL using Docker:
```bash
docker compose up postgres -d
```

The database will be available at `localhost:5432` with:
- Database: `test_database`
- Username: `username` 
- Password: `password`

Tables are automatically created when the backend starts.

### 3. Running the Application

#### Option A: Docker Compose (Recommended)
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

#### Option B: Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --reload

# Frontend  
cd frontend
yarn install
yarn start
```

## API Endpoints

All existing API endpoints are preserved:

### User Profiles
- `POST /api/profiles` - Create user profile
- `GET /api/profiles/{user_id}` - Get profile by ID
- `GET /api/profiles` - Get all profiles

### Ideas Management
- `POST /api/ideas` - Create idea
- `GET /api/ideas/user/{user_id}` - Get user's ideas
- `GET /api/ideas/{idea_id}` - Get idea by ID
- `PUT /api/ideas/{idea_id}` - Update idea
- `DELETE /api/ideas/{idea_id}` - Delete idea
- `GET /api/ideas/stages/{stage}` - Get ideas by stage

### AI Features
- `POST /api/ideas/generate` - Generate ideas with AI
- `POST /api/ideas/feedback` - Get AI feedback for idea

### Health Check
- `GET /api/health` - Service health status

## Database Schema

### user_profiles
```sql
CREATE TABLE user_profiles (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    background TEXT,
    experience JSONB,
    interests JSONB, 
    skills JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### ideas
```sql
CREATE TABLE ideas (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    stage VARCHAR DEFAULT 'suggested',
    ai_feedback TEXT,
    tags JSONB,
    priority VARCHAR DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Testing

The existing test suite (`backend_test.py`) works with the new implementation:

```bash
cd backend
python backend_test.py
```

## Migration Benefits

1. **Better Performance**: PostgreSQL offers better performance for relational data
2. **ACID Compliance**: Full transaction support and data integrity
3. **Scalability**: Better horizontal and vertical scaling options
4. **Modern AI**: GROQ provides faster inference and better model options
5. **Containerization**: Easy deployment and development environment setup
6. **Cost Efficiency**: Potentially lower costs compared to managed MongoDB + Gemini

## Development Notes

- All existing functionality is preserved
- API contracts remain unchanged
- Frontend requires no modifications
- Mock implementations available for development without external dependencies
- Full Docker setup for consistent development environments

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker compose ps

# View database logs
docker compose logs postgres

# Connect to database directly
PGPASSWORD=password psql -h localhost -p 5432 -U username -d test_database
```

### Backend Issues
```bash
# View backend logs
docker compose logs backend

# Run backend locally for debugging
cd backend
python server.py
```

### Frontend Issues
```bash
# View frontend logs  
docker compose logs frontend

# Run frontend locally
cd frontend
yarn start
```