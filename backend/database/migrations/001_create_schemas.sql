-- Migration 001: Create Schemas
-- Description: Creates the three main schemas for data separation
-- Author: Polymarket Analytics Platform
-- Date: 2026-08-19

-- Create schemas for data separation
CREATE SCHEMA IF NOT EXISTS live;
COMMENT ON SCHEMA live IS 'Real-time market data from Gamma API and CLOB';

CREATE SCHEMA IF NOT EXISTS mock;
COMMENT ON SCHEMA mock IS 'Simulated data for backtesting and strategy validation';

CREATE SCHEMA IF NOT EXISTS resolved;
COMMENT ON SCHEMA resolved IS 'Historical resolved markets and outcomes for accuracy analysis';

-- Verification query
SELECT schema_name, schema_owner
FROM information_schema.schemata
WHERE schema_name IN ('live', 'mock', 'resolved')
ORDER BY schema_name;
