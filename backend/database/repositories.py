"""
Database Repositories Module for Polymarket Analytics Platform.

Provides CRUD operations for all three schemas:
- Live Markets
- Mock Data
- Resolved Historical Results
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from uuid import UUID

from .connection import DatabaseConnection

logger = logging.getLogger(__name__)


class LiveMarketsRepository:
    """Repository for live market data operations"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create_market(self, market_data: Dict[str, Any]) -> Optional[str]:
        """Create a new live market"""
        try:
            query = """
                INSERT INTO live.markets
                (market_id, slug, question, yes_price, no_price,
                 volume_24h, liquidity, category, source, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (market_id) DO UPDATE
                SET yes_price = EXCLUDED.yes_price,
                    no_price = EXCLUDED.no_price,
                    volume_24h = EXCLUDED.volume_24h,
                    liquidity = EXCLUDED.liquidity,
                    updated_at = EXCLUDED.updated_at
                RETURNING market_id
            """

            result = await self.db.fetchval(
                query,
                market_data.get("market_id"),
                market_data.get("slug"),
                market_data.get("question"),
                market_data.get("yes_price"),
                market_data.get("no_price"),
                market_data.get("volume_24h", 0),
                market_data.get("liquidity", 0),
                market_data.get("category", "Other"),
                market_data.get("source", "gamma_api"),
                datetime.now(UTC),
                datetime.now(UTC)
            )

            return result

        except Exception as e:
            logger.error(f"Error creating market {market_data.get('market_id')}: {e}")
            return None

    async def get_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get a single live market by ID"""
        try:
            query = """
                SELECT * FROM live.markets
                WHERE market_id = $1
            """
            result = await self.db.fetchrow(query, market_id)
            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")
            return None

    async def get_markets(
        self,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get multiple live markets with optional filtering"""
        try:
            if category:
                query = """
                    SELECT * FROM live.markets
                    WHERE category = $1
                    ORDER BY updated_at DESC
                    LIMIT $2 OFFSET $3
                """
                results = await self.db.fetch(query, category, limit, offset)
            else:
                query = """
                    SELECT * FROM live.markets
                    ORDER BY updated_at DESC
                    LIMIT $1 OFFSET $2
                """
                results = await self.db.fetch(query, limit, offset)

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []

    async def update_market(self, market_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing market"""
        try:
            set_clauses = []
            params = []
            param_count = 1

            for key, value in updates.items():
                if key not in ["market_id", "id", "created_at"]:  # Don't update these
                    set_clauses.append(f"{key} = ${param_count}")
                    params.append(value)
                    param_count += 1

            if not set_clauses:
                return False

            params.append(market_id)  # For WHERE clause

            query = f"""
                UPDATE live.markets
                SET {', '.join(set_clauses)}, updated_at = NOW()
                WHERE market_id = ${param_count}
            """

            result = await self.db.execute(query, *params)
            return "UPDATE 1" in result

        except Exception as e:
            logger.error(f"Error updating market {market_id}: {e}")
            return False

    async def delete_market(self, market_id: str) -> bool:
        """Delete a market"""
        try:
            query = "DELETE FROM live.markets WHERE market_id = $1"
            result = await self.db.execute(query, market_id)
            return "DELETE 1" in result

        except Exception as e:
            logger.error(f"Error deleting market {market_id}: {e}")
            return False

    async def get_market_stats(self) -> Dict[str, Any]:
        """Get statistics about live markets"""
        try:
            # Total markets
            total = await self.db.fetchval("SELECT COUNT(*) FROM live.markets")

            # Markets by category
            category_query = """
                SELECT category, COUNT(*) as count
                FROM live.markets
                GROUP BY category
                ORDER BY count DESC
            """
            categories = await self.db.fetch(category_query)

            # Average liquidity
            avg_liquidity = await self.db.fetchval(
                "SELECT AVG(liquidity) FROM live.markets WHERE liquidity > 0"
            )

            return {
                "total_markets": total or 0,
                "category_breakdown": [
                    {"category": row["category"], "count": row["count"]}
                    for row in categories
                ],
                "average_liquidity": float(avg_liquidity) if avg_liquidity else 0.0
            }

        except Exception as e:
            logger.error(f"Error getting market stats: {e}")
            return {
                "total_markets": 0,
                "category_breakdown": [],
                "average_liquidity": 0.0,
                "error": str(e)
            }


class MockMarketsRepository:
    """Repository for mock/simulated market data"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create_mock_market(self, market_data: Dict[str, Any]) -> Optional[str]:
        """Create a new mock market"""
        try:
            query = """
                INSERT INTO mock.markets
                (market_id, slug, question, yes_price, no_price,
                 volume_24h, liquidity, category, scenario_id, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (market_id) DO UPDATE
                SET yes_price = EXCLUDED.yes_price,
                    no_price = EXCLUDED.no_price,
                    scenario_id = EXCLUDED.scenario_id
                RETURNING market_id
            """

            result = await self.db.fetchval(
                query,
                market_data.get("market_id"),
                market_data.get("slug"),
                market_data.get("question"),
                market_data.get("yes_price"),
                market_data.get("no_price"),
                market_data.get("volume_24h", 0),
                market_data.get("liquidity", 0),
                market_data.get("category", "Other"),
                market_data.get("scenario_id"),
                datetime.now(UTC)
            )

            return result

        except Exception as e:
            logger.error(f"Error creating mock market: {e}")
            return None

    async def get_mock_markets(
        self,
        scenario_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get mock markets with optional scenario filter"""
        try:
            if scenario_id:
                query = """
                    SELECT * FROM mock.markets
                    WHERE scenario_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """
                results = await self.db.fetch(query, scenario_id, limit)
            else:
                query = """
                    SELECT * FROM mock.markets
                    ORDER BY created_at DESC
                    LIMIT $1
                """
                results = await self.db.fetch(query, limit)

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error fetching mock markets: {e}")
            return []


class ResolvedMarketsRepository:
    """Repository for resolved/historical market data"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create_resolved_market(self, market_data: Dict[str, Any]) -> Optional[str]:
        """Create a resolved market record"""
        try:
            query = """
                INSERT INTO resolved.markets
                (market_id, slug, question, outcome, winning_outcome,
                 resolution_price, resolved_at, category, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (market_id) DO UPDATE
                SET winning_outcome = EXCLUDED.winning_outcome,
                    resolution_price = EXCLUDED.resolution_price,
                    resolved_at = EXCLUDED.resolved_at
                RETURNING market_id
            """

            result = await self.db.fetchval(
                query,
                market_data.get("market_id"),
                market_data.get("slug"),
                market_data.get("question"),
                market_data.get("outcome"),
                market_data.get("winning_outcome"),
                market_data.get("resolution_price"),
                market_data.get("resolved_at"),
                market_data.get("category", "Other"),
                datetime.now(UTC)
            )

            return result

        except Exception as e:
            logger.error(f"Error creating resolved market: {e}")
            return None

    async def get_resolved_markets(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get resolved markets with optional category filter"""
        try:
            if category:
                query = """
                    SELECT * FROM resolved.markets
                    WHERE category = $1
                    ORDER BY resolved_at DESC
                    LIMIT $2
                """
                results = await self.db.fetch(query, category, limit)
            else:
                query = """
                    SELECT * FROM resolved.markets
                    ORDER BY resolved_at DESC
                    LIMIT $1
                """
                results = await self.db.fetch(query, limit)

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error fetching resolved markets: {e}")
            return []

    async def create_resolved_signal(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """Create a resolved signal record"""
        try:
            query = """
                INSERT INTO resolved.signals
                (market_id, asset, direction, confidence, entry_price,
                 exit_price, pnl, roi, outcome, source, entry_timing_ms,
                 created_at, resolved_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id
            """

            result = await self.db.fetchval(
                query,
                signal_data.get("market_id"),
                signal_data.get("asset"),
                signal_data.get("direction"),
                signal_data.get("confidence"),
                signal_data.get("entry_price"),
                signal_data.get("exit_price"),
                signal_data.get("pnl"),
                signal_data.get("roi"),
                signal_data.get("outcome"),
                signal_data.get("source", "system"),
                signal_data.get("entry_timing_ms"),
                signal_data.get("created_at", datetime.now(UTC)),
                signal_data.get("resolved_at", datetime.now(UTC))
            )

            return result

        except Exception as e:
            logger.error(f"Error creating resolved signal: {e}")
            return None


class MarketPricesRepository:
    """Repository for time-series market price data"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create_price_point(self, price_data: Dict[str, Any]) -> bool:
        """Create a price history point"""
        try:
            query = """
                INSERT INTO live.market_prices
                (time, market_id, yes_price, no_price, volume, liquidity)
                VALUES ($1, $2, $3, $4, $5, $6)
            """

            await self.db.execute(
                query,
                price_data.get("time", datetime.now(UTC)),
                price_data.get("market_id"),
                price_data.get("yes_price"),
                price_data.get("no_price"),
                price_data.get("volume"),
                price_data.get("liquidity")
            )
            return True

        except Exception as e:
            logger.error(f"Error creating price point: {e}")
            return False

    async def get_price_history(
        self,
        market_id: str,
        hours_back: int = 24,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get price history for a market"""
        try:
            query = """
                SELECT * FROM live.market_prices
                WHERE market_id = $1
                  AND time >= NOW() - INTERVAL '1 hour' * $2
                ORDER BY time DESC
                LIMIT $3
            """

            results = await self.db.fetch(query, market_id, hours_back, limit)
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error fetching price history: {e}")
            return []


class PatternRepository:
    """Repository for pattern detection and tracking"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create_pattern(self, pattern_data: Dict[str, Any]) -> Optional[str]:
        """Create a detected pattern record"""
        try:
            query = """
                INSERT INTO analytics.detected_patterns
                (pattern_type, market_id, confidence, strength, direction,
                 pattern_data, detected_at, expires_at, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """

            result = await self.db.fetchval(
                query,
                pattern_data.get("pattern_type"),
                pattern_data.get("market_id"),
                pattern_data.get("confidence"),
                pattern_data.get("strength"),
                pattern_data.get("direction"),
                pattern_data.get("pattern_data"),
                pattern_data.get("detected_at", datetime.now(UTC)),
                pattern_data.get("expires_at"),
                pattern_data.get("is_active", True)
            )

            return result

        except Exception as e:
            logger.error(f"Error creating pattern: {e}")
            return None

    async def get_active_patterns(
        self,
        market_id: Optional[str] = None,
        pattern_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active patterns with optional filters"""
        try:
            conditions = ["is_active = TRUE"]
            params = []
            param_count = 1

            if market_id:
                conditions.append(f"market_id = ${param_count}")
                params.append(market_id)
                param_count += 1

            if pattern_type:
                conditions.append(f"pattern_type = ${param_count}")
                params.append(pattern_type)
                param_count += 1

            # Add expired check
            conditions.append(f"(expires_at IS NULL OR expires_at > NOW())")

            query = f"""
                SELECT * FROM analytics.detected_patterns
                WHERE {' AND '.join(conditions)}
                ORDER BY detected_at DESC
            """

            results = await self.db.fetch(query, *params)
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error fetching active patterns: {e}")
            return []

    async def update_pattern_outcome(
        self,
        pattern_id: str,
        outcome_data: Dict[str, Any]
    ) -> bool:
        """Update pattern with performance outcome"""
        try:
            query = """
                INSERT INTO analytics.pattern_performance
                (pattern_id, market_id, outcome, entry_price, exit_price,
                 pnl_percent, hold_duration_hours, resolved_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """

            await self.db.execute(
                query,
                pattern_id,
                outcome_data.get("market_id"),
                outcome_data.get("outcome"),
                outcome_data.get("entry_price"),
                outcome_data.get("exit_price"),
                outcome_data.get("pnl_percent"),
                outcome_data.get("hold_duration_hours"),
                outcome_data.get("resolved_at", datetime.now(UTC))
            )

            return True

        except Exception as e:
            logger.error(f"Error updating pattern outcome: {e}")
            return False

    async def get_pattern_performance_metrics(self, pattern_type: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for patterns"""
        try:
            if pattern_type:
                query = """
                    SELECT
                        dp.pattern_type,
                        COUNT(pp.id) as total_resolved,
                        SUM(CASE WHEN pp.outcome = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                        AVG(pp.pnl_percent) as avg_pnl_percent
                    FROM analytics.detected_patterns dp
                    LEFT JOIN analytics.pattern_performance pp ON dp.id = pp.pattern_id
                    WHERE dp.pattern_type = $1
                    GROUP BY dp.pattern_type
                """
                result = await self.db.fetchrow(query, pattern_type)
            else:
                query = """
                    SELECT
                        dp.pattern_type,
                        COUNT(pp.id) as total_resolved,
                        SUM(CASE WHEN pp.outcome = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                        AVG(pp.pnl_percent) as avg_pnl_percent
                    FROM analytics.detected_patterns dp
                    LEFT JOIN analytics.pattern_performance pp ON dp.id = pp.pattern_id
                    GROUP BY dp.pattern_type
                """
                results = await self.db.fetch(query)
                return {
                    row["pattern_type"]: {
                        "total_resolved": row["total_resolved"],
                        "successful": row["successful"],
                        "win_rate": (row["successful"] / row["total_resolved"]) if row["total_resolved"] > 0 else 0,
                        "avg_pnl_percent": row["avg_pnl_percent"]
                    }
                    for row in results
                }

            if result:
                return {
                    pattern_type: {
                        "total_resolved": result["total_resolved"],
                        "successful": result["successful"],
                        "win_rate": (result["successful"] / result["total_resolved"]) if result["total_resolved"] > 0 else 0,
                        "avg_pnl_percent": result["avg_pnl_percent"]
                    }
                }

            return {}

        except Exception as e:
            logger.error(f"Error getting pattern performance: {e}")
            return {}

    async def cleanup_expired_patterns(self, hours: int = 24) -> int:
        """Remove expired patterns"""
        try:
            query = """
                DELETE FROM analytics.detected_patterns
                WHERE expires_at < NOW() - INTERVAL '1 hour' * $1
            """

            result = await self.db.execute(query, hours)
            # Extract count from result (e.g., "DELETE 15" -> 15)
            count = int(result.split()[-1]) if result and "DELETE" in result else 0
            return count

        except Exception as e:
            logger.error(f"Error cleaning up patterns: {e}")
            return 0

    async def create_composite_signal(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """Create a composite signal record"""
        try:
            query = """
                INSERT INTO analytics.composite_signals
                (market_id, direction, composite_score, confidence, strength_level,
                 factor_data, signal_age_seconds, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """

            result = await self.db.fetchval(
                query,
                signal_data.get("market_id"),
                signal_data.get("direction"),
                signal_data.get("composite_score"),
                signal_data.get("confidence"),
                signal_data.get("strength_level"),
                signal_data.get("factor_data"),
                signal_data.get("signal_age_seconds", 0),
                signal_data.get("is_active", True)
            )

            return result

        except Exception as e:
            logger.error(f"Error creating composite signal: {e}")
            return None

    async def get_composite_signals(
        self,
        market_id: Optional[str] = None,
        active_only: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get composite signals"""
        try:
            conditions = []
            params = []
            param_count = 1

            if market_id:
                conditions.append(f"market_id = ${param_count}")
                params.append(market_id)
                param_count += 1

            if active_only:
                conditions.append(f"is_active = TRUE")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                SELECT * FROM analytics.composite_signals
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_count}
            """

            params.append(limit)
            results = await self.db.fetch(query, *params)
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error fetching composite signals: {e}")
            return []


# Factory function to get repositories
def get_repositories(db: DatabaseConnection) -> Dict[str, Any]:
    """Get all repository instances"""
    return {
        "live_markets": LiveMarketsRepository(db),
        "mock_markets": MockMarketsRepository(db),
        "resolved_markets": ResolvedMarketsRepository(db),
        "market_prices": MarketPricesRepository(db),
        "patterns": PatternRepository(db)
    }
