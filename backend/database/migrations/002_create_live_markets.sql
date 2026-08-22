-- Migration 002: Create Live Markets Tables
-- Description: Creates tables for real-time market data with TimescaleDB hypertable
-- Author: Polymarket Analytics Platform
-- Date: 2026-08-19

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Live markets table
CREATE TABLE IF NOT EXISTS live.markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255),
    question TEXT,
    yes_price DECIMAL(10, 4),
    no_price DECIMAL(10, 4),
    volume_24h DECIMAL(20, 2),
    liquidity DECIMAL(20, 2),
    category VARCHAR(50),
    source VARCHAR(50) DEFAULT 'gamma_api',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints to ensure data integrity
    CONSTRAINT yes_price_range CHECK (yes_price >= 0 AND yes_price <= 1),
    CONSTRAINT no_price_range CHECK (no_price >= 0 AND no_price <= 1),
    CONSTRAINT positive_volume CHECK (volume_24h >= 0),
    CONSTRAINT positive_liquidity CHECK (liquidity >= 0)
);

COMMENT ON TABLE live.markets IS 'Active markets from Polymarket Gamma API';

-- Create indexes for common queries
CREATE INDEX idx_live_markets_category ON live.markets(category);
CREATE INDEX idx_live_markets_updated_at ON live.markets(updated_at DESC);
CREATE INDEX idx_live_markets_liquidity ON live.markets(liquidity DESC);
CREATE INDEX idx_live_markets_source ON live.markets(source);

-- Time-series hypertable for price history
CREATE TABLE IF NOT EXISTS live.market_prices (
    time TIMESTAMPTZ NOT NULL,
    market_id VARCHAR(255) NOT NULL,
    yes_price DECIMAL(10, 4),
    no_price DECIMAL(10, 4),
    volume DECIMAL(20, 2),
    liquidity DECIMAL(20, 2),
    PRIMARY KEY (time, market_id)
);

COMMENT ON TABLE live.market_prices IS 'Time-series price history for live markets';

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('live.market_prices', 'time', if_not_exists => TRUE);

-- Create indexes on hypertable
CREATE INDEX idx_market_prices_market_id ON live.market_prices(market_id);
CREATE INDEX idx_market_prices_time ON live.market_prices(time DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION live.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_markets_updated_at
    BEFORE UPDATE ON live.markets
    FOR EACH ROW
    EXECUTE FUNCTION live.update_updated_at_column();

-- Verification queries
SELECT 'Live markets table created' as status, COUNT(*) as count
FROM live.markets
LIMIT 1;

SELECT 'Market prices hypertable created' as status, COUNT(*) as count
FROM live.market_prices
LIMIT 1;
