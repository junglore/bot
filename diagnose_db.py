import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

async def diagnose_databases():
    print("=" * 80)
    print("DATABASE DIAGNOSTIC TEST")
    print("=" * 80)
    
    # Test 1: MongoDB
    print("\n1. TESTING MONGODB CONNECTION...")
    try:
        MONGODB_URI = os.getenv("MONGODB_URI")
        mongo_client = AsyncIOMotorClient(MONGODB_URI)
        db = mongo_client["jungloreprod"]
        
        total_count = await db.packages.count_documents({})
        print(f"   ✓ Connected to MongoDB")
        print(f"   ✓ Total packages: {total_count}")
        
        # Test expedition query
        query = {"status": True, "type": {"$regex": "expedition", "$options": "i"}}
        cursor = db.packages.find(query).limit(5)
        expeditions = await cursor.to_list(5)
        print(f"   ✓ Expeditions found: {len(expeditions)}")
        
        if expeditions:
            for pkg in expeditions[:3]:
                print(f"     - {pkg.get('title', 'N/A')}")
        else:
            print("   ⚠️  NO EXPEDITIONS FOUND!")
            
        await mongo_client.close()
        
    except Exception as e:
        print(f"   ❌ MongoDB Error: {e}")
    
    # Test 2: PostgreSQL
    print("\n2. TESTING POSTGRESQL CONNECTION...")
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Test content query
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM content WHERE status = 'PUBLISHED'
            """))
            count = result.scalar()
            print(f"   ✓ Connected to PostgreSQL")
            print(f"   ✓ Published content: {count}")
            
            # Test search for "elephant"
            result = await conn.execute(text("""
                SELECT title FROM content 
                WHERE status = 'PUBLISHED'
                AND LOWER(title) LIKE '%elephant%'
                LIMIT 3
            """))
            posts = result.fetchall()
            print(f"   ✓ Posts matching 'elephant': {len(posts)}")
            for post in posts:
                print(f"     - {post[0]}")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"   ❌ PostgreSQL Error: {e}")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(diagnose_databases())
