"""
Utility script to check what content is available in the PostgreSQL database.
Useful for debugging content matching issues.
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv()

# PostgreSQL setup
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def check_content_by_keywords(keywords: list):
    """Check if content exists for given keywords"""
    print(f"\n{'='*80}")
    print(f"🔍 SEARCHING FOR CONTENT WITH KEYWORDS: {keywords}")
    print(f"{'='*80}\n")
    
    async with AsyncSessionLocal() as session:
        for keyword in keywords:
            print(f"\n--- Searching for: '{keyword}' ---")
            query = text("""
                SELECT title, slug, excerpt, type, published_at
                FROM content
                WHERE status = 'PUBLISHED'
                AND (
                    LOWER(title) LIKE :keyword
                    OR LOWER(excerpt) LIKE :keyword
                    OR LOWER(content) LIKE :keyword
                )
                ORDER BY published_at DESC NULLS LAST
                LIMIT 10
            """)
            
            result = await session.execute(query, {"keyword": f"%{keyword.lower()}%"})
            rows = result.fetchall()
            
            if rows:
                print(f"✅ Found {len(rows)} articles:")
                for i, row in enumerate(rows, 1):
                    title = row[0]
                    slug = row[1]
                    excerpt = row[2][:100] if row[2] else "No excerpt"
                    article_type = row[3]
                    published = row[4]
                    
                    print(f"\n  {i}. {title}")
                    print(f"     Type: {article_type}")
                    print(f"     URL: https://explorejungles.com/blog/{slug}")
                    print(f"     Excerpt: {excerpt}...")
                    print(f"     Published: {published}")
            else:
                print(f"❌ No articles found for keyword: '{keyword}'")


async def list_all_content(limit: int = 20):
    """List all published content"""
    print(f"\n{'='*80}")
    print(f"📚 ALL PUBLISHED CONTENT (showing {limit} most recent)")
    print(f"{'='*80}\n")
    
    async with AsyncSessionLocal() as session:
        query = text("""
            SELECT title, slug, type, published_at
            FROM content
            WHERE status = 'PUBLISHED'
            ORDER BY published_at DESC NULLS LAST
            LIMIT :limit
        """)
        
        result = await session.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        if rows:
            print(f"✅ Found {len(rows)} published articles:\n")
            for i, row in enumerate(rows, 1):
                title = row[0]
                slug = row[1]
                article_type = row[2]
                published = row[3]
                
                print(f"{i}. [{article_type}] {title}")
                print(f"   URL: https://explorejungles.com/blog/{slug}")
                print(f"   Published: {published}\n")
        else:
            print("❌ No published content found in database!")


async def check_database_stats():
    """Check database statistics"""
    print(f"\n{'='*80}")
    print(f"📊 DATABASE STATISTICS")
    print(f"{'='*80}\n")
    
    async with AsyncSessionLocal() as session:
        # Total content
        query = text("SELECT COUNT(*) FROM content WHERE status = 'PUBLISHED'")
        result = await session.execute(query)
        total = result.scalar()
        print(f"Total published content: {total}")
        
        # By type
        query = text("""
            SELECT type, COUNT(*) 
            FROM content 
            WHERE status = 'PUBLISHED'
            GROUP BY type
            ORDER BY COUNT(*) DESC
        """)
        result = await session.execute(query)
        rows = result.fetchall()
        
        if rows:
            print(f"\nContent by type:")
            for row in rows:
                print(f"  - {row[0]}: {row[1]} articles")


async def main():
    """Main function"""
    print("\n" + "="*80)
    print("🌿 JUNGLORE CONTENT DATABASE CHECKER")
    print("="*80)
    
    # Check database stats
    await check_database_stats()
    
    # List recent content
    await list_all_content(limit=15)
    
    # Check specific keywords (example: Tadoba Maya Tigress)
    await check_content_by_keywords(["maya", "tigress", "tadoba"])
    
    # Check for man-eating tigers (Jim Corbett)
    await check_content_by_keywords(["man-eating", "corbett", "man eater"])
    
    print("\n" + "="*80)
    print("✅ CHECK COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
