# Junglore Chatbot Backend

This is a Python backend for the Junglore chatbot, providing wildlife and jungle information to users with context-aware conversations powered by GPT-4o-mini.

## Features
- User-specific chat sessions (multiple per user)
- Context-aware conversations (remembers previous messages)
- MongoDB for persistent storage
- Redis for fast session/context caching
- GPT-4o-mini integration for conversational flow
- RESTful API (testable via Postman)
- Expedition recommendations: when a user asks about planning a jungle safari expedition, the assistant replies affirmatively, lists the national parks where Junglore runs expeditions, and if the user selects a park (e.g., "Tadoba National Park"), the assistant recommends the corresponding expedition post on Junglore.com with a direct link.
- Expedition recommendations: if a user asks about planning a "jungle safari expedition", the assistant will reply confirming expeditions are available and list national parks we offer. When the user selects a park (for example, "Tadoba National Park"), the assistant will recommend the relevant expedition post on Junglore with a link.

## Setup
1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
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
- `GET /sessions/` — List all sessions for a user
- `GET /sessions/{session_id}/history` — Get chat history for a session

## Testing
- Use Postman to test all endpoints (see example requests in this README soon)

---

For questions, contact the backend team. 