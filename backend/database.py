"""
Database configuration and table creation for PostgreSQL
"""
import asyncpg
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import uuid

class Database:
    def __init__(self):
        self.pool = None
        self.postgres_url = os.environ.get('POSTGRES_URL')

    async def connect(self):
        """Create database connection pool"""
        self.pool = await asyncpg.create_pool(self.postgres_url)
        await self.create_tables()

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()

    async def create_tables(self):
        """Create necessary tables if they don't exist"""
        async with self.pool.acquire() as connection:
            # Create user_profiles table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    background TEXT,
                    experience JSONB,
                    interests JSONB,
                    skills JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')

            # Create ideas table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS ideas (
                    id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    description TEXT,
                    stage VARCHAR DEFAULT 'suggested',
                    ai_feedback TEXT,
                    tags JSONB,
                    priority VARCHAR DEFAULT 'medium',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    FOREIGN KEY (user_id) REFERENCES user_profiles(id)
                )
            ''')

    # User Profile Operations
    async def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user profile"""
        async with self.pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO user_profiles (id, name, background, experience, interests, skills, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', 
                profile_data['id'],
                profile_data['name'],
                profile_data['background'],
                json.dumps(profile_data['experience']),
                json.dumps(profile_data['interests']),
                json.dumps(profile_data['skills']),
                profile_data['created_at']
            )
            return profile_data

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                'SELECT * FROM user_profiles WHERE id = $1', user_id
            )
            if row:
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'background': row['background'],
                    'experience': json.loads(row['experience']) if row['experience'] else [],
                    'interests': json.loads(row['interests']) if row['interests'] else [],
                    'skills': json.loads(row['skills']) if row['skills'] else [],
                    'created_at': row['created_at']
                }
            return None

    async def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Get all user profiles"""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch('SELECT * FROM user_profiles ORDER BY created_at DESC')
            return [
                {
                    'id': row['id'],
                    'name': row['name'],
                    'background': row['background'],
                    'experience': json.loads(row['experience']) if row['experience'] else [],
                    'interests': json.loads(row['interests']) if row['interests'] else [],
                    'skills': json.loads(row['skills']) if row['skills'] else [],
                    'created_at': row['created_at']
                }
                for row in rows
            ]

    # Ideas Operations
    async def create_idea(self, idea_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new idea"""
        async with self.pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO ideas (id, user_id, title, description, stage, ai_feedback, tags, priority, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ''',
                idea_data['id'],
                idea_data['user_id'],
                idea_data['title'],
                idea_data['description'],
                idea_data['stage'],
                idea_data.get('ai_feedback'),
                json.dumps(idea_data['tags']),
                idea_data['priority'],
                idea_data['created_at'],
                idea_data['updated_at']
            )
            return idea_data

    async def get_idea(self, idea_id: str) -> Optional[Dict[str, Any]]:
        """Get idea by ID"""
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                'SELECT * FROM ideas WHERE id = $1', idea_id
            )
            if row:
                return {
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'title': row['title'],
                    'description': row['description'],
                    'stage': row['stage'],
                    'ai_feedback': row['ai_feedback'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'priority': row['priority'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None

    async def get_user_ideas(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all ideas for a user"""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(
                'SELECT * FROM ideas WHERE user_id = $1 ORDER BY updated_at DESC', user_id
            )
            return [
                {
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'title': row['title'],
                    'description': row['description'],
                    'stage': row['stage'],
                    'ai_feedback': row['ai_feedback'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'priority': row['priority'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                for row in rows
            ]

    async def update_idea(self, idea_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an idea"""
        async with self.pool.acquire() as connection:
            # Build dynamic update query
            set_clauses = []
            values = []
            param_count = 1

            for key, value in update_data.items():
                if key == 'tags' and value is not None:
                    set_clauses.append(f"{key} = ${param_count}")
                    values.append(json.dumps(value))
                else:
                    set_clauses.append(f"{key} = ${param_count}")
                    values.append(value)
                param_count += 1

            if not set_clauses:
                return False

            # Add updated_at
            set_clauses.append(f"updated_at = ${param_count}")
            values.append(datetime.utcnow())
            param_count += 1

            # Add idea_id for WHERE clause
            values.append(idea_id)

            query = f"UPDATE ideas SET {', '.join(set_clauses)} WHERE id = ${param_count}"
            result = await connection.execute(query, *values)
            return result != "UPDATE 0"

    async def delete_idea(self, idea_id: str) -> bool:
        """Delete an idea"""
        async with self.pool.acquire() as connection:
            result = await connection.execute(
                'DELETE FROM ideas WHERE id = $1', idea_id
            )
            return result != "DELETE 0"

    async def get_ideas_by_stage(self, stage: str) -> List[Dict[str, Any]]:
        """Get ideas by stage"""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(
                'SELECT * FROM ideas WHERE stage = $1 ORDER BY updated_at DESC', stage
            )
            return [
                {
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'title': row['title'],
                    'description': row['description'],
                    'stage': row['stage'],
                    'ai_feedback': row['ai_feedback'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'priority': row['priority'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                for row in rows
            ]