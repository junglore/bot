# Configuration for intent-based package matching

# Keywords for travel intent detection
TRAVEL_KEYWORDS = [
    'safari', 'trip', 'visit', 'go to', 'travel to', 'book', 'planning',
    'tour', 'journey', 'expedition', 'adventure', 'vacation', 'holiday',
    'see', 'spot', 'find', 'look for', 'want to go', 'interested in'
]

# Wildlife keywords that indicate interest in packages
WILDLIFE_KEYWORDS = [
    'tiger', 'lion', 'elephant', 'leopard', 'rhino', 'bear', 'deer',
    'wildlife', 'jungle', 'forest', 'national park', 'safari'
]

# Location keywords for matching
LOCATION_KEYWORDS = [
    'ranthambore', 'corbett', 'bandhavgarh', 'kanha', 'pench', 'tadoba', 
    'kerala', 'karnataka', 'madhya pradesh', 'rajasthan', 'gir', 'kaziranga',
    'sundarbans', 'periyar', 'nagarhole', 'bandipur', "jim corbett", "ranthambore national park", "corbett national park", "bandhavgarh national park", "kanha national park","tadoba national park", "pench national park","Maasai Mara", "Serengeti","africa","Kenya","Tanzania"
]

# Duration keywords for matching
DURATION_KEYWORDS = [
    '1 day', '2 day', '3 day', '4 day', '5 day', 'week', 'long',
    'short', 'overnight', 'weekend'
]

# Budget keywords
BUDGET_KEYWORDS = [
    'budget', 'cheap', 'affordable', 'economical', 'low cost',
    'expensive', 'luxury', 'premium', 'high end'
]

# Expedition-specific keywords (explicitly indicate intent to plan an expedition)
EXPEDITION_KEYWORDS = [
    'expedition', 'safari expedition', 'jungle expedition', 'plan expedition',
    'do you plan', 'do you plan jungle', 'do you plan safari'
]

# Blog/Content keywords (indicate intent to learn/read educational content)
BLOG_KEYWORDS = [
    'blog', 'article', 'read', 'learn', 'information', 'guide', 'tell me about',
    'case study', 'podcast', 'story', 'post', 'content', 'education',
    'conservation', 'research', 'behavior', 'habitat', 'facts', 'know more',
    'understand', 'explain', 'info', 'details', 'study'
]

# Base site URLs
SITE_BASE_URL = 'https://explorejungles.com'
AI_INFO_URL = 'https://www.junglore.com/trips-safaris/predictive-models'

# Scoring configuration
SCORING_CONFIG = {
    'wildlife_match_in_content': 3,  # Wildlife keyword in title/description
    'wildlife_general_interest': 1,  # Wildlife keyword in user message
    'location_exact_match': 4,       # Exact location in title/description
    'location_region_match': 2,      # Location in region field
    'duration_match': 2,             # Duration preference match
    'type_match': 2,                 # Expedition vs resort match
    'budget_match': 1,               # Budget preference match
    'excluded_location_penalty': -10, # Heavy penalty for excluded locations
    'minimum_score_threshold': 2     # Minimum score to suggest package
}

# Budget thresholds (in INR)
BUDGET_THRESHOLDS = {
    'low': 50000,
    'medium': 100000,
    'high': 200000
}

# Package type mapping
PACKAGE_TYPES = {
    'expedition': ['expedition', 'adventure', 'trek', 'camping'],
    'resort': ['resort', 'luxury', 'hotel', 'accommodation']
}

