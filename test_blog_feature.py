"""
Test script for blog recommendation feature
Run this after starting the server with: uvicorn main:app --reload
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_blog_recommendation():
    """Test blog content recommendation feature"""
    
    async with httpx.AsyncClient() as client:
        # Step 1: Create a new session
        print("📝 Creating new chat session...")
        session_response = await client.post(
            f"{BASE_URL}/sessions/",
            json={"user_id": "test-user-123", "title": "Blog Test Session"}
        )
        session_data = session_response.json()
        session_id = session_data["session_id"]
        print(f"✅ Session created: {session_id}\n")
        
        # Step 2: Test blog intent queries
        test_queries = [
            "Tell me about tiger conservation",
            "Can I read articles about leopards?",
            "Learn more about wildlife behavior",
            "I want to know about man-eating big cats",
            "Information about jungle ecosystems"
        ]
        
        print("🧪 Testing blog recommendation queries:\n")
        
        for query in test_queries:
            print(f"👤 User: {query}")
            
            response = await client.post(
                f"{BASE_URL}/sessions/{session_id}/message",
                json={"user_id": "test-user-123", "message": query}
            )
            
            if response.status_code == 200:
                data = response.json()
                bot_reply = data["reply"]
                print(f"🤖 Bot: {bot_reply[:200]}...")  # Show first 200 chars
                print("-" * 80 + "\n")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   {response.text}\n")
        
        # Step 3: Test non-blog query (should go to normal flow)
        print("\n🧪 Testing normal query (non-blog intent):\n")
        normal_query = "What is a tiger?"
        print(f"👤 User: {normal_query}")
        
        response = await client.post(
            f"{BASE_URL}/sessions/{session_id}/message",
            json={"user_id": "test-user-123", "message": normal_query}
        )
        
        if response.status_code == 200:
            data = response.json()
            bot_reply = data["reply"]
            print(f"🤖 Bot: {bot_reply[:200]}...")
        else:
            print(f"❌ Error: {response.status_code}")
        
        print("\n✅ Test completed!")

if __name__ == "__main__":
    print("=" * 80)
    print("BLOG RECOMMENDATION FEATURE TEST")
    print("=" * 80 + "\n")
    print("⚠️  Make sure the server is running: uvicorn main:app --reload\n")
    
    asyncio.run(test_blog_recommendation())
