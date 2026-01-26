import asyncio
import os
import sys
sys.path.insert(0, 'D:/Faunabot')
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from models import Base

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

# Convert Railway URL to asyncpg format
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def create_tables():
    print('Creating chatbot tables...')
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        # Only create tables if they don't exist (doesn't drop existing ones)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('✓ Chatbot tables ready!')

asyncio.run(create_tables())
