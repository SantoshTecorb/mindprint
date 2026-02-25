-- PostgreSQL Database Setup for Memory Data Collection System
-- Run this script to create the database and user

-- Create database (run as postgres user)
CREATE DATABASE memorydb;

-- Create user for the application
CREATE USER nanobot WITH PASSWORD 'your_secure_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE memorydb TO nanobot;

-- Connect to the memorydb database and run:
-- \c memorydb

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO nanobot;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nanobot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nanobot;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nanobot;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO nanobot;

-- Test connection (optional)
-- \connect memorydb nanobot
-- SELECT current_database(), current_user;
