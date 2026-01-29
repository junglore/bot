# Enhanced Response Format - Test Guide

## Changes Implemented

### 1. **Rich Expedition Responses**
When users ask about expeditions, the bot now provides:
- Conversational confirmation ("Yes! We have expeditions planned for [Month] to [Park]")
- Detailed package information (title, duration, description)
- Direct expedition link with call-to-action
- Banner image in response
- Multiple expedition options if available

### 2. **Enhanced Content Responses**
When recommending articles/blogs:
- Featured article with image highlighted
- Excerpt included for context
- Direct links to all relevant articles
- Image data included in response

## Response Format

### Expedition Query Response
```json
{
  "reply": "Yes! We have expeditions planned for February to Tadoba. 🌿\n\n**Dudhwa: Terai's Hidden Kingdom**\n📅 Duration: 2 Nights 3 Days\n\nExperience thrilling safaris and majestic wildlife in a luxurious setting!\n\n🔗 View detailed itinerary and book: https://junglore.com/explore/tadoba-national-park\n\n💡 Each expedition includes expert guides, comfortable accommodations, and curated wildlife experiences!",
  "banner_image": "https://...",
  "expedition_package": {
    "title": "Dudhwa: Terai's Hidden Kingdom",
    "image": "https://...",
    "duration": "2 Nights 3 Days",
    "description": "Unleash your wild side...",
    "url": "https://junglore.com/explore/tadoba-national-park",
    "park": "Tadoba"
  }
}
```

### Educational Content Response
```json
{
  "reply": "I found some great resources on this topic:\n\n**Featured:** BIG CATS TURNED DEADLY\nUnderstanding Man-Eater Behavior...\n\n🔗 Read more: https://explorejungles.com/blog/big-cats-turned-deadly\n\nExplore more educational content on ExploreJungles.com! 🌿",
  "featured_image": "https://...",
  "featured_article": {
    "title": "BIG CATS TURNED DEADLY",
    "excerpt": "Understanding Man-Eater Behavior...",
    "url": "https://explorejungles.com/blog/big-cats-turned-deadly",
    "image": "https://..."
  }
}
```

## Test Cases

### Test 1: Expedition Query with Month and Location
**Input:**
```json
{
  "user_id": "test-user",
  "message": "Suggest safari for February in Tadoba"
}
```

**Expected Output:**
- ✅ Conversational confirmation mentioning February and Tadoba
- ✅ Package title and duration
- ✅ Brief description
- ✅ Direct expedition URL
- ✅ `banner_image` field with image URL
- ✅ `expedition_package` object with full details

### Test 2: General Expedition Query
**Input:**
```json
{
  "user_id": "test-user",
  "message": "Suggest an expedition for February"
}
```

**Expected Output:**
- ✅ List of available parks
- ✅ Prompt to select a specific park
- ✅ No specific package recommendation yet

### Test 3: Educational Content Query
**Input:**
```json
{
  "user_id": "test-user",
  "message": "Tell me about man-eating tigers"
}
```

**Expected Output:**
- ✅ "BIG CATS TURNED DEADLY" article featured
- ✅ Excerpt from article
- ✅ Direct URL to article
- ✅ `featured_image` field if image exists
- ✅ `featured_article` object with details

### Test 4: Specific Park + Month
**Input:**
```json
{
  "user_id": "test-user",
  "message": "Do you have expeditions to Corbett in March?"
}
```

**Expected Output:**
- ✅ "Yes! We have expeditions planned for March to Jim Corbett"
- ✅ Package details with image
- ✅ Expedition URL
- ✅ Additional packages if available

## Testing in Postman

1. **Create/Get Session ID:**
   ```
   POST http://localhost:8000/sessions/
   {
     "user_id": "test-user-123",
     "title": "Test Expedition Chat"
   }
   ```

2. **Test Expedition Query:**
   ```
   POST http://localhost:8000/sessions/{session_id}/message
   {
     "user_id": "test-user-123",
     "message": "Suggest safari for February in Tadoba"
   }
   ```

3. **Check Response Fields:**
   - ✅ `reply` contains conversational text
   - ✅ `banner_image` or `featured_image` contains URL
   - ✅ `expedition_package` or `featured_article` contains structured data

## Frontend Integration

The frontend can now:

### For Expeditions:
```javascript
if (response.expedition_package) {
  // Display expedition card with:
  displayExpeditionCard({
    image: response.expedition_package.image,
    title: response.expedition_package.title,
    duration: response.expedition_package.duration,
    description: response.expedition_package.description,
    link: response.expedition_package.url
  });
}
```

### For Articles:
```javascript
if (response.featured_article) {
  // Display article card with:
  displayArticleCard({
    image: response.featured_article.image,
    title: response.featured_article.title,
    excerpt: response.featured_article.excerpt,
    link: response.featured_article.url
  });
}
```

## Benefits

1. **Better UX**: Users see images and structured information
2. **Higher Engagement**: Visual content increases click-through rates
3. **Clear CTAs**: Direct links with context drive conversions
4. **Mobile-Friendly**: Structured data easier to display on mobile
5. **SEO Value**: Rich snippets possible with structured data

## Notes

- Server auto-reloads when code changes (if running with `--reload`)
- Images are pulled from MongoDB (expeditions) and PostgreSQL (articles)
- If no image exists, response falls back to text-only format
- All responses still include text `reply` field for backward compatibility
