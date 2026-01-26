# MongoDB to PostgreSQL Migration Guide

## Overview
This guide covers the migration from MongoDB (junglore.com) to PostgreSQL (explorejungles.com) for the Faunabot wildlife chatbot.

## Changes Made

### 1. Database Migration
- **Old**: MongoDB (`jungloreprod` database)
- **New**: PostgreSQL database

### 2. Domain Change
- **Old**: junglore.com
- **New**: explorejungles.com

### 3. Updated Files
- `requirements.txt` - Added PostgreSQL dependencies (asyncpg, sqlalchemy, psycopg2-binary)
- `config.py` - Changed all URLs from junglore.com to explorejungles.com
- `models.py` - Created SQLAlchemy models for PostgreSQL
- `main.py` - Updated all database operations to use PostgreSQL

### 4. Core Functionality Preserved
✓ Knowledge base and AI responses remain unchanged
✓ Wildlife information queries work the same
✓ Expedition recommendations continue to function
✓ Predictive model references maintained
✓ Redis caching still active

## Prerequisites

1. PostgreSQL database instance (local or cloud)
2. Python 3.8+
3. Access to existing MongoDB database (for migration)

## Environment Variables

Update your `.env` file with the following:

```bash
# PostgreSQL Database
DATABASE_URL=postgresql://username:password@host:port/database_name
# Or for async:
# DATABASE_URL=postgresql+asyncpg://username:password@host:port/database_name

# Redis (unchanged)
REDIS_URL=redis://localhost:6379

# OpenAI (unchanged)
OPENAI_API_KEY=your_openai_api_key

# MongoDB (only needed for migration)
MONGODB_URI=mongodb://username:password@host:port/jungloreprod
```

## Installation Steps

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Initialize PostgreSQL Database

This creates all necessary tables:

```bash
python scripts/init_db.py
```

### Step 3: Migrate Data from MongoDB (Optional)

If you have existing data in MongoDB that needs to be migrated:

```bash
python scripts/migrate_mongodb_to_postgres.py
```

This will transfer:
- User accounts
- Chat sessions and history
- Expedition packages

### Step 4: Run the Application

```bash
uvicorn main:app --reload
```

## Database Schema

### Users Table
- `id` (String, Primary Key)
- `email` (String, Unique)
- `name` (String)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Sessions Table
- `session_id` (String, Primary Key)
- `user_id` (String, Foreign Key)
- `title` (String)
- `created_at` (DateTime)
- `history` (JSON)

### Packages Table
- `id` (String, Primary Key)
- `title` (String)
- `description` (Text)
- `heading` (String)
- `region` (String)
- `duration` (String)
- `type` (String)
- `price` (Float)
- `currency` (String)
- `image` (String)
- `additional_images` (JSON)
- `features` (JSON)
- `date` (JSON)
- `status` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)

## API Endpoints (Unchanged)

- `GET /health` - Health check
- `POST /sessions/` - Create new chat session
- `GET /sessions/` - List user sessions
- `GET /sessions/{session_id}/history` - Get chat history
- `POST /sessions/{session_id}/message` - Send message
- `GET /packages/{package_id}/details` - Get package details

## Testing

1. **Health Check**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Create Session**
   ```bash
   curl -X POST http://localhost:8000/sessions/ \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_user", "title": "Test Chat"}'
   ```

3. **Send Message**
   ```bash
   curl -X POST http://localhost:8000/sessions/{session_id}/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_user", "message": "Tell me about tiger safaris"}'
   ```

## Troubleshooting

### Database Connection Issues

If you see connection errors:
1. Verify DATABASE_URL in `.env`
2. Check PostgreSQL is running
3. Verify database credentials and network access

### Migration Issues

If migration script fails:
1. Check both MongoDB and PostgreSQL connections
2. Ensure sufficient disk space
3. Check logs for specific error messages

### Redis Connection

If Redis caching fails:
1. Verify REDIS_URL in `.env`
2. Ensure Redis is running
3. The app will fallback to PostgreSQL if Redis is unavailable

## Production Deployment

### Heroku PostgreSQL

```bash
# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# The DATABASE_URL will be automatically set
# The code handles conversion from postgres:// to postgresql+asyncpg://
```

### AWS RDS PostgreSQL

1. Create RDS PostgreSQL instance
2. Set security groups to allow inbound connections
3. Update DATABASE_URL in environment variables

### Render/Railway

1. Create PostgreSQL database service
2. Copy connection string
3. Set as DATABASE_URL environment variable

## Key Differences from MongoDB

1. **Query Syntax**: SQLAlchemy ORM instead of PyMongo
2. **IDs**: Still using string UUIDs for compatibility
3. **Relationships**: Proper foreign key relationships
4. **Transactions**: Explicit commit/rollback handling
5. **Case-Sensitive Searches**: Using `.ilike()` for case-insensitive matching

## Rollback Plan

If you need to rollback to MongoDB:
1. Keep the MongoDB connection string in `.env`
2. Revert to the previous commit
3. Redeploy with old codebase

## Support

For issues or questions:
1. Check application logs
2. Verify environment variables
3. Test database connectivity independently
4. Review migration script output

## Next Steps

After successful migration:
1. Monitor application performance
2. Verify all endpoints work correctly
3. Test expedition recommendations
4. Validate predictive model links
5. Remove MongoDB dependency once stable
