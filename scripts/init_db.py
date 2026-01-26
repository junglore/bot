"""
Database initialization script for PostgreSQL migration
This script creates the necessary tables in PostgreSQL
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from models import Base

load_dotenv()

async def init_db():
    """Initialize database tables"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Handle Heroku-style DATABASE_URL
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    
    print(f"Connecting to database...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(init_db())
