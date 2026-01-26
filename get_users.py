import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def get_user_ids():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://'))
    
    # Get first 5 users
    result = await conn.fetch("SELECT id, email FROM users LIMIT 5")
    
    print("Available users:")
    for row in result:
        print(f"  ID: {row['id']}")
        print(f"  Email: {row['email']}")
        print()
    
    await conn.close()

asyncio.run(get_user_ids())
