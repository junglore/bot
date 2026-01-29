# Junglore Chatbot Backend

This is a Python backend for the Junglore chatbot, providing wildlife and jungle information to users with context-aware conversations powered by GPT-4o-mini.

## Features
- User-specific chat sessions (multiple per user)
- Context-aware conversations (remembers previous messages)
- MongoDB for persistent storage
- Redis for fast session/context caching
- GPT-4o-mini integration for conversational flow
- RESTful API (testable via Postman)
- **Smart Content Recommendation**: The bot intelligently checks the database FIRST for any relevant content (blogs, case studies, articles) before providing general information. If content exists on the website related to the user's query, it will be recommended with direct links.
- **Expedition recommendations**: When users ask about planning jungle safari expeditions, the assistant lists available national parks and recommends specific expedition posts on Junglore.com with direct links when a park is selected.
- **Database-first approach**: All content queries are matched against the PostgreSQL database (ExploreJungles.com) and MongoDB (Junglore.com) before the AI generates general responses, ensuring users get existing website content whenever available.

## Setup
1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: 
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your secrets (MongoDB URI, Redis URI, OpenAI API key, etc.)
4. **Run the server:**
   ```bash
    uvicorn main:app --reload
   ```

## API Endpoints
- `POST /sessions/` — Start a new chat session
- `POST /sessions/{session_id}/message` — Send a message to a session, get bot reply
  - Response may include:
    - `reply`: Text response from bot
    - `banner_image`: Featured image URL (for expeditions)
    - `expedition_package`: Expedition details with image, duration, description, URL
    - `featured_image`: Article image URL (for educational content)
    - `featured_article`: Article details with image, excerpt, URL
- `GET /sessions/` — List all sessions for a user
- `GET /sessions/{session_id}/history` — Get chat history for a session

## Testing
- Use Postman to test all endpoints (see example requests in this README soon)

---

For questions, contact the backend team. 