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

-- 1. Memory Data Table (Seller assets)
CREATE TABLE IF NOT EXISTS memory_data (
    id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    content TEXT NOT NULL,
    file_hash VARCHAR(32) NOT NULL,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100),
    extra_metadata TEXT,
    UNIQUE(file_path, file_hash)
);

-- 2. Rentals Table (Buyer tokens)
CREATE TABLE IF NOT EXISTS rentals (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    seller_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- 3. Sellers Table (Traceable installations)
CREATE TABLE IF NOT EXISTS sellers (
    user_id VARCHAR(100) PRIMARY KEY,
    hostname TEXT,
    os_name TEXT,
    os_version TEXT,
    python_version TEXT,
    install_path TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 4. Buyers Table (Traceable persona adoption)
CREATE TABLE IF NOT EXISTS buyers (
    user_id VARCHAR(100) PRIMARY KEY,
    hostname TEXT,
    os_name TEXT,
    os_version TEXT,
    python_version TEXT,
    install_path TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Grant privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nanobot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nanobot;

-- Test connection (optional)
-- \connect memorydb nanobot
-- SELECT current_database(), current_user;
