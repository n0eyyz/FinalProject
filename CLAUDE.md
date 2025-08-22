# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **FastAPI-based YouTube location extraction server** that processes YouTube videos to extract location information using AI/ML services. The project has been **refactored from Celery-based async processing to synchronous processing** (as noted in the recent commits).

**Core functionality:**

- Extract location data from YouTube videos using transcripts and AI analysis
- User authentication and content history tracking
- PostgreSQL database with async SQLAlchemy
- RESTful API with automatic documentation

## Development Commands

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables in .env file
DATABASE_URL="postgresql://user:password@host:port/database"
```

### Database Management

```bash
# Apply database migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Initialize database (if needed)
python scripts/init_db.py
```

### Running the Application

```bash
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Development with auto-reload
uvicorn app.main:app --reload
```

### Testing

```bash
# Run tests with pytest
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_users.py
```

## Architecture Overview

### Core Processing Flow

The application follows a **synchronous processing model** (post-Celery removal):

1. **API Request** → FastAPI router receives YouTube URL
2. **Cache Check** → Check if video already processed in database
3. **Extraction** → If new, extract transcript and metadata from YouTube
4. **AI Analysis** → Use Google Gemini API to extract location data from transcript
5. **Storage** → Save results to PostgreSQL database
6. **Response** → Return location data to client

### Layer Architecture

```
┌─────────────────┐
│   API Routes    │  FastAPI routers (youtube, auth, users)
├─────────────────┤
│   Repositories  │  Database CRUD operations with async SQLAlchemy
├─────────────────┤
│   Services      │  Business logic (ExtractorService, GeminiService)
├─────────────────┤
│   Utils         │  Utilities (auth, email, hashing, URL parsing)
├─────────────────┤
│   Models        │  SQLAlchemy ORM models
└─────────────────┘
```

### Database Schema

**Core entities:**

- `Users` - User accounts with email/password auth
- `Contents` - Processed YouTube videos with metadata
- `Places` - Extracted location data with coordinates
- `UserContentHistory` - User access history tracking
- `ContentPlaces` - Many-to-many relationship between content and places

### Key Design Patterns

**Async/Await Throughout**: All database operations and external API calls use async/await

```python
# Database operations
async def get_content_by_id(db: AsyncSession, content_id: str)

# API routes
@router.post("/process")
async def process_youtube_url_and_get_places(...)
```

**Repository Pattern**: Database operations abstracted into repository layer

```python
# app/repositories/locations.py - handles all location-related DB operations
# app/repositories/users.py - handles user-related DB operations
```

**Service Layer**: Business logic separated from API routes

```python
# app/services/extractor.py - handles YouTube data extraction
# nlp/gemini_location.py - handles AI location analysis
```

## Critical Implementation Details

### URL Processing

YouTube URLs are processed through `app/utils/url.py` to extract video IDs. The system supports various YouTube URL formats.

### Authentication System

- JWT-based authentication using `python-jose`
- Password hashing with `passlib` and bcrypt
- Optional authentication on main processing endpoint (supports guest users)

### Database Configuration

- Uses async PostgreSQL with `asyncpg` driver
- SSL configuration with environment variable toggle (`DB_SSL_INSECURE`)
- Connection pooling and prepared statement caching disabled for compatibility

### Error Handling

- Comprehensive logging throughout the application
- Graceful fallbacks for missing transcripts or AI analysis failures
- Database transaction handling with automatic rollback

### External Dependencies

- **Google Gemini API** for location extraction from text
- **YouTube APIs** via `youtube-transcript-api` and `yt-dlp`
- **PostgreSQL** for persistent storage
- **FastAPI** for web framework with automatic API documentation

## Important Notes

### Recent Celery Removal

The project recently removed Celery async task processing in favor of synchronous processing. When working on the codebase:

- No Celery workers or Redis message broker needed
- All processing happens synchronously in API endpoints
- Previous job status tracking endpoints may need removal/refactoring

### Environment Variables

Critical environment variables that must be configured:

```bash
DATABASE_URL=postgresql://user:pass@host:port/dbname
# Optional: DB_SSL_INSECURE=true (for development)
```

### Development Workflow

1. Make model changes in `models.py`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Apply migration: `alembic upgrade head`
4. Test changes with `pytest`
5. Update repository/service layers as needed

### API Documentation

When server is running, access auto-generated API docs at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### response

- always use Korean unless I saying in English.
