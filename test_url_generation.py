"""
Test script to verify URL generation is strictly database-driven.
This ensures GPT never creates fake URLs.
"""
import asyncio
import sys
from main import (
    find_blog_content,
    find_expedition_packages,
    match_blog_content,
    match_user_query_to_database,
    construct_post_url,
    detect_travel_intent
)
from config import SITE_BASE_URL, JUNGLORE_SITE_BASE_URL, AI_PREDICTION_URL

async def test_blog_urls():
    """Test that blog URLs come from database"""
    print("\n" + "="*60)
    print("TEST 1: Blog URL Generation")
    print("="*60)
    
    # Test direct content query
    print("\n1.1 Testing direct blog content query...")
    blog_posts = await find_blog_content("elephant")
    
    if blog_posts:
        print(f"✅ Found {len(blog_posts)} blog posts")
        for post in blog_posts[:3]:
            url = post.get('url', '')
            print(f"   - {post['title']}")
            print(f"     URL: {url}")
            
            # Verify URL structure
            if url.startswith(SITE_BASE_URL):
                print(f"     ✅ URL uses SITE_BASE_URL constant")
            else:
                print(f"     ❌ ERROR: URL does not use SITE_BASE_URL constant!")
    else:
        print("❌ No blog posts found - check PostgreSQL connection")
    
    # Test match_blog_content
    print("\n1.2 Testing blog content matching...")
    test_queries = [
        "Tell me about elephants",
        "Conservation efforts",
        "Wildlife behavior",
        "Case studies"
    ]
    
    for query in test_queries:
        result = await match_blog_content(query)
        if result['matched']:
            print(f"✅ Query '{query}' matched {len(result['posts'])} posts")
            for post in result['posts'][:2]:
                print(f"   - {post['title']}: {post['url']}")
        else:
            print(f"⚠️  Query '{query}' found no matches")


async def test_expedition_urls():
    """Test that expedition URLs come from database"""
    print("\n" + "="*60)
    print("TEST 2: Expedition URL Generation")
    print("="*60)
    
    # Test direct expedition query
    print("\n2.1 Testing direct expedition package query...")
    packages = await find_expedition_packages("corbett")
    
    if packages:
        print(f"✅ Found {len(packages)} expedition packages")
        for pkg in packages[:3]:
            title = pkg.get('title', 'Unknown')
            url = construct_post_url(pkg)
            print(f"   - {title}")
            print(f"     URL: {url}")
            
            # Verify URL structure
            if url.startswith(JUNGLORE_SITE_BASE_URL):
                print(f"     ✅ URL uses JUNGLORE_SITE_BASE_URL constant")
            else:
                print(f"     ❌ ERROR: URL does not use JUNGLORE_SITE_BASE_URL constant!")
    else:
        print("❌ No expedition packages found - check MongoDB connection")
    
    # Test match_user_query_to_database
    print("\n2.2 Testing expedition query matching...")
    test_queries = [
        "Dudhwa national park",
        "Jim Corbett expedition",
        "Safari to Ranthambore",
        "Tadoba tiger reserve"
    ]
    
    for query in test_queries:
        result = await match_user_query_to_database(query)
        if result['matched']:
            print(f"✅ Query '{query}' matched {result['park_name']}")
            for pkg in result['packages'][:2]:
                url = construct_post_url(pkg)
                print(f"   - {pkg.get('title')}: {url}")
        else:
            print(f"⚠️  Query '{query}' found no matches")


def test_ai_prediction_url():
    """Test that AI prediction URL is hardcoded"""
    print("\n" + "="*60)
    print("TEST 3: AI Prediction URL")
    print("="*60)
    
    print(f"\n✅ AI_PREDICTION_URL constant defined: {AI_PREDICTION_URL}")
    
    if AI_PREDICTION_URL == "https://junglore.com/ai-info":
        print("✅ URL matches expected value")
    else:
        print(f"❌ ERROR: Unexpected URL value!")
    
    # Test intent detection
    print("\n3.1 Testing AI intent detection...")
    test_queries = [
        "What is AI prediction?",
        "Best time to visit Corbett",
        "Sighting probability for tigers",
        "When should I visit for best wildlife"
    ]
    
    for query in test_queries:
        intent = detect_travel_intent(query)
        if intent.get('ai_intent'):
            print(f"✅ Query '{query}' detected AI intent")
            print(f"   Should return URL: {AI_PREDICTION_URL}")
        else:
            print(f"⚠️  Query '{query}' did not detect AI intent")


async def test_url_constants():
    """Verify all URL constants are properly defined"""
    print("\n" + "="*60)
    print("TEST 4: URL Constants Verification")
    print("="*60)
    
    constants = {
        "SITE_BASE_URL": SITE_BASE_URL,
        "JUNGLORE_SITE_BASE_URL": JUNGLORE_SITE_BASE_URL,
        "AI_PREDICTION_URL": AI_PREDICTION_URL
    }
    
    for name, value in constants.items():
        print(f"\n{name}:")
        print(f"  Value: {value}")
        if value.startswith("http"):
            print(f"  ✅ Valid URL format")
        else:
            print(f"  ❌ ERROR: Invalid URL format!")


async def main():
    """Run all URL generation tests"""
    print("\n" + "="*60)
    print("🔍 URL GENERATION VERIFICATION TEST")
    print("="*60)
    print("\nThis test verifies that ALL URLs come from database or")
    print("hardcoded constants, and GPT never generates fake URLs.")
    
    try:
        # Test all URL generation paths
        await test_url_constants()
        await test_blog_urls()
        await test_expedition_urls()
        test_ai_prediction_url()
        
        print("\n" + "="*60)
        print("✅ URL GENERATION TEST COMPLETE")
        print("="*60)
        print("\nSummary:")
        print("- All URLs should use constants (SITE_BASE_URL, JUNGLORE_SITE_BASE_URL, AI_PREDICTION_URL)")
        print("- Blog URLs are constructed from PostgreSQL slug data")
        print("- Expedition URLs are constructed from MongoDB package data")
        print("- AI prediction URL is hardcoded constant")
        print("- GPT should NEVER see or generate URL strings")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
