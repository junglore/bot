# Content Recommendation Feature - Database-First Approach

## Overview
The chatbot now implements a **database-first approach** for all user queries. Before providing general AI-generated responses, the system **automatically checks the database** for relevant content that already exists on the website and recommends it with direct links.

## How It Works

### 1. **Intelligent Content Matching** When a user asks ANY question (not just explicit "blog" or "article" requests), the system:
- Extracts meaningful keywords from the query
- Searches the PostgreSQL database (ExploreJungles.com content)
- Uses progressive keyword matching (individual → combined → full query)
- Returns relevant articles, blogs, case studies, etc.

### 2. **Priority System**
The message handling follows this priority:
1. ✅ **Gate Prediction queries** → Direct link to AI tool
2. ✅ **Expedition queries** → MongoDB search for packages
3. ✅ **AI/Prediction queries** → Direct link to info page
4. ✅ **ALL OTHER queries** → **Check database for content FIRST**
5. ⬇️ Only if no database content found → AI generates general response

### 3. **Example Use Cases**

#### Case Study Example (Your Use Case):
```
User: "Tell me about man-eating tigers"
System: 
- Searches database for "man-eating" and "tigers"
- Finds: "BIG CATS TURNED DEADLY" case study
- Returns: Article with title, excerpt, and direct URL to explorejungles.com
```

#### Wildlife Behavior Example:
```
User: "Why do elephants migrate?"
System:
- Searches database for "elephants" and "migrate"
- If article exists → Returns article with URL
- If no article → AI provides general information
```

#### Conservation Example:
```
User: "What is Project Tiger?"
System:
- Searches database for "project" and "tiger"
- If blog post exists → Returns post with URL
- If no content → AI provides general information
```

## Technical Implementation

### Updated Functions:

#### `calculate_relevance_score(article_title, article_excerpt, search_keywords)`
- **Location**: [main.py](main.py)
- **Purpose**: Ranks articles by relevance to user query
- **Scoring**:
  - Title match: **+10 points** per keyword
  - Excerpt match: **+3 points** per keyword
  - Minimum score threshold: **3 points**
- **Example**: Query "maya tigress tadoba"
  - Article with all 3 in title: 30 points
  - Article with 1 in title, 1 in excerpt: 13 points
  - Article with keywords only in body: filtered out

