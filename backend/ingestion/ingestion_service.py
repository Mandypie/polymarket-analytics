"""
Data Ingestion Service for Polymarket Analytics Platform.

Periodically fetches market data from Gamma API and stores it in the database.
Separates data into Live, Mock, and Resolved schemas.
"""

import asyncio
import logging
from datetime import datetime, UTC
from typing import Optional, Dict, Any
from dataclasses import dataclass

from backend.database.connection import DatabaseConnection
from .gamma_client import GammaClient, MarketData, get_gamma_client

logger = logging.getLogger(__name__)


@dataclass
class IngestionConfig:
    """Configuration for data ingestion service"""
    interval_seconds: int = 60  # Fetch every 60 seconds
    max_markets_per_batch: int = 100
    enable_live_ingestion: bool = True
    enable_price_history: bool = True
    categories: list[str] = None

    def __post_init__(self):
        if self.categories is None:
            self.categories = ["Politics", "Sports", "Crypto", "Culture"]


class IngestionService:
    """
    Service for ingesting market data from Gamma API into the database.

    Fetches live markets and stores them in the live.markets table.
    Maintains price history in the live.market_prices hypertable.
    """

    def __init__(
        self,
        db: DatabaseConnection,
        gamma_client: Optional[GammaClient] = None,
        config: Optional[IngestionConfig] = None
    ):
        self.db = db
        self.gamma_client = gamma_client
        self.config = config or IngestionConfig()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the ingestion service"""
        if self._running:
            logger.warning("Ingestion service already running")
            return

        self._running = True
        logger.info("Starting ingestion service")

        # Initial ingestion
        await self.ingest_once()

        # Start periodic ingestion
        self._task = asyncio.create_task(self._periodic_ingestion())

    async def stop(self):
        """Stop the ingestion service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Ingestion service stopped")

    async def _periodic_ingestion(self):
        """Periodically ingest market data"""
        while self._running:
            try:
                await asyncio.sleep(self.config.interval_seconds)
                if self._running:
                    await self.ingest_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic ingestion: {e}")

    async def ingest_once(self):
        """Perform a single ingestion cycle"""
        try:
            logger.info("Starting ingestion cycle")

            # Get Gamma client
            if self.gamma_client is None:
                self.gamma_client = await get_gamma_client()

            # Fetch markets
            markets = await self.gamma_client.fetch_markets(
                active=True,
                limit=self.config.max_markets_per_batch
            )

            if not markets:
                logger.warning("No markets fetched from Gamma API")
                return

            # Store in database
            await self._store_markets(markets)

            logger.info(f"Ingestion cycle completed: {len(markets)} markets")

        except Exception as e:
            logger.error(f"Ingestion cycle failed: {e}")

    async def _store_markets(self, markets: list[MarketData]):
        """Store markets in the live.markets table"""
        stored_count = 0
        updated_count = 0

        for market in markets:
            try:
                # Check if market exists
                query = """
                    SELECT id FROM live.markets
                    WHERE market_id = $1
                """
                existing = await self.db.fetchval(query, market.market_id)

                if existing:
                    # Update existing market
                    update_query = """
                        UPDATE live.markets
                        SET yes_price = $2,
                            no_price = $3,
                            volume_24h = $4,
                            liquidity = $5,
                            updated_at = $6
                        WHERE market_id = $1
                    """
                    await self.db.execute(
                        update_query,
                        market.market_id,
                        market.yes_price,
                        market.no_price,
                        market.volume_24h,
                        market.liquidity,
                        datetime.now(UTC)
                    )
                    updated_count += 1
                else:
                    # Insert new market
                    insert_query = """
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
                    """
                    await self.db.execute(
                        insert_query,
                        market.market_id,
                        market.slug,
                        market.question,
                        market.yes_price,
                        market.no_price,
                        market.volume_24h,
                        market.liquidity,
                        market.category,
                        "gamma_api",
                        datetime.now(UTC),
                        datetime.now(UTC)
                    )
                    stored_count += 1

                # Store price history if enabled
                if self.config.enable_price_history:
                    await self._store_price_history(market)

            except Exception as e:
                logger.error(f"Error storing market {market.market_id}: {e}")

        logger.info(f"Stored {stored_count} new markets, updated {updated_count} existing markets")

    async def _store_price_history(self, market: MarketData):
        """Store market price in the time-series hypertable"""
        try:
            query = """
                INSERT INTO live.market_prices
                (time, market_id, yes_price, no_price, volume, liquidity)
                VALUES ($1, $2, $3, $4, $5, $6)
            """
            await self.db.execute(
                query,
                datetime.now(UTC),
                market.market_id,
                market.yes_price,
                market.no_price,
                market.volume_24h,
                market.liquidity
            )
        except Exception as e:
            logger.error(f"Error storing price history for {market.market_id}: {e}")

    async def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get statistics about the ingestion service"""
        try:
            # Total markets
            total_markets = await self.db.fetchval(
                "SELECT COUNT(*) FROM live.markets"
            )

            # Markets by category
            category_query = """
                SELECT category, COUNT(*) as count
                FROM live.markets
                GROUP BY category
                ORDER BY count DESC
            """
            category_stats = await self.db.fetch(category_query)

            # Latest update time
            latest_update = await self.db.fetchval(
                "SELECT MAX(updated_at) FROM live.markets"
            )

            return {
                "total_markets": total_markets or 0,
                "category_breakdown": [
                    {"category": row["category"], "count": row["count"]}
                    for row in category_stats
                ],
                "latest_update": latest_update.isoformat() if latest_update else None,
                "service_running": self._running
            }
        except Exception as e:
            logger.error(f"Error fetching ingestion stats: {e}")
            return {
                "total_markets": 0,
                "category_breakdown": [],
                "latest_update": None,
                "service_running": self._running,
                "error": str(e)
            }


# Singleton instance
_ingestion_service: Optional[IngestionService] = None


async def get_ingestion_service(
    db: DatabaseConnection,
    gamma_client: Optional[GammaClient] = None
) -> IngestionService:
    """Get or create singleton ingestion service"""
    global _ingestion_service
    if _ingestion_service is None:
        if gamma_client is None:
            gamma_client = await get_gamma_client()
        _ingestion_service = IngestionService(db, gamma_client)
    return _ingestion_service
