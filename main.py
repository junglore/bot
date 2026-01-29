import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import redis.asyncio as redis
import openai
import uuid
from openai import AsyncOpenAI
import json
import re
from models import Base, User, ChatbotSession as DBSession, Package
from config import (
    TRAVEL_KEYWORDS, WILDLIFE_KEYWORDS, LOCATION_KEYWORDS, DURATION_KEYWORDS,
    BUDGET_KEYWORDS, EXPEDITION_KEYWORDS, BLOG_KEYWORDS, EXPEDITION_PARKS, AI_INFO_KEYWORDS, AI_INFO_URL, AI_PREDICTION_URL, SCORING_CONFIG, BUDGET_THRESHOLDS, PACKAGE_TYPES,
    SYSTEM_PROMPT, REDIS_CONFIG, PACKAGE_SUGGESTION_CONFIG, SITE_BASE_URL, JUNGLORE_SITE_BASE_URL, GATE_PREDICTION_KEYWORDS, GATE_PREDICTION_URL
)

load_dotenv()

app = FastAPI()

# PostgreSQL setup (ExploreJungles.com - Blogs, Case Studies, Podcasts)
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Replace both postgres:// and postgresql:// with postgresql+asyncpg://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not DATABASE_URL.startswith("postgresql+asyncpg://"):
        # If it has any other postgresql driver, replace it
        DATABASE_URL = DATABASE_URL.replace("postgresql+", "postgresql+asyncpg://").replace("://", "", 1)
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# MongoDB setup (Junglore.com - Expeditions, Predictive Models)
MONGODB_URI = os.getenv("MONGODB_URI")
if MONGODB_URI:
    import motor.motor_asyncio
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    mongo_db = mongo_client["jungloreprod"]
else:
    mongo_client = None
    mongo_db = None

# Database dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Redis setup
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# OpenAI setup
openai_api_key = os.getenv("OPENAI_API_KEY")
import httpx
# Create a dedicated httpx AsyncClient and pass it to the OpenAI client to avoid version-specific constructor issues
httpx_client = httpx.AsyncClient()
client = AsyncOpenAI(api_key=openai_api_key, http_client=httpx_client)

# Models
class Message(BaseModel):
    sender: str  # 'user' or 'bot'
    text: str
    timestamp: Optional[str] = None

class NewSessionRequest(BaseModel):
    user_id: str
    title: Optional[str] = None

class SendMessageRequest(BaseModel):
    user_id: str
    message: str

class SessionInfo(BaseModel):
    session_id: str
    title: Optional[str]
    created_at: str

class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Database connection health check
@app.get("/health/db")
async def health_db():
    health_status = {
        "mongodb": "unknown",
        "postgresql": "unknown",
        "redis": "unknown"
    }
    
    # Check MongoDB
    try:
        if mongo_db is not None:
            await mongo_db.command("ping")
            # Try to count packages
            count = await mongo_db.packages.count_documents({})
            health_status["mongodb"] = f"connected ({count} packages)"
        else:
            health_status["mongodb"] = "connection is None"
    except Exception as e:
        health_status["mongodb"] = f"error: {str(e)}"
    
    # Check PostgreSQL
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT COUNT(*) FROM content"))
            count = result.scalar()
            health_status["postgresql"] = f"connected ({count} content items)"
    except Exception as e:
        health_status["postgresql"] = f"error: {str(e)}"
    
    # Check Redis
    try:
        await redis_client.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
    
    return health_status

