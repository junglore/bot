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

# Base site URL for recommending Junglore posts
SITE_BASE_URL = 'https://junglore.com'

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
SYSTEM_PROMPT = """Safari Sighting Prediction Recommendation

You are an AI assistant for Junglore, a wildlife travel and safari experience platform.

Primary Objective:
Whenever a user asks about how AI is used in safaris, the chances or probability of wildlife sightings, or the likelihood of seeing animals during a safari, you MUST:
- Acknowledge the user’s question clearly.
- Explain briefly (1–2 sentences) how Junglore uses AI-driven predictive models.
- Recommend Junglore’s AI-powered Safari Sighting Prediction Models.
- Redirect the user to the official Junglore predictive models page (see link below).

Intent Detection Criteria (trigger behavior for queries like):
- “How do you use AI in safaris?”
- “What are the chances of spotting a tiger with you?”
- “Can you predict wildlife sightings?”
- “How likely am I to see animals on a safari?”
- “Do you have any model that predicts sightings?”

Response Guidelines (mandatory):
- Tone: Informative, confident, friendly.
- State that Junglore uses AI-driven predictive models based on historical sighting data, seasonal patterns, park-specific trends, time/zone and movement analytics.
- Do NOT guarantee sightings (no promises) and do NOT provide random or made-up probabilities.
- Keep responses concise, value-driven, and encourage users to explore the model.

Mandatory Recommendation & Redirection (always include):
👉 Explore our AI-powered Safari Sighting Prediction Models here:
https://www.junglore.com/trips-safaris/preditive-modals

Sample response template (use as guidance):
"We use AI to enhance safari planning by analyzing historical sightings, seasonal trends, and park-specific movement patterns. While sightings can never be guaranteed, our predictive model estimates probability of sightings and helps guide better-informed safari choices. To learn more and explore the model, visit: https://www.junglore.com/trips-safaris/preditive-modals"

Important Rules:
- NEVER claim guaranteed sightings.
- NEVER provide random probabilities.
- ALWAYS recommend the Junglore predictive model and include the official link above.
- Keep responses concise (one to three short paragraphs) and focused on data-driven value.
"""

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

# Junglore site base URL (used to build expedition post links)
SITE_BASE_URL = "https://junglore.com"

# Expedition-specific keywords to detect user asking about expeditions
EXPEDITION_KEYWORDS = [
    'expedition', 'safari expedition', 'jungle expedition', 'plan expedition', 'do you plan', 'do you run expeditions', 'expeditions', "national park", "trip"p

# Map canonical park names to URL-friendly slugs used on Junglore site
EXPEDITION_PARKS = {
    'Tadoba': 'tadoba-national-park',
    'Ranthambore': 'ranthambore-national-park',
    'Corbett': 'corbett-national-park',
    'Bandhavgarh': 'bandhavgarh-national-park',
    'Kanha': 'kanha-national-park'
}

# AI / predictive models info (keywords and external information page)
AI_INFO_KEYWORDS = [
    'ai', 'predict', 'prediction', 'predictive', 'predictive model', 'predictive models', 'sighting', 'sighting chances', 'chances of sighting', 'probability of sighting', 'model', 'machine learning',
]

# External page explaining Junglore's predictive models for sighting chances
AI_INFO_URL = "https://www.junglore.com/trips-safaris/preditive-modals"  