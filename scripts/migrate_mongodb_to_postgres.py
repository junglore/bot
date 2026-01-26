"""
Migration script to transfer data from MongoDB to PostgreSQL
Run this script to migrate existing data from junglore.com MongoDB to explorejungles.com PostgreSQL
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import motor.motor_asyncio
from models import User, Session as DBSession, Package
from datetime import datetime

load_dotenv()

async def migrate_data():
    """Migrate data from MongoDB to PostgreSQL"""
    
    # MongoDB setup
    MONGODB_URI = os.getenv("MONGODB_URI")
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    mongo_db = mongo_client["jungloreprod"]
    
    # PostgreSQL setup
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        print("Starting data migration...")
        
        # Migrate Users
        print("\n=== Migrating Users ===")
        users = await mongo_db.users.find({}).to_list(None)
        user_count = 0
        for mongo_user in users:
            try:
                user = User(
                    id=str(mongo_user.get("_id")),
                    email=mongo_user.get("email", ""),
                    name=mongo_user.get("name", ""),
                    created_at=mongo_user.get("created_at", datetime.utcnow()),
                    updated_at=mongo_user.get("updated_at", datetime.utcnow())
                )
                session.add(user)
                user_count += 1
                if user_count % 100 == 0:
                    await session.commit()
                    print(f"Migrated {user_count} users...")
            except Exception as e:
                print(f"Error migrating user {mongo_user.get('_id')}: {e}")
                continue
        
        await session.commit()
        print(f"✓ Migrated {user_count} users")
        
        # Migrate Sessions
        print("\n=== Migrating Sessions ===")
        sessions = await mongo_db.sessions.find({}).to_list(None)
        session_count = 0
        for mongo_session in sessions:
            try:
                db_session = DBSession(
                    session_id=mongo_session.get("session_id"),
                    user_id=mongo_session.get("user_id"),
                    title=mongo_session.get("title", "New Chat"),
                    created_at=mongo_session.get("created_at", datetime.utcnow()),
                    history=mongo_session.get("history", [])
                )
                session.add(db_session)
                session_count += 1
                if session_count % 100 == 0:
                    await session.commit()
                    print(f"Migrated {session_count} sessions...")
            except Exception as e:
                print(f"Error migrating session {mongo_session.get('session_id')}: {e}")
                continue
        
        await session.commit()
        print(f"✓ Migrated {session_count} sessions")
        
        # Migrate Packages
        print("\n=== Migrating Packages ===")
        packages = await mongo_db.packages.find({}).to_list(None)
        package_count = 0
        for mongo_package in packages:
            try:
                package = Package(
                    id=str(mongo_package.get("_id")),
                    title=mongo_package.get("title", ""),
                    description=mongo_package.get("description", ""),
                    heading=mongo_package.get("heading", ""),
                    region=mongo_package.get("region", ""),
                    duration=mongo_package.get("duration", ""),
                    type=mongo_package.get("type", ""),
                    price=mongo_package.get("price", 0.0),
                    currency=mongo_package.get("currency", "INR"),
                    image=mongo_package.get("image", ""),
                    additional_images=mongo_package.get("additional_images", []),
                    features=mongo_package.get("features", {}),
                    date=mongo_package.get("date", []),
                    status=mongo_package.get("status", True),
                    created_at=mongo_package.get("created_at", datetime.utcnow()),
                    updated_at=mongo_package.get("updated_at", datetime.utcnow())
                )
                session.add(package)
                package_count += 1
                if package_count % 50 == 0:
                    await session.commit()
                    print(f"Migrated {package_count} packages...")
            except Exception as e:
                print(f"Error migrating package {mongo_package.get('_id')}: {e}")
                continue
        
        await session.commit()
        print(f"✓ Migrated {package_count} packages")
        
        print("\n=== Migration Summary ===")
        print(f"Total Users: {user_count}")
        print(f"Total Sessions: {session_count}")
        print(f"Total Packages: {package_count}")
        print("\nMigration completed successfully!")
    
    await engine.dispose()
    mongo_client.close()

if __name__ == "__main__":
    asyncio.run(migrate_data())
