"""
Gamma API Client for Polymarket Analytics Platform.

Fetches market data from Polymarket's Gamma API (public, no authentication).
Uses official polymarket-client SDK when available.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, UTC
from dataclasses import dataclass

try:
    from polymarket_client import AsyncPublicClient
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Normalized market data structure"""
    market_id: str
    slug: str
    question: str
    yes_price: float
    no_price: float
    volume_24h: float
    liquidity: float
    category: str
    end_date: Optional[datetime] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(UTC)


class GammaClient:
    """
    Client for Polymarket Gamma API.

    Uses official SDK when available, falls back to custom HTTP client.
    """

    def __init__(self, base_url: str = "https://gamma-api.polymarket.com"):
        self.base_url = base_url
        self._client = None
        self._session = None

    async def _get_client(self):
        """Get or create API client"""
        if SDK_AVAILABLE:
            if self._client is None:
                self._client = AsyncPublicClient()
            return self._client
        else:
            if self._session is None:
                self._session = aiohttp.ClientSession()
            return self._session

    async def fetch_markets(
        self,
        active: bool = True,
        limit: int = 100,
        offset: int = 0,
        tags: Optional[List[str]] = None
    ) -> List[MarketData]:
        """
        Fetch markets from Gamma API.

        Args:
            active: Filter for active/inactive markets
            limit: Maximum number of markets to return
            offset: Pagination offset
            tags: Filter by tags/categories

        Returns:
            List of normalized MarketData objects
        """
        try:
            if SDK_AVAILABLE:
                return await self._fetch_with_sdk(active, limit, offset, tags)
            else:
                return await self._fetch_with_http(active, limit, offset, tags)

        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []

    async def _fetch_with_sdk(
        self,
        active: bool,
        limit: int,
        offset: int,
        tags: Optional[List[str]]
    ) -> List[MarketData]:
        """Fetch markets using official SDK"""
        client = await self._get_client()

        try:
            # Build query parameters
            params = {"active": active, "limit": limit}
            if offset:
                params["offset"] = offset
            if tags:
                params["tag_slug"] = tags

            # Fetch from Gamma API
            response = await client.fetch_markets(**params)

            # Normalize response
            markets = []
            for item in response:
                try:
                    market = self._normalize_market(item)
                    markets.append(market)
                except Exception as e:
                    logger.warning(f"Failed to normalize market {item.get('marketId')}: {e}")
                    continue

            logger.info(f"Fetched {len(markets)} markets via SDK")
            return markets

        except Exception as e:
            logger.error(f"SDK fetch failed: {e}")
            return []

    async def _fetch_with_http(
        self,
        active: bool,
        limit: int,
        offset: int,
        tags: Optional[List[str]]
    ) -> List[MarketData]:
        """Fetch markets using HTTP client (fallback)"""
        session = await self._get_client()

        # Build query parameters
        params = {"active": str(active).lower(), "limit": str(limit)}
        if offset:
            params["offset"] = str(offset)
        if tags:
            params["tag_slug"] = ",".join(tags)

        try:
            async with session.get(
                f"{self.base_url}/markets",
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                data = await response.json()

                # Normalize response
                markets = []
                for item in data:
                    try:
                        market = self._normalize_market(item)
                        markets.append(market)
                    except Exception as e:
                        logger.warning(f"Failed to normalize market {item.get('marketId')}: {e}")
                        continue

                logger.info(f"Fetched {len(markets)} markets via HTTP")
                return markets

        except aiohttp.ClientError as e:
            logger.error(f"HTTP fetch failed: {e}")
            return []

    def _normalize_market(self, item: Dict[str, Any]) -> MarketData:
        """Normalize API response to MarketData"""
        return MarketData(
            market_id=item.get("marketId", item.get("id", "")),
            slug=item.get("slug", ""),
            question=item.get("question", ""),
            yes_price=float(item.get("yesTokenPrice", item.get("yesPrice", 0))),
            no_price=float(item.get("noTokenPrice", item.get("noPrice", 0))),
            volume_24h=float(item.get("volume24h", 0)),
            liquidity=float(item.get("totalLiquidity", item.get("liquidity", 0))),
            category=self._infer_category(item),
            end_date=self._parse_end_date(item),
            created_at=datetime.now(UTC)
        )

    def _infer_category(self, item: Dict[str, Any]) -> str:
        """Infer category from market data"""
        slug = item.get("slug", "").lower()
        question = item.get("question", "").lower()
        description = item.get("description", "").lower()
        tags = item.get("tags", [])

        # Check tags first
        if tags:
            tag_str = str(tags).lower()
            if any(t in tag_str for t in ["politics", "election"]):
                return "Politics"
            elif any(t in tag_str for t in ["sports", "game"]):
                return "Sports"
            elif any(t in tag_str for t in ["crypto", "bitcoin", "eth"]):
                return "Crypto"

        # Check slug, question, description
        combined = f"{slug} {question} {description}"

        if any(t in combined for t in ["election", "politic", "vote", "congress", "senate", "house"]):
            return "Politics"
        elif any(t in combined for t in ["sport", "game", "team", "win", "match", "player"]):
            return "Sports"
        elif any(t in combined for t in ["btc", "eth", "crypto", "bitcoin", "solana", "blockchain"]):
            return "Crypto"
        elif any(t in combined for t in ["movie", "culture", "entertainment", "music", "celebrity"]):
            return "Culture"

        return "Other"

    def _parse_end_date(self, item: Dict[str, Any]) -> Optional[datetime]:
        """Parse end date from market data"""
        end_date = item.get("end_date")
        if end_date:
            try:
                if isinstance(end_date, str):
                    return datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                elif isinstance(end_date, int):
                    return datetime.fromtimestamp(end_date, UTC)
            except Exception as e:
                logger.warning(f"Failed to parse end date: {e}")
        return None

    async def fetch_single_market(self, market_id: str) -> Optional[MarketData]:
        """Fetch a single market by ID"""
        try:
            if SDK_AVAILABLE:
                client = await self._get_client()
                response = await client.fetch_market(market_id)
                if response:
                    return self._normalize_market(response)
            else:
                session = await self._get_client()
                async with session.get(
                    f"{self.base_url}/markets/{market_id}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._normalize_market(data)

        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")

        return None

    async def close(self):
        """Close client connections"""
        if self._client:
            # SDK client doesn't need explicit closing
            self._client = None
        if self._session:
            await self._session.close()
            self._session = None

        logger.info("Gamma client closed")


# Singleton instance
_gamma_client: Optional[GammaClient] = None


async def get_gamma_client() -> GammaClient:
    """Get or create singleton Gamma client"""
    global _gamma_client
    if _gamma_client is None:
        _gamma_client = GammaClient()
    return _gamma_client
