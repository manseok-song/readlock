-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas for different services
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS book;
CREATE SCHEMA IF NOT EXISTS reading;
CREATE SCHEMA IF NOT EXISTS community;
CREATE SCHEMA IF NOT EXISTS gamification;

-- Grant privileges
GRANT ALL PRIVILEGES ON SCHEMA auth TO readlock;
GRANT ALL PRIVILEGES ON SCHEMA book TO readlock;
GRANT ALL PRIVILEGES ON SCHEMA reading TO readlock;
GRANT ALL PRIVILEGES ON SCHEMA community TO readlock;
GRANT ALL PRIVILEGES ON SCHEMA gamification TO readlock;

-- Create indexes for common searches (will be created by Alembic, but good to have as reference)
-- CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users (email);
-- CREATE INDEX IF NOT EXISTS idx_books_isbn ON book.books (isbn);
-- CREATE INDEX IF NOT EXISTS idx_reading_sessions_user ON reading.reading_sessions (user_id, created_at);
