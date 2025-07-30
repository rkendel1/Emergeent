#!/usr/bin/env python3
"""
Simple script to test PostgreSQL connection and create tables
"""
import asyncio
import asyncpg
import sys

async def test_connection():
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            "postgresql://username:password@localhost:5432/test_database"
        )
        
        print("✅ Successfully connected to PostgreSQL!")
        
        # Create user_profiles table
        await conn.execute('''
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
        print("✅ Created user_profiles table")

        # Create ideas table
        await conn.execute('''
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
        print("✅ Created ideas table")
        
        # Test insert
        await conn.execute('''
            INSERT INTO user_profiles (id, name, background, experience, interests, skills)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO NOTHING
        ''', 
            'test-user-123',
            'Test User',
            'Testing database connection',
            '["Database testing"]',
            '["PostgreSQL"]',
            '["Python", "Docker"]'
        )
        print("✅ Inserted test user profile")
        
        # Test query
        result = await conn.fetchrow('SELECT name FROM user_profiles WHERE id = $1', 'test-user-123')
        if result:
            print(f"✅ Retrieved user: {result['name']}")
        
        await conn.close()
        print("✅ Database setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_connection())
        sys.exit(0 if success else 1)
    except ImportError as e:
        print(f"❌ Missing required packages: {e}")
        print("Note: This requires 'asyncpg' package to be installed")
        sys.exit(1)