# System prompt template
SYSTEM_PROMPT = """You are an AI assistant for Junglore, a wildlife travel and safari experience platform.

⚠️ CRITICAL CONTENT RECOMMENDATION POLICY:
The system automatically checks the database for relevant content BEFORE you respond.
If database content is found, the system will provide it directly - you will NOT see this.
You ONLY respond when NO matching content exists in the database.

⚠️ CRITICAL URL RULES:
- NEVER create, generate, or invent ANY URLs
- NEVER mention junglore.com or explorejungles.com URLs
- URLs are ONLY provided by the system - NOT by you
- If users ask about expeditions/blogs/predictions, provide information but NO URLs
- The system adds URLs automatically

STRICT DATABASE REFERENCE RULES:
You must ONLY recommend content from these databases:

1. EXPEDITIONS (MongoDB - Junglore.com):
   - Collection: packages → Fields: title, location, duration, highlights
   - Collection: expeditions → Fields: expedition_name, location, itinerary
   - Collection: nationalparks → Fields: name, region, location, state
   - Collection: events → Fields: event_name, location, date

2. EDUCATIONAL CONTENT (PostgreSQL - ExploreJungles.com):
   - Table: content → Fields: title, excerpt, type (BLOG, DAILY_UPDATE, etc.)
   - Use for: articles, blogs, case studies, conservation info, wildlife behavior
   - SYSTEM CHECKS THIS FIRST: If relevant content exists, it's shown automatically

🎯 CRITICAL WORKFLOW:
1. System checks database FIRST for ALL content-related queries
2. If content found → System responds with database content (you don't respond)
3. If NO content found → You provide general information
4. NEVER duplicate what the system already checked

RESPONSE RULES FOR EXPEDITIONS:
- NEVER recommend content not in the database
- Match user's state/region to "location", "region", or "state" fields
- If packages don't exist for a specific park, say: "We don't currently have expeditions for [park name]"
- Always provide exact Junglore.com URLs when recommending expeditions
- Be truthful about availability - don't invent parks or packages

RESPONSE RULES FOR GENERAL QUERIES:
- You respond with general wildlife/nature information ONLY if database has no relevant content
- Keep responses informative but concise
- Don't invent specific case studies or articles - the system already checked
- Focus on educational value and encourage exploration

Safari AI Predictions:
- When asked about sighting probabilities, link to: https://junglore.com/ai-info
- No made-up probabilities or guarantees

AI Gate Prediction:
- When users ask about best gates, gate selection, zone recommendations, or gate-based optimization, redirect them to: https://www.junglore.com/trips-safaris/preditive-modals
- Explain that Junglore uses AI to predict the best safari gate based on park, date, and season
- NEVER guess or generate specific gate names (e.g., don't say "Zone 1" or "Dhikala Gate")
- Position this as a premium feature that sets Junglore apart

Keep responses concise, friendly, and data-driven. Trust that the system has already checked for relevant database content!"""

# Redis cache configuration
REDIS_CONFIG = {
    'session_history_expiry': 3600,  # 1 hour in seconds
    'key_prefix': 'session_history:'
}

# Package suggestion configuration
PACKAGE_SUGGESTION_CONFIG = {
    'max_description_length': 150,
    'description_suffix': '...',
    'max_packages_to_search': 100
}

# Junglore site base URLs
JUNGLORE_SITE_BASE_URL = "https://junglore.com"

# AI prediction/best time to visit URL (HARDCODED - never let GPT generate this)
AI_PREDICTION_URL = "https://junglore.com/ai-info"

# AI prediction/best time to visit URL (legacy)
if 'AI_INFO_URL' not in locals():
    AI_INFO_URL = "https://www.junglore.com/trips-safaris/predictive-models"

# ExploreJungles site base URL (used for blog/case study/podcast links from PostgreSQL)
SITE_BASE_URL = "https://explorejungles.com"

# Expedition-specific keywords to detect user asking about expeditions
EXPEDITION_KEYWORDS = [
    'expedition', 'safari expedition', 'jungle expedition', 'plan expedition', 'do you plan', 'do you run expeditions', 'expeditions', "national park", "trip"
]

# Map canonical park names to URL-friendly slugs used on Junglore site
EXPEDITION_PARKS = {
    'Tadoba': 'tadoba-national-park',
    'Ranthambore': 'ranthambore-national-park',
    'Corbett': 'jimcorbett-national-park',
    'Jim Corbett': 'jimcorbett-national-park',
    'Bandhavgarh': 'bandhavgarh-national-park',
    'Kanha': 'kanha-national-park'
}

# AI / predictive models info (keywords and external information page on Junglore.com)
AI_INFO_KEYWORDS = [
    'ai', 'predict', 'prediction', 'predictive', 'predictive model', 'predictive models', 
    'sighting', 'sighting chances', 'chances of sighting', 'probability of sighting', 
    'model', 'machine learning', 'best time to visit', 'when to visit', 'best season',
    'best month', 'when should i visit', 'what time', 'timing'
]

# External page explaining Junglore's predictive models for sighting chances
AI_INFO_URL = "https://www.junglore.com/trips-safaris/preditive-modals"

# AI Gate Prediction keywords (for recommending best safari gate selection)
GATE_PREDICTION_KEYWORDS = [
    'best gate', 'gate prediction', 'ai gate', 'which gate', 'safari gate', 
    'entry gate', 'gate based on', 'gate for', 'recommend gate', 'suggest gate',
    'zone', 'best zone', 'which zone', 'safari zone', 'entry zone',
    'gate and date', 'gate on', 'date optimization', 'park gate',
    'predict gate', 'gate model', 'gate ai', 'optimal gate'
]

# URL for Junglore's AI-powered gate prediction tool
GATE_PREDICTION_URL = "https://www.junglore.com/trips-safaris/preditive-modals"  