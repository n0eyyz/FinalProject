# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`pind_server` is a FastAPI-based backend server that extracts location information from YouTube videos and manages user authentication. The system uses YouTube video transcripts and Google's Gemini AI to identify and extract geographical locations mentioned in videos.

## Development Commands

### Server Management

- Start development server: `uvicorn app.main:app --reload --host 0.0.0.0 --port 9001`
- Install dependencies: `pip install -r requirements.txt`

### Database Operations

- Create new migration: `alembic revision --autogenerate -m "Your migration message"`
- Apply migrations: `alembic upgrade head`
- Downgrade migration: `alembic downgrade -1`

### Database Setup

Database configuration is handled through environment variables (DATABASE_URL or DB_URL) loaded from a `.env` file in the project root. The system uses PostgreSQL as the primary database.

## Architecture Overview

### Core Components

**Models (`models.py`)**: Defines SQLAlchemy ORM models:

- `Users`: User authentication and profiles
- `Contents`: YouTube video metadata and transcripts
- `Places`: Extracted location data with coordinates
- `ContentPlaces`: Many-to-many relationship between content and places
- `UserContentHistory`: User activity tracking

**API Structure**:

- `app/main.py`: FastAPI application entry point with CORS middleware
- `app/routers/`: API endpoints (`auth.py`, `youtube.py`)
- `app/repositories/`: Database access layer (`users.py`, `locations.py`)
- `app/schemas/`: Pydantic models for request/response validation
- `app/utils/`: Utility functions (hashing, JWT tokens, URL processing)

**External Services**:

- `crawlers/youtube.py`: YouTube transcript extraction using `youtube-transcript-api`
- `nlp/gemini_location.py`: Location extraction using Google's Gemini AI
- `app/services/extractor.py`: Orchestrates transcript and location extraction

### Authentication Flow

JWT-based authentication using OAuth2 password flow. Users authenticate with email/password, receive JWT tokens for subsequent API calls. The `app/dependencies.py` provides dependency injection for protected endpoints.

### Data Processing Pipeline

1. YouTube URL → Video ID extraction (`app/utils/url.py`)
2. Transcript extraction via YouTube API (`crawlers/youtube.py`)
3. Location extraction using Gemini AI (`nlp/gemini_location.py`)
4. Data persistence with duplicate prevention (`app/repositories/locations.py`)
5. User history tracking for content access

### Database Schema

Uses composite unique constraints to prevent duplicate places (name + lat + lng) and content-place relationships. Migration history is managed through Alembic with version files in `migrations/versions/`.

## Configuration Notes

- Environment variables are loaded via `python-dotenv` from project root `.env` file
- Database URL configuration supports both `DATABASE_URL` and `DB_URL` environment variables
- CORS is configured for all origins (development setup - should be restricted in production)
- SSL/TLS certificate paths are configured but commented out in `app/main.py`

## Key Dependencies

**Core Framework**: FastAPI, SQLAlchemy, Alembic, Uvicorn
**YouTube Processing**: `youtube-transcript-api`, `yt-dlp`
**AI/ML**: Google Generative AI (Gemini), `transformers`, `torch`
**Image/Text Processing**: `easyocr`, `opencv-python-headless`, `selenium`
**Audio Processing**: `librosa`

## Development Patterns

- Uses repository pattern for database operations
- Pydantic schemas for data validation
- Dependency injection for database sessions and user authentication
- Comprehensive logging in YouTube processing pipeline
- Environment-based configuration management

## Reply

- Default to Korean, and only switch to English if I type 'in English'.
