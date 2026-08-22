-- Migration 003: Create Mock Data Tables
-- Description: Creates tables for simulated data used in backtesting
-- Author: Polymarket Analytics Platform
-- Date: 2026-08-19

-- Mock markets table
CREATE TABLE IF NOT EXISTS mock.markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255),
    question TEXT,
    yes_price DECIMAL(10, 4),
    no_price DECIMAL(10, 4),
    volume_24h DECIMAL(20, 2),
    liquidity DECIMAL(20, 2),
    category VARCHAR(50),
    scenario_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT mock_yes_price_range CHECK (yes_price >= 0 AND yes_price <= 1),
    CONSTRAINT mock_no_price_range CHECK (no_price >= 0 AND no_price <= 1),
    CONSTRAINT mock_positive_volume CHECK (volume_24h >= 0),
    CONSTRAINT mock_positive_liquidity CHECK (liquidity >= 0)
);

COMMENT ON TABLE mock.markets IS 'Simulated market data for backtesting scenarios';

-- Create indexes
CREATE INDEX idx_mock_markets_category ON mock.markets(category);
CREATE INDEX idx_mock_markets_scenario ON mock.markets(scenario_id);
CREATE INDEX idx_mock_markets_created_at ON mock.markets(created_at DESC);

-- Mock signals table for backtesting strategies
CREATE TABLE IF NOT EXISTS mock.signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset VARCHAR(50) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- UP or DOWN
    confidence DECIMAL(3, 2) NOT NULL, -- 0.00 to 1.00
    entry_price DECIMAL(20, 8),
    exit_price DECIMAL(20, 8),
    source VARCHAR(50),
    market_id VARCHAR(255),
    scenario_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    outcome VARCHAR(10), -- WIN, LOSS, PENDING

    -- Constraints
    CONSTRAINT mock_asset_check CHECK (asset IN ('BTC', 'ETH', 'SOL', 'XRP', 'OTHER')),
    CONSTRAINT mock_direction_check CHECK (direction IN ('UP', 'DOWN')),
    CONSTRAINT mock_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT mock_outcome_check CHECK (outcome IN ('WIN', 'LOSS', 'PENDING'))
);

COMMENT ON TABLE mock.signals IS 'Simulated trading signals for strategy backtesting';

-- Create indexes
CREATE INDEX idx_mock_signals_asset ON mock.signals(asset);
CREATE INDEX idx_mock_signals_scenario ON mock.signals(scenario_id);
CREATE INDEX idx_mock_signals_outcome ON mock.signals(outcome);
CREATE INDEX idx_mock_signals_created_at ON mock.signals(created_at DESC);

-- Verification queries
SELECT 'Mock markets table created' as status, COUNT(*) as count
FROM mock.markets
LIMIT 1;

SELECT 'Mock signals table created' as status, COUNT(*) as count
FROM mock.signals
LIMIT 1;