#### `match_content_in_database(user_message: str)`
- **Location**: [main.py](main.py#L505-L568)
- **Purpose**: Intelligently matches user queries to database content
- **Features**:
  - Enhanced stop word filtering
  - Progressive keyword search (3 attempts with different combinations)
  - **Relevance scoring and filtering** (NEW)
  - Sorts results by relevance score (highest first)
  - Filters out low-relevance results (score < 3)
  - Verbose logging for debugging
  - Returns matched posts with URLs

#### Message Handler Updates
- **Location**: [main.py](main.py#L866-L893)
- **Change**: Added database check for ALL queries (not just blog-intent queries)
- **Flow**: 
  ```
  Handle specific intents (expeditions, gate prediction, etc.)
  ↓
  Check database for ANY relevant content
  ↓
  If found → Return database content with URLs
  ↓
  If not found → Proceed to AI response
  ```

### System Prompt Updates
- **Location**: [config.py](config.py#L78-L135)
- **Key Changes**:
  - Added "CRITICAL CONTENT RECOMMENDATION POLICY" section
  - Instructs AI that system checks database FIRST
  - AI only responds when NO database content exists
  - Emphasizes not duplicating system checks

## Benefits

1. **✅ Users Get Existing Content First**: No need to manually generate information that already exists on the website
2. **✅ Drives Traffic**: Direct links to explorejungles.com articles increase engagement
3. **✅ Consistency**: Users get official content instead of AI-generated variations
4. **✅ SEO Value**: Promotes existing articles and case studies
5. **✅ Reduced AI Cost**: Less GPT-4 calls when database content is available
6. **✅ Better User Experience**: Curated content instead of generic responses

## Testing

### Diagnostic Tool:
Run the database checker to see what content is available:
```bash
python check_content.py
```

This will show:
- Total published content count
- Content breakdown by type
- Recent articles
- Specific searches (e.g., "maya tigress tadoba")

### Test Cases:
1. **Man-eating tigers**: Should return Jim Corbett case study
2. **Wildlife behavior**: Should return relevant articles if available
3. **Conservation topics**: Should return blog posts if available
4. **Generic greetings**: Should use AI (no database match expected)
5. **Expedition queries**: Should still work as before (MongoDB)

### How to Test:
```bash
# Start the server
uvicorn main:app --reload

# Use Postman or curl
POST http://localhost:8000/sessions/{session_id}/message
{
    "user_id": "test-user-id",
    "message": "tell me about man eating tigers"
}
```

### Expected Response:
```json
{
    "reply": "I found some great resources on this topic:\n\n📖 **BIG CATS TURNED DEADLY**\n   Use of the term \"Man-Eating\" is by convention, as attacks are not limited to 'men' and do not...\n   Read more: https://explorejungles.com/blog/big-cats-turned-deadly\n\nExplore more educational content on ExploreJungles.com! 🌿"
}
```

## Configuration

### Keywords to Exclude (Stop Words):
Located in `match_content_in_database()` function:
```python
stop_words = ['tell', 'me', 'about', 'the', 'a', 'an', 'in', 'blog', 
              'article', 'read', 'learn', 'want', 'to', 'know', 
              'case', 'study', 'what', 'why', 'how', 'is', 'are', 
              'was', 'were', 'can', 'could', 'would', 'should']
```

### Search Limits:
- Max results per search: **5 posts**
- Max keywords tried: **3 attempts** (individual, combined 2, full query)
- Display limit in response: **5 posts max**
- **Minimum relevance score**: **3 points** (filters low-quality matches)
- **Title match value**: **10 points** per keyword
- **Excerpt match value**: **3 points** per keyword

## Recent Improvements (Jan 28, 2026)

### 🎯 Relevance Scoring System
**Problem**: System was returning irrelevant articles that happened to contain keywords somewhere in the content.

**Example**: Query "maya tigress tadoba" returned forest fire articles because they contained "tigress" in the body text.

**Solution**: 
- Implemented weighted relevance scoring
- Title matches worth **10 points** (highly relevant)
- Excerpt matches worth **3 points** (moderately relevant)  
- Body-only matches filtered out (minimum score: 3)
- Results sorted by relevance score

**Impact**: Users now see articles where keywords appear in the title first, which are almost always the most relevant.

### 🔍 Better Filtering
**Problem**: Too many false positives from partial keyword matches.

**Solution**:
- Minimum relevance threshold of 3 points
- Filters out articles with only body text matches
- Requires at least one title or excerpt match

**Impact**: Cleaner, more focused results that actually answer the user's question.

### 🛠️ Database Diagnostic Tool
**Problem**: Hard to debug why certain queries weren't finding expected content.

**Solution**: Created `check_content.py` utility that:
- Shows all published content
- Searches specific keywords
- Displays relevance scores
- Helps identify if content exists in database

**Impact**: Easy troubleshooting and content audit.

## Logging

The system includes verbose logging to help debug content matching:
```
🔍 CONTENT MATCHING - Extracted keywords: ['man', 'eating', 'tigers']
   Searching database with keyword: 'man'
   ✅ Found 2 posts with keyword: 'man'
   ✅ CONTENT MATCH SUCCESS: Found 2 relevant posts
📊 CHECKING DATABASE for relevant content...
✅ Found 2 relevant posts - recommending database content
```

## Future Enhancements

1. **Semantic Search**: Implement vector embeddings for better content matching
2. **Relevance Scoring**: Rank results by relevance instead of just matching
3. **Multi-source Aggregation**: Combine MongoDB + PostgreSQL results
4. **User Feedback**: Track which recommended articles users click
5. **A/B Testing**: Compare database-first vs AI-first approaches

## Related Files

- [main.py](main.py) - Core implementation
- [config.py](config.py) - System prompt and configuration
- [README.md](README.md) - User-facing documentation
- [models.py](models.py) - Database models

---

**Implementation Date**: January 28, 2026  
**Feature Status**: ✅ Production Ready