# Create a new user
@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(
        id=str(uuid.uuid4()),
        email=user.email,
        name=user.name
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse(id=new_user.id, email=new_user.email, name=new_user.name)

# Start a new chat session
@app.post("/sessions/", response_model=SessionInfo)
async def start_session(req: NewSessionRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Note: User validation temporarily disabled for testing
        # Uncomment below to enforce user existence check
        # result = await db.execute(select(User).filter(User.id == req.user_id))
        # user = result.scalar_one_or_none()
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")
        
        session_id = str(uuid.uuid4())
        session = DBSession(
            session_id=session_id,
            user_id=req.user_id,
            title=req.title or "New Chat",
            history=[]
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return SessionInfo(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at.isoformat()
        )
    except Exception as e:
        print(f"ERROR creating session: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

# List all sessions for a user
@app.get("/sessions/", response_model=List[SessionInfo])
async def list_sessions(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DBSession).filter(DBSession.user_id == user_id).limit(100)
    )
    sessions = result.scalars().all()
    return [
        SessionInfo(
            session_id=s.session_id,
            title=s.title,
            created_at=s.created_at.isoformat()
        )
        for s in sessions
    ]

# Get chat history for a session
@app.get("/sessions/{session_id}/history", response_model=List[Message])
async def get_history(session_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DBSession).filter(
            DBSession.session_id == session_id,
            DBSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return [Message(**m) for m in session.history or []]

async def generate_package_description(package, description_type="short"):
    """Generate AI-powered description for packages"""
    try:
        package_info = f"""
        Title: {package.get('title', '')}
        Description: {package.get('description', '')}
        Location: {package.get('heading', '')} - {package.get('region', '')}
        Duration: {package.get('duration', '')}
        Type: {package.get('type', '')}
        Price: {package.get('price', '')} {package.get('currency', '')}
        Features: {package.get('features', {})}
        """
        
        if description_type == "short":
            prompt = f"""
            Create a compelling 1-2 line description for this safari package:
            {package_info}
            
            Make it exciting and enticing. Keep it under 100 characters. Focus on the main wildlife and experience.
            """
        else:  # detailed description
            prompt = f"""
            Create a detailed, engaging description for this safari package:
            {package_info}
            
            Write a comprehensive description that includes:
            - What wildlife they'll see
            - The experience highlights
            - Location details
            - What makes this package special
            - What's included
            
            Make it exciting and informative. Write 3-4 paragraphs.
            """
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a wildlife safari expert. Create compelling descriptions that make people excited about the safari experience."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200 if description_type == "short" else 500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generating package description: {e}")
        # Fallback to original description
        if description_type == "short":
            return package.get('description', '')[:100] + "..." if len(package.get('description', '')) > 100 else package.get('description', '')
        else:
            return package.get('description', '')

async def intelligent_package_matching(user_message, packages):
    """Use GPT-4o-mini to intelligently match user intent with packages"""
    try:
        if not packages:
            return None
            
        # Create a summary of available packages for the AI
        package_summaries = []
        for i, package in enumerate(packages, 1):
            summary = f"""
            {i}. Package: {package.get('title', '')}
            Description: {package.get('description', '')}
            Location: {package.get('heading', '')} - {package.get('region', '')}
            Duration: {package.get('duration', '')}
            Type: {package.get('type', '')}
            Wildlife Focus: {package.get('title', '')} {package.get('description', '')}
            """
            package_summaries.append(summary)
        
        # Create the matching prompt for GPT-4o-mini
        matching_prompt = f"""
        You are an expert wildlife safari consultant. A user has asked: "{user_message}"
        
        Based on their request, analyze these available safari packages and recommend the MOST RELEVANT ONE that best matches their specific requirements.
        
        Available packages:
        {chr(10).join(package_summaries)}
        
        Consider:
        1. Wildlife they want to see (tigers, elephants, lions, etc.)
        2. Specific locations they mentioned (Ranthambore, Corbett, etc.)
        3. Duration preferences (1 day, 3 days, etc.)
        4. Type of experience (expedition vs luxury resort)
        5. Budget considerations
        6. Any negative preferences they mentioned (e.g., "not in Corbett")
        
        Respond with ONLY the package number (1, 2, 3, etc.) that best matches their request. If no package is suitable, respond with "NONE".
        
        Be very precise - only recommend a package if it's a strong match for their specific requirements.
        """
        
        # Call GPT-4o-mini for intelligent matching
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a wildlife safari expert. Analyze user requests and match them with the most relevant safari package. Be precise and only recommend strong matches."},
                {"role": "user", "content": matching_prompt}
            ],
            max_tokens=50,
            temperature=0.1  # Low temperature for consistent matching
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse the AI response
        try:
            if ai_response.upper() == "NONE":
                return None
            elif ai_response.isdigit():
                package_index = int(ai_response) - 1
                if 0 <= package_index < len(packages):
                    return packages[package_index]
        except:
            pass
            
        return None
        
    except Exception as e:
        print(f"Error in intelligent package matching: {e}")
        return None

async def find_relevant_package(user_message, db_session: AsyncSession):
    """Find the most relevant expedition from Junglore.com MongoDB"""
    if mongo_db is None:
        return None
    
    try:
        # Get all active expedition packages from MongoDB
        cursor = mongo_db.packages.find({"status": True})
        packages = await cursor.to_list(length=PACKAGE_SUGGESTION_CONFIG['max_packages_to_search'])
        
        if not packages:
            return None
        
        # Use AI-powered matching
        best_match = await intelligent_package_matching(user_message, packages)
        
        return best_match
        
    except Exception as e:
        print(f"Error finding relevant package: {e}")
        return None

# Helpers for expedition-specific behaviour
import re

def _slugify(text: str) -> str:
    """Simple slugify for building article URLs."""
    text = text or ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip('-')
    return text

async def find_expedition_packages(location: Optional[str] = None, max_results: int = 100):
    """Return expedition packages from Junglore.com MongoDB (Expeditions)"""
    if mongo_db is None:
        print("❌ ERROR: MongoDB connection is None - cannot fetch packages")
        print("   Check your MONGODB_URI in .env file")
        return []
    
    try:
        print(f"\n🔍 QUERYING MONGODB for expeditions (location filter: {location})...")
        
        # Try lenient query first - just get expedition type packages
        query = {"type": {"$regex": "expedition", "$options": "i"}}
        
        # Add location filter if provided
        if location:
            query["$or"] = [
                {"region": {"$regex": location, "$options": "i"}},
                {"heading": {"$regex": location, "$options": "i"}},
                {"title": {"$regex": location, "$options": "i"}},
                {"slug": {"$regex": location, "$options": "i"}}
            ]
        
        packages = await mongo_db.packages.find(query).to_list(max_results)
        print(f"✅ Found {len(packages)} packages in MongoDB")
        
        if len(packages) == 0:
            print("⚠️  WARNING: Zero packages returned from MongoDB!")
            print(f"   Query used: {query}")
            print("   This suggests:")
            print("   1. No packages exist in 'packages' collection")
            print("   2. Wrong database connected (check MONGODB_URI)")
            print("   3. Field 'type' doesn't contain 'expedition' in any package")
        
        return packages
    except Exception as e:
        print(f"❌ ERROR fetching expeditions from MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return []


async def extract_park_names_from_packages(packages):
    """Extract unique park/location names from packages dynamically"""
    park_names = set()
    for pkg in packages:
        # Extract from multiple fields
        for field in ['region', 'heading', 'title', 'location']:
            value = pkg.get(field, '')
            if value and isinstance(value, str):
                # Clean up the name
                cleaned = value.replace('National Park', '').replace('Expedition', '').strip()
                if cleaned:
                    park_names.add(cleaned)
    return sorted(list(park_names))


def calculate_relevance_score(article_title: str, article_excerpt: str, search_keywords: list) -> int:
    """
    Calculate relevance score for an article based on keyword matches.
    Higher score = more relevant.
    """
    score = 0
    title_lower = article_title.lower()
    excerpt_lower = article_excerpt.lower()
    
    for keyword in search_keywords:
        keyword_lower = keyword.lower()
        # Title matches are worth more
        if keyword_lower in title_lower:
            score += 10
        # Excerpt matches are worth less
        if keyword_lower in excerpt_lower:
            score += 3
    
    return score


async def find_blog_content(topic: Optional[str] = None, max_results: int = 10, keywords: list = None):
    """
    Retrieve blog/educational content from PostgreSQL (ExploreJungles.com).
    Supports optional topic filtering and relevance scoring.
    Returns list of blog posts with details, sorted by relevance.
    """
    try:
        print(f"\n🔍 QUERYING POSTGRESQL for blog content (topic: {topic}, keywords: {keywords})...")
        
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            # Build query - get published content only
            if topic:
                # Use parameterized query to avoid SQL injection
                query = text("""
                    SELECT id, title, slug, excerpt, author_name, 
                           featured_image, type, view_count, published_at, created_at
                    FROM content
                    WHERE status = 'PUBLISHED'
                    AND (
                        LOWER(title) LIKE :topic
                        OR LOWER(excerpt) LIKE :topic
                        OR LOWER(content) LIKE :topic
                    )
                    ORDER BY published_at DESC NULLS LAST
                    LIMIT :limit
                """)
                result = await session.execute(query, {"topic": f"%{topic.lower()}%", "limit": max_results * 2})  # Get more for scoring
            else:
                # Get recent content if no topic specified
                query = text("""
                    SELECT id, title, slug, excerpt, author_name, 
                           featured_image, type, view_count, published_at, created_at
                    FROM content
                    WHERE status = 'PUBLISHED'
                    ORDER BY published_at DESC NULLS LAST
                    LIMIT :limit
                """)
                result = await session.execute(query, {"limit": max_results})
            
            rows = result.fetchall()
            print(f"✅ Retrieved {len(rows)} blog posts from database")
            
            if len(rows) == 0:
                print("⚠️  WARNING: Zero blog posts returned from PostgreSQL!")
                print(f"   Search topic: {topic}")
                print("   This suggests:")
                print("   1. No published content in 'content' table")
                print("   2. Search topic doesn't match any articles")
                print("   3. Database connection issue")
            
            # Format results with relevance scoring
            formatted_content = []
            for row in rows:
                article = {
                    "id": str(row[0]),
                    "title": row[1],
                    "slug": row[2],
                    "excerpt": row[3] or "",
                    "author": row[4] or "Junglore",
                    "image": row[5] or "",
                    "type": row[6],
                    "views": row[7] or 0,
                    "url": f"{SITE_BASE_URL}/blog/{row[2]}",  # explorejungles.com blog URL
                    "relevance_score": 0
                }
                
                # Calculate relevance if keywords provided
                if keywords:
                    article["relevance_score"] = calculate_relevance_score(
                        article["title"], 
                        article["excerpt"], 
                        keywords
                    )
                
                formatted_content.append(article)
            
            # If keywords provided, filter and sort by relevance
            if keywords:
                # Filter out low relevance (score < 3 means only weak matches)
                formatted_content = [a for a in formatted_content if a["relevance_score"] >= 3]
                # Sort by relevance score (highest first)
                formatted_content.sort(key=lambda x: x["relevance_score"], reverse=True)
                print(f"   Filtered to {len(formatted_content)} relevant posts (min score: 3)")
                if formatted_content:
                    print(f"   Top result: '{formatted_content[0]['title']}' (score: {formatted_content[0]['relevance_score']})")
            
            return formatted_content[:max_results]
            
    except Exception as e:
        print(f"Error querying PostgreSQL content: {e}")
        import traceback
        traceback.print_exc()
        return []


async def match_content_in_database(user_message: str) -> dict:
    """
    Analyze user message and match against ALL available content in database.
    Checks blog/educational content first before providing general information.
    Returns matched content from database.
    """
    try:
        # Extract topic keywords from user query
        user_lower = user_message.lower()
        
        # Define stop words
        stop_words = ['tell', 'me', 'about', 'the', 'a', 'an', 'in', 'blog', 'article', 'read', 'learn', 'want', 'to', 'know', 'case', 'study', 'what', 'why', 'how', 'is', 'are', 'was', 'were', 'can', 'could', 'would', 'should']
        
        # Extract meaningful keywords
        words = user_lower.split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        print(f"\n🔍 CONTENT MATCHING - Extracted keywords: {keywords}")
        
        # Try searching with most important keywords first
        blog_posts = []
        search_topic = None
        
        if keywords:
            # Try individual keywords starting with the most important ones
            for keyword in keywords[:3]:  # Try first 3 keywords
                search_topic = keyword
                print(f"   Searching database with keyword: '{search_topic}'")
                blog_posts = await find_blog_content(topic=search_topic, max_results=5, keywords=keywords)
                if blog_posts:
                    print(f"   ✅ Found {len(blog_posts)} posts with keyword: '{search_topic}'")
                    break
            
            # If no results with individual keywords, try combined search
            if not blog_posts and len(keywords) > 1:
                search_topic = ' '.join(keywords[:2])
                print(f"   Trying combined search: '{search_topic}'")
                blog_posts = await find_blog_content(topic=search_topic, max_results=5, keywords=keywords)
                
            # If still no results, try with all keywords combined
            if not blog_posts and len(keywords) > 2:
                search_topic = ' '.join(keywords)
                print(f"   Trying full search: '{search_topic}'")
                blog_posts = await find_blog_content(topic=search_topic, max_results=5, keywords=keywords)
        
        if blog_posts:
            print(f"   ✅ CONTENT MATCH SUCCESS: Found {len(blog_posts)} relevant posts")
        else:
            print(f"   ❌ No matching content found in database")
        
        return {
            "matched": len(blog_posts) > 0,
            "posts": blog_posts,
            "topic": search_topic
        }
        
    except Exception as e:
        print(f"Error in match_content_in_database: {e}")
        import traceback
        traceback.print_exc()
        return {
            "matched": False,
            "posts": [],
            "topic": None
        }


async def match_user_query_to_database(user_message: str) -> dict:
    """Match user query to available expeditions in database
    Returns: {'matched': bool, 'park_name': str or None, 'packages': list}
    """
    if mongo_db is None:
        print("ERROR: MongoDB connection is None")
        return {'matched': False, 'park_name': None, 'packages': []}
    
    try:
        # Get ALL available expedition packages from database
        print(f"\n🔍 MATCHING user query to database...")
        print(f"   User message: {user_message}")
        all_packages = await find_expedition_packages(location=None)
        print(f"   Retrieved {len(all_packages)} total packages from database")
        
        if not all_packages:
            print("⚠️  WARNING: No packages found in database")
            print("   Returning NO MATCH result")
            return {'matched': False, 'park_name': None, 'packages': [], 'available_parks': []}
        
        # Extract park names from packages for display
        available_parks = await extract_park_names_from_packages(all_packages)
        print(f"Available parks: {available_parks}")
        
        # Simple string matching - check if user message contains any park-related keywords
        user_lower = user_message.lower()
        matched_packages = []
        matched_park_name = None
        
        # Extract key terms from user query (remove common words)
        stop_words = ['national', 'park', 'expedition', 'safari', 'tell', 'me', 'about', 'the', 'a', 'an', 'in']
        user_words = [word for word in user_lower.split() if word not in stop_words and len(word) > 2]
        
        print(f"Extracted keywords from user query: {user_words}")
        
        # Search through all packages
        for pkg in all_packages:
            title = (pkg.get('title') or '').lower()
            heading = (pkg.get('heading') or '').lower()
            slug = (pkg.get('slug') or '').lower()
            region = (pkg.get('region') or '').lower()
            
            # Combine all searchable fields
            pkg_text = f"{title} {heading} {slug} {region}"
            
            # Check if ANY user keyword matches ANY package field
            for user_word in user_words:
                if user_word in pkg_text:
                    matched_packages.append(pkg)
                    if not matched_park_name:
                        matched_park_name = pkg.get('heading') or pkg.get('title')
                    print(f"  ✓ Matched '{user_word}' in package: {pkg.get('title')}")
                    break  # Don't add same package twice
        
        print(f"String matching found {len(matched_packages)} packages for query: '{user_message}'")
        
        if matched_packages:
            return {'matched': True, 'park_name': matched_park_name, 'packages': matched_packages}
        
        # No direct match - return all available parks for user to choose
        print("No direct match - returning all available parks")
        return {'matched': False, 'park_name': None, 'packages': all_packages, 'available_parks': available_parks}
            
    except Exception as e:
        print(f"ERROR in match_user_query_to_database: {e}")
        import traceback
        traceback.print_exc()
        return {'matched': False, 'park_name': None, 'packages': []}


def construct_post_url(package):
    """Construct expedition landing page URL for Junglore.com"""
    # Get title and clean it
    title = package.get('title', '').strip()
    
    # If title has " - ", take the part before it (e.g., "Jim Corbett National Park - 3 Nights 4 Days")
    if ' - ' in title:
        park_name = title.split(' - ')[0].strip()
    else:
        # Use title as-is (e.g., "Tadoba", "Ranthambore")
        park_name = title
    
    # Remove common words that aren't part of the park identifier
    park_name = park_name.replace('National Park', '').replace('national park', '').strip()
    
    # Create slug: "Jim Corbett" -> "jimcorbett", "Tadoba" -> "tadoba"
    slug = _slugify(park_name)
    
    # Always append -national-park
    slug = slug + '-national-park'
    
    return f"{JUNGLORE_SITE_BASE_URL}/explore/{slug}"

# New endpoint for detailed package information
@app.get("/packages/{package_id}/details")
async def get_package_details(package_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed package information with AI-generated description"""
    try:
        # Get package from database
        result = await db.execute(select(Package).filter(Package.id == package_id, Package.status == True))
        package = result.scalar_one_or_none()
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Convert to dict for processing
        package_dict = package.to_dict()
        
        # Generate detailed AI description
        detailed_description = await generate_package_description(package_dict, "detailed")
        
        # Prepare response with all package details
        response_data = {
            "title": package_dict.get("title", ""),
            "image": package_dict.get("image", ""),
            "additional_images": package_dict.get("additional_images", []),
            "description": detailed_description,
            "duration": package_dict.get("duration", ""),
            "region": package_dict.get("region", ""),
            "price": package_dict.get("price", ""),
            "currency": package_dict.get("currency", ""),
            "type": package_dict.get("type", ""),
            "features": package_dict.get("features", {}),
            "date": package_dict.get("date", []),
            "package_id": str(package_dict.get("_id", ""))
        }
        
        return response_data
        
    except Exception as e:
        print(f"Error getting package details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def detect_travel_intent(user_message):
    """Detect travel intent, expedition intent, blog intent, AI info queries, gate prediction queries, and any mentioned locations from the user message.

    Returns a dict: { 'travel_intent': bool, 'expedition_intent': bool, 'blog_intent': bool, 'ai_intent': bool, 'gate_prediction_intent': bool, 'locations': [str] }
    """
    try:
        message_lower = user_message.lower()
        travel = any(keyword in message_lower for keyword in TRAVEL_KEYWORDS)
        wildlife_interest = any(keyword in message_lower for keyword in WILDLIFE_KEYWORDS)
        expedition = any(keyword in message_lower for keyword in EXPEDITION_KEYWORDS) or ('expedition' in message_lower)
        blog_intent = any(keyword in message_lower for keyword in BLOG_KEYWORDS)
        ai_intent = any(keyword in message_lower for keyword in AI_INFO_KEYWORDS)
        gate_prediction_intent = any(keyword in message_lower for keyword in GATE_PREDICTION_KEYWORDS)
        # Detect any known location keywords mentioned (case-insensitive)
        locations = [kw for kw in LOCATION_KEYWORDS if kw.lower() in message_lower]
        return {
            'travel_intent': travel or wildlife_interest,
            'expedition_intent': expedition,
            'blog_intent': blog_intent,
            'ai_intent': ai_intent,
            'gate_prediction_intent': gate_prediction_intent,
            'locations': locations
        }
    except Exception as e:
        print(f"Error in intent detection: {e}")
        return {'travel_intent': False, 'expedition_intent': False, 'blog_intent': False, 'ai_intent': False, 'gate_prediction_intent': False, 'locations': []} 

async def update_session_history(session_id: str, new_history: list, db_session: AsyncSession):
    """Helper function to update session history in both PostgreSQL and Redis"""
    # Update PostgreSQL
    result = await db_session.execute(
        select(DBSession).filter(DBSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if session:
        session.history = new_history
        await db_session.commit()
    
    # Update Redis cache
    redis_key = f"session_history:{session_id}"
    await redis_client.set(redis_key, json.dumps(new_history), ex=REDIS_CONFIG['session_history_expiry'])
 

@app.post("/sessions/{session_id}/message")
async def send_message(session_id: str, req: SendMessageRequest, db: AsyncSession = Depends(get_db)):
    redis_key = f"session_history:{session_id}"
    # Try to get history from Redis
    history_json = await redis_client.get(redis_key)
    if history_json:
        history = json.loads(history_json)
    else:
        # Fallback to PostgreSQL if not in Redis
        result = await db.execute(
            select(DBSession).filter(
                DBSession.session_id == session_id,
                DBSession.user_id == req.user_id
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        history = (session.history or [])[-10:]
        # Cache in Redis for future
        await redis_client.set(redis_key, json.dumps(history), ex=REDIS_CONFIG['session_history_expiry'])
    
    # Detect travel and expedition intents
    intent_info = detect_travel_intent(req.message)
    travel_intent = intent_info.get('travel_intent', False)
    expedition_intent = intent_info.get('expedition_intent', False)
    blog_intent = intent_info.get('blog_intent', False)
    gate_prediction_intent = intent_info.get('gate_prediction_intent', False)
    detected_locations = intent_info.get('locations', [])

    # Handle AI Gate Prediction queries
    if gate_prediction_intent:
        print(f"Gate prediction intent detected in message: {req.message}")
        
        # Extract park name if mentioned in message
        park_mentioned = None
        for location in LOCATION_KEYWORDS:
            if location.lower() in req.message.lower():
                park_mentioned = location.title()
                break
        
        # Build response
        bot_reply = "🎯 **Junglore's AI-Powered Gate Prediction**\n\n"
        bot_reply += "Junglore uses an advanced AI predictive model to help you choose the best safari gate for optimal wildlife sightings! "
        bot_reply += "Our model analyzes historical data, seasonal patterns, and current conditions to recommend the ideal entry gate based on:\n\n"
        bot_reply += "✅ National park location\n"
        bot_reply += "✅ Your safari date\n"
        bot_reply += "✅ Seasonal wildlife movement patterns\n"
        bot_reply += "✅ Recent sighting trends\n\n"
        bot_reply += f"📊 **Get AI-powered gate recommendations:** {GATE_PREDICTION_URL}\n\n"
        
        # If park mentioned, try to add relevant expedition link
        if park_mentioned:
            bot_reply += f"Planning a safari to {park_mentioned}? Check out our expedition packages:\n"
            # Try to find packages for this park
            match_result = await match_user_query_to_database(park_mentioned)
            if match_result['matched'] and match_result['packages']:
                pkg = match_result['packages'][0]  # Get first package
                url = construct_post_url(pkg)
                bot_reply += f"🌿 {url}\n\n"
        else:
            bot_reply += "💡 *Tip: Visit the link above and select your destination park and travel dates to get personalized gate recommendations!*\n\n"
        
        bot_reply += "Trust Junglore's AI to maximize your chances of incredible wildlife encounters! 🐅🌿"
        
        # Save user and bot messages
        new_history = (history + [
            {"sender": "user", "text": req.message},
            {"sender": "bot", "text": bot_reply}
        ])[-10:]
        # Update database and cache
        await update_session_history(session_id, new_history, db)
        
        return {"reply": bot_reply}

    # Handle explicit expedition queries using dynamic AI-powered database matching
    if expedition_intent:
        # Use AI to match user query to database
        match_result = await match_user_query_to_database(req.message)
        
        if match_result['matched'] and match_result['packages']:
            # Specific park found with packages
            park_name = match_result['park_name']
            packages = match_result['packages']
            
            # Extract month/timing if mentioned in query
            message_lower = req.message.lower()
            months = ['january', 'february', 'march', 'april', 'may', 'june', 
                     'july', 'august', 'september', 'october', 'november', 'december',
                     'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            time_mentioned = None
            for month in months:
                if month in message_lower:
                    time_mentioned = month.title()
                    break
            
            # Build conversational response with package details
            if time_mentioned:
                bot_reply = f"Yes! We have expeditions planned for {time_mentioned} to {park_name}. 🌿\n\n"
            else:
                bot_reply = f"Yes! We have exciting expeditions to {park_name}. 🌿\n\n"
            
            # Add detailed package info for top match
            top_package = packages[0]
            title = top_package.get('title') or top_package.get('heading', '')
            duration = top_package.get('duration', '')
            description = top_package.get('description', '')
            url = construct_post_url(top_package)
            image = top_package.get('image', '')
            
            bot_reply += f"**{title}**\n"
            if duration:
                bot_reply += f"📅 Duration: {duration}\n"
            if description:
                # Truncate description to 150 chars
                short_desc = description[:150] + "..." if len(description) > 150 else description
                bot_reply += f"\n{short_desc}\n"
            
            bot_reply += f"\n🔗 **View detailed itinerary and book:** {url}\n"
            
            # Add more packages if available
            if len(packages) > 1:
                bot_reply += f"\n**Other {park_name} expeditions:**\n"
                for pkg in packages[1:3]:  # Show 2 more
                    pkg_title = pkg.get('title') or pkg.get('heading', '')
                    pkg_url = construct_post_url(pkg)
                    bot_reply += f"• {pkg_title}: {pkg_url}\n"
            
            bot_reply += "\n💡 *Each expedition includes expert guides, comfortable accommodations, and curated wildlife experiences!*"
            
            # Prepare response with image
            response_data = {"reply": bot_reply}
            if image:
                response_data["banner_image"] = image
            if packages:
                # Include package details for frontend
                response_data["expedition_package"] = {
                    "title": title,
                    "image": image,
                    "duration": duration,
                    "description": description[:200] if description else "",
                    "url": url,
                    "park": park_name
                }
            
        elif match_result['park_name'] and not match_result['packages']:
            # Park mentioned but no packages found
            park_name = match_result['park_name']
            bot_reply = f"We don't currently have expeditions for {park_name}. Would you like to explore other parks?"
            response_data = {"reply": bot_reply}
            
        elif 'available_parks' in match_result and match_result['available_parks']:
            # No specific park - list all available parks
            parks = match_result['available_parks'][:10]
            bot_reply = "Yes — we offer jungle safari expeditions in: " + ", ".join(parks) + ". Which one are you interested in?"
            response_data = {"reply": bot_reply}
            
        else:
            # No packages in database at all
            bot_reply = "We're currently setting up our expedition packages. Please check back soon!"
            response_data = {"reply": bot_reply}
        
        # Save user and bot messages
        new_history = (history + [
            {"sender": "user", "text": req.message},
            {"sender": "bot", "text": bot_reply}
        ])[-10:]
        # Update database and cache
        await update_session_history(session_id, new_history, db)
        
        return response_data
    
    # ALWAYS check database for relevant content FIRST (unless it's already handled above)
    print(f"\n📊 CHECKING DATABASE for relevant content...")
    content_result = await match_content_in_database(req.message)
    
    if content_result['matched'] and content_result['posts']:
        # Found relevant content in database - recommend it FIRST
        posts = content_result['posts']
        print(f"✅ Found {len(posts)} relevant posts - recommending database content")
        
        # Build recommendation with URLs
        bot_reply = "I found some great resources on this topic:\n\n"
        
        # Include featured article with image if available
        top_post = posts[0]
        if top_post.get('image'):
            bot_reply += f"**Featured:** {top_post['title']}\n"
            if top_post.get('excerpt'):
                bot_reply += f"{top_post['excerpt'][:150]}...\n\n"
            bot_reply += f"🔗 Read more: {top_post['url']}\n\n"
            
            # Add other articles
            if len(posts) > 1:
                bot_reply += "**More articles:**\n"
                for post in posts[1:5]:  # Show next 4
                    bot_reply += f"📖 {post['title']}: {post['url']}\n"
        else:
            # No images available, show list format
            for post in posts[:5]:  # Show top 5
                title = post['title']
                url = post['url']
                excerpt = post.get('excerpt', '')[:100]  # First 100 chars
                bot_reply += f"📖 **{title}**\n"
                if excerpt:
                    bot_reply += f"   {excerpt}...\n"
                bot_reply += f"   Read more: {url}\n\n"
        
        bot_reply += "Explore more educational content on ExploreJungles.com! 🌿"
        
        # Prepare response with image if available
        response_data = {"reply": bot_reply}
        if posts and posts[0].get('image'):
            response_data["featured_image"] = posts[0]['image']
            response_data["featured_article"] = {
                "title": posts[0]['title'],
                "excerpt": posts[0].get('excerpt', '')[:200],
                "url": posts[0]['url'],
                "image": posts[0]['image']
            }
        
        # Save user and bot messages
        new_history = (history + [
            {"sender": "user", "text": req.message},
            {"sender": "bot", "text": bot_reply}
        ])[-10:]
        # Update database and cache
        await update_session_history(session_id, new_history, db)
        
        return response_data
    else:
        print(f"❌ No content found in database - proceeding with AI response")
    
    # Handle AI prediction queries - hardcoded URL (never let GPT generate)
    if intent_info.get('ai_intent', False):
        print(f"AI prediction intent detected in message: {req.message}")
        
        bot_reply = (
            f"For information on sighting probabilities and AI-based predictions, visit: {AI_PREDICTION_URL}\n\n"
            f"This page provides detailed insights into wildlife sighting predictions powered by AI technology."
        )
        
        # Save user and bot messages
        new_history = (history + [
            {"sender": "user", "text": req.message},
            {"sender": "bot", "text": bot_reply}
        ])[-10:]
        # Update database and cache
        await update_session_history(session_id, new_history, db)
        
        return {"reply": bot_reply}

    # If not handled as expedition flow, proceed to call OpenAI as before
    # Add system prompt at the beginning
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Add conversation history
    messages.extend([{"role": "user" if m["sender"] == "user" else "assistant", "content": m["text"]} for m in history])
    messages.append({"role": "user", "content": req.message})
    
    # Call OpenAI GPT-4o-mini
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        bot_reply = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")
    
    # If travel intent detected, try to find relevant package
    package_suggestion = None
    if travel_intent:
        package_suggestion = await find_relevant_package(req.message, db)
    
    # Save user and bot messages
    new_history = (history + [
        {"sender": "user", "text": req.message},
        {"sender": "bot", "text": bot_reply}
    ])[-10:]
    # Update database and cache
    await update_session_history(session_id, new_history, db)
    
    # Return response with optional package suggestion
    response_data = {"reply": bot_reply}
    if package_suggestion:
        # Generate short AI description for the card
        short_description = await generate_package_description(package_suggestion, "short")
        
        response_data["package_suggestion"] = {
            "title": package_suggestion.get("title", ""),
            "image": package_suggestion.get("image", ""),
            "description": short_description,
            "package_id": str(package_suggestion.get("_id", ""))
        }
    
    return response_data 