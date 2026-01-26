# Blog/Content Recommendation Feature - Implementation Summary

## Overview
Added educational content recommendation functionality to the Junglore chatbot, enabling users to discover articles, blogs, and case studies from ExploreJungles.com.

---

## Changes Made

### 1. **New Functions Added to [main.py](main.py)**

#### `find_blog_content(topic, max_results=10)`
- **Purpose**: Query PostgreSQL `content` table for published blog posts
- **Parameters**: 
  - `topic` (optional): Keywords to search in title, excerpt, and content
  - `max_results`: Limit number of results (default: 10)
- **Returns**: List of formatted blog post dictionaries with:
  - `id`, `title`, `slug`, `excerpt`, `author`, `image`, `type`, `views`
  - `url`: Direct link to article (format: `https://explorejungles.com/blog/{slug}`)
- **Database**: PostgreSQL `content` table (status = 'PUBLISHED')

#### `match_blog_content(user_message)`
- **Purpose**: Analyze user message and match against blog content
- **Logic**:
  - Extracts keywords (filters out stop words like 'tell', 'me', 'about', 'the')
  - Combines first 3 keywords as search topic
  - Calls `find_blog_content()` with extracted topic
- **Returns**: Dictionary with:
  - `matched`: Boolean indicating if posts found
  - `posts`: List of matched blog posts
  - `topic`: Combined search keywords

---

### 2. **Intent Detection Updates ([main.py](main.py))**

#### Updated `detect_travel_intent()` function
- Added `blog_intent` detection using new `BLOG_KEYWORDS`
- Returns additional field: `blog_intent: bool`

#### Added Blog Intent Handling in `/sessions/{session_id}/message` endpoint
- **Trigger**: When `blog_intent == True`
- **Flow**:
  1. Calls `match_blog_content()` to find relevant articles
  2. If posts found:
     - Formats response with titles, excerpts, and URLs
     - Shows top 5 results
     - Includes markdown formatting (📖 emoji, **bold titles**)
  3. If no posts found:
     - Asks user to specify topic
     - Suggests exploring ExploreJungles.com
  4. Saves conversation to history (PostgreSQL + Redis)
  5. Returns bot reply immediately (no GPT call)

---

### 3. **Configuration Updates ([config.py](config.py))**

#### New Constant: `BLOG_KEYWORDS`
```python
BLOG_KEYWORDS = [
    'blog', 'article', 'read', 'learn', 'information', 'guide', 'tell me about',
    'case study', 'podcast', 'story', 'post', 'content', 'education',
    'conservation', 'research', 'behavior', 'habitat', 'facts', 'know more',
    'understand', 'explain', 'info', 'details', 'study'
]
```

#### Updated `SYSTEM_PROMPT`
- Added section for **EDUCATIONAL CONTENT** rules
- Mentions PostgreSQL `content` table
- Instructs assistant to recommend blog posts when users want to learn
- Emphasizes including article URLs from ExploreJungles.com

---

### 4. **Documentation ([README.md](README.md))**

#### Updated Features Section
- Added dual database architecture explanation:
  - **MongoDB**: Junglore.com expeditions
  - **PostgreSQL**: ExploreJungles.com educational content
- Added description of blog recommendation feature
- Clarified intent detection for both expeditions and content

---

## How It Works

### Example User Flow

**User**: "Tell me about tiger behavior"

**System**:
1. Detects `blog_intent = True` (keyword: "tell me about")
2. Extracts keywords: `['tiger', 'behavior']`
3. Queries PostgreSQL:
   ```sql
   SELECT * FROM content
   WHERE status = 'PUBLISHED'
   AND (LOWER(title) LIKE '%tiger behavior%' OR ...)
   LIMIT 5
   ```
4. Formats response:
   ```
   Here are some articles you might find interesting:

   📖 **Big Cats Turned Deadly - Understanding Man-Eater Behavior**
      Explore the transformation of tigers into man-eaters...
      Read more: https://explorejungles.com/blog/big-cats-deadly

   📖 **Tiger Conservation in India**
      Learn about conservation efforts...
      Read more: https://explorejungles.com/blog/tiger-conservation

   Explore more educational content on ExploreJungles.com! 🌿
   ```

---

## Database Structure

### PostgreSQL `content` Table
- **Columns Used**:
  - `id` (UUID): Primary key
  - `title` (VARCHAR): Article title
  - `slug` (VARCHAR): URL-friendly identifier
  - `excerpt` (TEXT): Short description
  - `content` (TEXT): Full article content
  - `author_name` (VARCHAR): Author
  - `featured_image` (VARCHAR): Image path
  - `type` (ENUM): Content type (BLOG, DAILY_UPDATE, etc.)
  - `status` (ENUM): Publication status (PUBLISHED, DRAFT)
  - `published_at` (TIMESTAMP): Publication date
  - `view_count` (INTEGER): Number of views

- **Current Data**: 11 published articles

---

## Testing the Feature

### Test Queries
Try these queries to test blog recommendations:

1. **"Tell me about tiger conservation"**
   - Should return articles about conservation

2. **"Can I read articles about leopards?"**
   - Triggers blog_intent with "read" keyword

3. **"Learn more about wildlife behavior"**
   - Triggers blog_intent with "learn" keyword

4. **"Information about man-eating big cats"**
   - Should match existing article about man-eaters

5. **"Case studies on jungle ecosystems"**
   - Triggers blog_intent with "case studies" keyword

---

## Benefits

1. **Educational Value**: Users can discover in-depth articles beyond chatbot responses
2. **SEO Traffic**: Drives users to ExploreJungles.com blog
3. **Dual Purpose**: Chatbot serves both planning (expeditions) and learning (content) needs
4. **Dynamic Matching**: Uses keyword extraction for flexible search
5. **Database-Driven**: Content recommendations stay current with PostgreSQL updates

---

## Future Enhancements

Potential improvements for future iterations:

1. **Content Categorization**: Add filtering by content type (BLOG vs. CASE_STUDY vs. PODCAST)
2. **Popularity Sorting**: Sort by `view_count` or engagement metrics
3. **Semantic Search**: Use embeddings for better topic matching
4. **Related Content**: Suggest "related articles" after showing initial results
5. **Analytics**: Track which articles chatbot users click most

---

## Technical Notes

- **No GPT Call**: Blog recommendations bypass OpenAI to save API costs and reduce latency
- **SQL Injection Protection**: Uses parameterized queries with SQLAlchemy
- **Graceful Degradation**: Returns empty list on errors (doesn't break chatbot)
- **Caching**: Results saved to Redis via conversation history
- **URL Format**: `https://explorejungles.com/blog/{slug}` (matches existing site structure)

---

**Implementation Date**: January 16, 2026  
**Status**: ✅ Complete and tested
