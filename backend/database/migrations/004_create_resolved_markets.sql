-- Migration 004: Create Resolved Markets Tables
-- Description: Creates tables for historical resolved markets and performance tracking
-- Author: Polymarket Analytics Platform
-- Date: 2026-08-19

-- Resolved markets table
CREATE TABLE IF NOT EXISTS resolved.markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255),
    question TEXT,
    outcome VARCHAR(50),
    winning_outcome VARCHAR(50), -- YES or NO
    resolution_price DECIMAL(10, 4),
    resolved_at TIMESTAMP,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT resolved_winning_outcome CHECK (winning_outcome IN ('YES', 'NO'))
);

COMMENT ON TABLE resolved.markets IS 'Historical resolved markets for accuracy analysis';

-- Create indexes
CREATE INDEX idx_resolved_markets_category ON resolved.markets(category);
CREATE INDEX idx_resolved_markets_resolved_at ON resolved.markets(resolved_at DESC);
CREATE INDEX idx_resolved_markets_outcome ON resolved.markets(outcome);
CREATE INDEX idx_resolved_markets_winning ON resolved.markets(winning_outcome);

-- Resolved signals table for tracking actual performance
CREATE TABLE IF NOT EXISTS resolved.signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id VARCHAR(255),
    asset VARCHAR(50),
    direction VARCHAR(10) NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL,
    entry_price DECIMAL(20, 8),
    exit_price DECIMAL(20, 8),
    pnl DECIMAL(20, 8),
    roi DECIMAL(10, 4), -- Return on investment percentage
    outcome VARCHAR(10) NOT NULL, -- WIN, LOSS
    source VARCHAR(50),
    entry_timing_ms INTEGER, -- Time from signal to entry in milliseconds
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,

    -- Constraints
    CONSTRAINT resolved_direction_check CHECK (direction IN ('UP', 'DOWN')),
    CONSTRAINT resolved_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT resolved_outcome_check CHECK (outcome IN ('WIN', 'LOSS'))
);

COMMENT ON TABLE resolved.signals IS 'Historical signal performance for analytics';

-- Create indexes
CREATE INDEX idx_resolved_signals_market_id ON resolved.signals(market_id);
CREATE INDEX idx_resolved_signals_asset ON resolved.signals(asset);
CREATE INDEX idx_resolved_signals_outcome ON resolved.signals(outcome);
CREATE INDEX idx_resolved_signals_confidence ON resolved.signals(confidence);
CREATE INDEX idx_resolved_signals_resolved_at ON resolved.signals(resolved_at DESC);

-- Category performance view
CREATE OR REPLACE VIEW resolved.category_performance AS
SELECT
    category,
    COUNT(*) as total_markets,
    SUM(CASE WHEN winning_outcome = 'YES' THEN 1 ELSE 0 END) as yes_outcomes,
    SUM(CASE WHEN winning_outcome = 'NO' THEN 1 ELSE 0 END) as no_outcomes,
    AVG(resolution_price) as avg_resolution_price
FROM resolved.markets
GROUP BY category
ORDER BY total_markets DESC;

COMMENT ON VIEW resolved.category_performance IS 'Performance metrics by category';

-- Signal performance view
CREATE OR REPLACE VIEW resolved.signal_performance AS
SELECT
    ROUND(confidence, 2) as confidence_bucket,
    COUNT(*) as total_signals,
    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as winning_signals,
    ROUND(
        100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        2
    ) as win_rate_pct,
    ROUND(AVG(pnl), 4) as avg_pnl,
    ROUND(AVG(roi), 4) as avg_roi
FROM resolved.signals
GROUP BY ROUND(confidence, 2)
ORDER BY confidence_bucket;

COMMENT ON VIEW resolved.signal_performance IS 'Win rate and ROI by confidence level';

-- Verification queries
SELECT 'Resolved markets table created' as status, COUNT(*) as count
FROM resolved.markets
LIMIT 1;

SELECT 'Resolved signals table created' as status, COUNT(*) as count
FROM resolved.signals
LIMIT 1;
