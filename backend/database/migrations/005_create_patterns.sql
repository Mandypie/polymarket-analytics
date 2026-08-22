-- Migration 005: Pattern Detection Tables
-- Creates tables for storing detected patterns and their performance

-- Create analytics schema if not exists
CREATE SCHEMA IF NOT EXISTS analytics;

-- Detected patterns table
CREATE TABLE IF NOT EXISTS analytics.detected_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(50) NOT NULL,
    market_id VARCHAR(255) NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    strength VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('LONG', 'SHORT', 'NEUTRAL')),
    pattern_data JSONB NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT pattern_type_check CHECK (pattern_type IN (
        'momentum_reversal',
        'liquidity_trap',
        'cross_market',
        'resolution_prob',
        'sentiment'
    ))
);

-- Pattern performance tracking table
CREATE TABLE IF NOT EXISTS analytics.pattern_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID REFERENCES analytics.detected_patterns(id) ON DELETE CASCADE,
    market_id VARCHAR(255) NOT NULL,
    outcome VARCHAR(10) NOT NULL CHECK (outcome IN ('SUCCESS', 'FAILURE', 'PENDING')),
    entry_price DECIMAL(10, 8),
    exit_price DECIMAL(10, 8),
    pnl_percent DECIMAL(10, 4),
    hold_duration_hours INTEGER,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Composite signals table (for multi-factor signals)
CREATE TABLE IF NOT EXISTS analytics.composite_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id VARCHAR(255) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('LONG', 'SHORT', 'NEUTRAL')),
    composite_score DECIMAL(3, 2) NOT NULL CHECK (composite_score >= 0 AND composite_score <= 1),
    confidence DECIMAL(3, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    strength_level VARCHAR(20) NOT NULL,
    factor_data JSONB NOT NULL,  -- Stores factor breakdown
    signal_age_seconds INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_patterns_market ON analytics.detected_patterns(market_id);
CREATE INDEX IF NOT EXISTS idx_patterns_active ON analytics.detected_patterns(is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON analytics.detected_patterns(pattern_type, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_detected_at ON analytics.detected_patterns(detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_pattern_perf_pattern ON analytics.pattern_performance(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_perf_market ON analytics.pattern_performance(market_id);
CREATE INDEX IF NOT EXISTS idx_pattern_perf_outcome ON analytics.pattern_performance(outcome);

CREATE INDEX IF NOT EXISTS idx_composite_market ON analytics.composite_signals(market_id);
CREATE INDEX IF NOT EXISTS idx_composite_active ON analytics.composite_signals(is_active, created_at DESC);

-- Comments for documentation
COMMENT ON TABLE analytics.detected_patterns IS 'Stores detected trading patterns with metadata';
COMMENT ON TABLE analytics.pattern_performance IS 'Tracks performance outcomes of detected patterns';
COMMENT ON TABLE analytics.composite_signals IS 'Stores multi-factor composite signals with factor breakdown';

COMMENT ON COLUMN analytics.detected_patterns.pattern_data IS 'JSON metadata containing pattern-specific information (RSI, momentum, etc.)';
COMMENT ON COLUMN analytics.composite_signals.factor_data IS 'JSON array of factor scores with weights and contributions';
