import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import motor.motor_asyncio
import redis.asyncio as redis
import openai
import uuid
from bson import ObjectId
from openai import AsyncOpenAI
import json
import re
from config import (
    TRAVEL_KEYWORDS, WILDLIFE_KEYWORDS, LOCATION_KEYWORDS, DURATION_KEYWORDS,
    BUDGET_KEYWORDS, EXPEDITION_KEYWORDS, EXPEDITION_PARKS, AI_INFO_KEYWORDS, AI_INFO_URL, SCORING_CONFIG, BUDGET_THRESHOLDS, PACKAGE_TYPES,
    SYSTEM_PROMPT, REDIS_CONFIG, PACKAGE_SUGGESTION_CONFIG, SITE_BASE_URL
)

load_dotenv()

app = FastAPI()

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = mongo_client["jungloreprod"]

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

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Start a new chat session
@app.post("/sessions/", response_model=SessionInfo)
async def start_session(req: NewSessionRequest):
    # Validate user_id exists in users collection
    user = await db["users"].find_one({"_id": ObjectId(req.user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "user_id": req.user_id,
        "title": req.title or "New Chat",
        "created_at": str(uuid.uuid1()),
        "history": []
    }
    await db.sessions.insert_one(session)
    return SessionInfo(session_id=session_id, title=session["title"], created_at=session["created_at"])

# List all sessions for a user
@app.get("/sessions/", response_model=List[SessionInfo])
async def list_sessions(user_id: str):
    sessions = await db.sessions.find({"user_id": user_id}).to_list(100)
    return [SessionInfo(session_id=s["session_id"], title=s["title"], created_at=s["created_at"]) for s in sessions]

# Get chat history for a session
@app.get("/sessions/{session_id}/history", response_model=List[Message])
async def get_history(session_id: str, user_id: str):
    session = await db.sessions.find_one({"session_id": session_id, "user_id": user_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return [Message(**m) for m in session.get("history", [])]

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

async def find_relevant_package(user_message):
    """Find the most relevant package using AI-powered matching"""
    try:
        # Get all active packages
        packages = await db.packages.find({"status": True}).to_list(PACKAGE_SUGGESTION_CONFIG['max_packages_to_search'])
        
        if not packages:
            return None
        
        # Use AI-powered matching instead of keyword scoring
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

async def find_expedition_packages(location: Optional[str] = None, max_results: int = 10):
    """Return expedition packages optionally filtered by a location string."""
    query = {"status": True, "type": {"$regex": "expedition", "$options": "i"}}
    if location:
        query["$or"] = [
            {"region": {"$regex": location, "$options": "i"}},
            {"heading": {"$regex": location, "$options": "i"}},
            {"title": {"$regex": location, "$options": "i"}}
        ]
    packages = await db.packages.find(query).to_list(PACKAGE_SUGGESTION_CONFIG['max_packages_to_search'])
    return packages[:max_results]


def construct_post_url(package):
    """Construct a plausible expedition article URL for a package."""
    # Prefer region or title to build a slug
    slug_source = package.get('region') or package.get('title') or package.get('heading') or 'expedition'
    slug = _slugify(slug_source)
    return f"{SITE_BASE_URL}/expeditions/{slug}"

# New endpoint for detailed package information
@app.get("/packages/{package_id}/details")
async def get_package_details(package_id: str):
    """Get detailed package information with AI-generated description"""
    try:
        # Validate package_id format
        if not ObjectId.is_valid(package_id):
            raise HTTPException(status_code=400, detail="Invalid package ID")
        
        # Get package from database
        package = await db.packages.find_one({"_id": ObjectId(package_id), "status": True})
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Generate detailed AI description
        detailed_description = await generate_package_description(package, "detailed")
        
        # Prepare response with all package details
        response_data = {
            "title": package.get("title", ""),
            "image": package.get("image", ""),
            "additional_images": package.get("additional_images", []),
            "description": detailed_description,
            "duration": package.get("duration", ""),
            "region": package.get("region", ""),
            "price": package.get("price", ""),
            "currency": package.get("currency", ""),
            "type": package.get("type", ""),
            "features": package.get("features", {}),
            "date": package.get("date", []),
            "package_id": str(package.get("_id", ""))
        }
        
        return response_data
        
    except Exception as e:
        print(f"Error getting package details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def detect_travel_intent(user_message):
    """Detect travel intent, expedition intent, AI/predictive model queries, and any mentioned locations from the user message.

    Returns a dict: { 'travel_intent': bool, 'expedition_intent': bool, 'ai_intent': bool, 'locations': [str] }
    """
    try:
        message_lower = user_message.lower()
        travel = any(keyword in message_lower for keyword in TRAVEL_KEYWORDS)
        wildlife_interest = any(keyword in message_lower for keyword in WILDLIFE_KEYWORDS)
        expedition = any(keyword in message_lower for keyword in EXPEDITION_KEYWORDS) or ('expedition' in message_lower)
        ai_intent = any(keyword in message_lower for keyword in AI_INFO_KEYWORDS)
        # Detect any known location keywords mentioned
        locations = [kw for kw in LOCATION_KEYWORDS if kw in message_lower]
        return {
            'travel_intent': travel or wildlife_interest,
            'expedition_intent': expedition,
            'ai_intent': ai_intent,
            'locations': locations
        }
    except Exception as e:
        print(f"Error in intent detection: {e}")
        return {'travel_intent': False, 'expedition_intent': False, 'ai_intent': False, 'locations': []} 

@app.post("/sessions/{session_id}/message")
async def send_message(session_id: str, req: SendMessageRequest):
    redis_key = f"session_history:{session_id}"
    # Try to get history from Redis
    history_json = await redis_client.get(redis_key)
    if history_json:
        history = json.loads(history_json)
    else:
        # Fallback to MongoDB if not in Redis
        session = await db.sessions.find_one({"session_id": session_id, "user_id": req.user_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        history = session.get("history", [])[-10:]
        # Cache in Redis for future
        await redis_client.set(redis_key, json.dumps(history), ex=REDIS_CONFIG['session_history_expiry'])
    
    # Detect travel and expedition intents
    intent_info = detect_travel_intent(req.message)
    travel_intent = intent_info.get('travel_intent', False)
    expedition_intent = intent_info.get('expedition_intent', False)
    detected_locations = intent_info.get('locations', [])

    # Handle explicit expedition queries before calling the AI: list parks or recommend an expedition post
    if expedition_intent:
        # If user asked generally about expeditions (no specific location), list parks we offer expeditions in
        if not detected_locations:
            # Prefer the configured expedition park list when available
            parks = list(EXPEDITION_PARKS.keys())
            if parks:
                bot_reply = "Yes — we offer jungle safari expeditions in: " + ", ".join(parks) + ". Which one are you interested in?"
            else:
                exp_packages = await find_expedition_packages()
                parks = []
                for pkg in exp_packages:
                    name = (pkg.get('region') or pkg.get('heading') or pkg.get('title') or '').strip()
                    if name:
                        parks.append(name.title())
                parks = sorted(list(dict.fromkeys(parks)))  # unique, preserve order
                if parks:
                    bot_reply = "Yes — we offer jungle safari expeditions in: " + ", ".join(parks[:10]) + ". Which one are you interested in?"
                else:
                    bot_reply = "Yes — we offer jungle safari expeditions. Which region or national park are you interested in?"

            # Save user and bot messages
            new_history = (history + [
                {"sender": "user", "text": req.message},
                {"sender": "bot", "text": bot_reply}
            ])[-10:]
            # Update MongoDB
            await db.sessions.update_one({"session_id": session_id}, {"$set": {"history": new_history}})
            # Update Redis cache
            await redis_client.set(redis_key, json.dumps(new_history), ex=REDIS_CONFIG['session_history_expiry'])

            return {"reply": bot_reply}

        # If user mentioned a location, find expedition packages for that location and recommend the post
        else:
            location = detected_locations[0]
            # If the user also asked about AI/prediction for this park, include the predictive models page and an expedition link
            if intent_info.get('ai_intent'):
                packages = await find_expedition_packages(location)
                if packages:
                    pkg = packages[0]
                    post_url = construct_post_url(pkg)
                    bot_reply = (f"Yes — we use predictive models to estimate sighting chances. "
                                f"For {location.title()}, here's a recommended expedition: {pkg.get('title','')} — Read more: {post_url}. "
                                f"Learn about our predictive models here: {AI_INFO_URL}")

                    short_description = await generate_package_description(pkg, "short")
                    # Save user and bot messages
                    new_history = (history + [
                        {"sender": "user", "text": req.message},
                        {"sender": "bot", "text": bot_reply}
                    ])[-10:]
                    # Update MongoDB
                    await db.sessions.update_one({"session_id": session_id}, {"$set": {"history": new_history}})
                    # Update Redis cache
                    await redis_client.set(redis_key, json.dumps(new_history), ex=REDIS_CONFIG['session_history_expiry'])

                    response_data = {"reply": bot_reply,
                                     "package_suggestion": {
                                         "title": pkg.get('title', ''),
                                         "image": pkg.get('image', ''),
                                         "description": short_description,
                                         "package_id": str(pkg.get('_id', '')),
                                         "post_url": post_url,
                                         "model_info_url": AI_INFO_URL
                                     }}
                    return response_data
                else:
                    # If no packages in DB but the location matches a known expedition park, return the expedition post link along with model info
                    park_match = None
                    for canonical, slug in EXPEDITION_PARKS.items():
                        if canonical.lower() in location.lower() or slug.replace('-', ' ') in location.lower():
                            park_match = (canonical, slug)
                            break
                    if park_match:
                        canonical, slug = park_match
                        post_url = f"{SITE_BASE_URL}/expeditions/{slug}"
                        bot_reply = (f"Yes — we use predictive models to estimate sighting chances. "
                                    f"Here's our expedition post for {canonical}: {post_url}. "
                                    f"Learn more about our predictive models here: {AI_INFO_URL}")

                        # Save user and bot messages
                        new_history = (history + [
                            {"sender": "user", "text": req.message},
                            {"sender": "bot", "text": bot_reply}
                        ])[-10:]
                        await db.sessions.update_one({"session_id": session_id}, {"$set": {"history": new_history}})
                        await redis_client.set(redis_key, json.dumps(new_history), ex=REDIS_CONFIG['session_history_expiry'])
                        return {"reply": bot_reply, "model_info_url": AI_INFO_URL}
                    else:
                        bot_reply = (f"We use predictive models to estimate sighting chances, but I don't have an expedition post for {location.title()} right now. "
                                    f"Learn more about our predictive models here: {AI_INFO_URL}")

                        # Save user and bot messages
                        new_history = (history + [
                            {"sender": "user", "text": req.message},
                            {"sender": "bot", "text": bot_reply}
                        ])[-10:]
                        # Update MongoDB
                        await db.sessions.update_one({"session_id": session_id}, {"$set": {"history": new_history}})
                        # Update Redis cache
                        await redis_client.set(redis_key, json.dumps(new_history), ex=REDIS_CONFIG['session_HISTORY_EXPIRY'])

                        return {"reply": bot_reply, "model_info_url": AI_INFO_URL}
            # Regular expedition handling when not asking AI-specific question
            packages = await find_expedition_packages(location)
            if packages:
                pkg = packages[0]
                short_description = await generate_package_description(pkg, "short")
                post_url = construct_post_url(pkg)
                bot_reply = f"Yes — here's our recommended expedition for {location.title()}: {pkg.get('title','')} — {short_description} Read more: {post_url}"

                # Save user and bot messages
                new_history = (history + [
                    {"sender": "user", "text": req.message},
                    {"sender": "bot", "text": bot_reply}
                ])[-10:]
                # Update MongoDB
                await db.sessions.update_one({"session_id": session_id}, {"$set": {"history": new_history}})
                # Update Redis cache
                await redis_client.set(redis_key, json.dumps(new_history), ex=REDIS_CONFIG['session_history_expiry'])

                response_data = {"reply": bot_reply,
                                 "package_suggestion": {
                                     "title": pkg.get('title', ''),
                                     "image": pkg.get('image', ''),
                                     "description": short_description,
                                     "package_id": str(pkg.get('_id', '')),
                                     "post_url": post_url
                                 }}
                return response_data
            else:
                # If no packages in DB but location matches known park, return link; else apologize
                park_match = None
                for canonical, slug in EXPEDITION_PARKS.items():
                    if canonical.lower() in location.lower() or slug.replace('-', ' ') in location.lower():
                        park_match = (canonical, slug)
                        break
                if park_match:
                    canonical, slug = park_match
                    post_url = f"{SITE_BASE_URL}/expeditions/{slug}"
                    bot_reply = f"Yes — here's our expedition post for {canonical}: {post_url}"

                    # Save user and bot messages
                    new_history = (history + [
                        {"sender": "user", "text": req.message},
                        {"sender": "bot", "text": bot_reply}
                    ])[-10:]
                    await db.sessions.update_one({"session_id": session_id}, {"$set": {"history": new_history}})
                    await redis_client.set(redis_key, json.dumps(new_history), ex=REDIS_CONFIG['session_history_expiry'])
                    return {"reply": bot_reply}
                else:
                    bot_reply = f"Sorry, we don't currently have expeditions for {location.title()}. Would you like to see other parks?"

                    # Save user and bot messages
                    new_history = (history + [
                        {"sender": "user", "text": req.message},
                        {"sender": "bot", "text": bot_reply}
                    ])[-10:]
                    # Update MongoDB
                    await db.sessions.update_one({"session_id": session_id}, {"$set": {"history": new_history}})
                    # Update Redis cache
                    await redis_client.set(redis_key, json.dumps(new_history), ex=REDIS_CONFIG['session_history_expiry'])

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
        package_suggestion = await find_relevant_package(req.message)
    
    # Save user and bot messages
    new_history = (history + [
        {"sender": "user", "text": req.message},
        {"sender": "bot", "text": bot_reply}
    ])[-10:]
    # Update MongoDB
    await db.sessions.update_one({"session_id": session_id}, {"$set": {"history": new_history}})
    # Update Redis cache
    await redis_client.set(redis_key, json.dumps(new_history), ex=REDIS_CONFIG['session_history_expiry'])
    
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