import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_packages():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://'))
    
    # Check chatbot_packages table
    result = await conn.fetch("SELECT COUNT(*) as count FROM chatbot_packages")
    print(f"Chatbot packages: {result[0]['count']}")
    
    # Check if there's an existing packages table
    try:
        result = await conn.fetch("SELECT COUNT(*) as count FROM packages WHERE status = true")
        print(f"Main packages table: {result[0]['count']}")
        
        # Get a sample package
        sample = await conn.fetch("SELECT id, title, region, type FROM packages WHERE status = true LIMIT 3")
        print("\nSample packages:")
        for pkg in sample:
            print(f"  - {pkg['title']} ({pkg['region']}) - Type: {pkg['type']}")
    except:
        print("No 'packages' table found")
    
    await conn.close()

asyncio.run(check_packages())
