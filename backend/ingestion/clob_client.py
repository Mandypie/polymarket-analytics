"""
CLOB API Client for Polymarket Analytics Platform.

Fetches order book data from Polymarket CLOB API (public endpoints).
Provides order book depth, spread analysis, and liquidity metrics.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, UTC
from dataclasses import dataclass

try:
    import aiohttp
except ImportError:
    import requests as aiohttp_lib
    aiohttp = None

logger = logging.getLogger(__name__)


@dataclass
class OrderBookLevel:
    """Single order book level (price, size)"""
    price: float
    size: float
    orders: int = 1

    def __repr__(self):
        return f"OrderBookLevel(price={self.price:.4f}, size={self.size:.2f})"


@dataclass
class OrderBook:
    """Complete order book for a market"""
    market_id: str
    token_id: str
    bids: List[OrderBookLevel]  # Buy orders (descending price)
    asks: List[OrderBookLevel]  # Sell orders (ascending price)
    timestamp: datetime
    sequence: Optional[int] = None
    min_order_size: float = 0.0
    tick_size: float = 0.01

    def get_best_bid(self) -> Optional[OrderBookLevel]:
        """Get highest bid (buy order)"""
        return self.bids[0] if self.bids else None

    def get_best_ask(self) -> Optional[OrderBookLevel]:
        """Get lowest ask (sell order)"""
        return self.asks[0] if self.asks else None

    def get_spread(self) -> Optional[float]:
        """Get bid-ask spread"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid and best_ask:
            return best_ask.price - best_bid.price
        return None

    def get_spread_pct(self) -> Optional[float]:
        """Get spread as percentage of mid price"""
        spread = self.get_spread()
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        if spread and best_bid and best_ask:
            mid_price = (best_bid.price + best_ask.price) / 2
            return (spread / mid_price) * 100 if mid_price > 0 else None
        return None

    def get_total_liquidity(self) -> Dict[str, float]:
        """Get total liquidity on both sides"""
        bid_liquidity = sum(level.size for level in self.bids)
        ask_liquidity = sum(level.size for level in self.asks)
        return {
            "total_bids": bid_liquidity,
            "total_asks": ask_liquidity,
            "total": bid_liquidity + ask_liquidity
        }

    def get_depth_at_price(self, target_price: float, side: str) -> float:
        """Get cumulative depth up to a target price"""
        if side == "bid":
            cumulative = sum(
                level.size for level in self.bids
                if level.price >= target_price
            )
        else:  # ask
            cumulative = sum(
                level.size for level in self.asks
                if level.price <= target_price
            )
        return cumulative


class CLOBClient:
    """
    Client for Polymarket CLOB API.

    Fetches order book data, market depth, and liquidity metrics.
    Uses public endpoints (no authentication required for market data).
    """

    def __init__(self, base_url: str = "https://clob.polymarket.com"):
        self.base_url = base_url
        self._session = None

    async def _get_session(self):
        """Get or create aiohttp session"""
        if self._session is None:
            if aiohttp:
                self._session = aiohttp.ClientSession()
            else:
                raise ImportError("aiohttp is required for CLOB client")
        return self._session

    async def fetch_order_book(
        self,
        token_id: str,
        limit: int = 20
    ) -> Optional[OrderBook]:
        """
        Fetch order book for a specific token.

        Args:
            token_id: Polymarket token ID
            limit: Number of price levels to return

        Returns:
            OrderBook object with bids and asks
        """
        try:
            session = await self._get_session()

            async with session.get(
                f"{self.base_url}/book",
                params={"tokenID": token_id, "limit": str(limit)},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                data = await response.json()

                return self._parse_order_book(data, token_id)

        except Exception as e:
            logger.error(f"Error fetching order book for {token_id}: {e}")
            return None

    async def fetch_market_price(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current market price for a token.

        Args:
            token_id: Polymarket token ID

        Returns:
            Dict with price information
        """
        try:
            session = await self._get_session()

            async with session.get(
                f"{self.base_url}/price",
                params={"tokenID": token_id},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                data = await response.json()

                return {
                    "token_id": token_id,
                    "price": float(data.get("price", 0)),
                    "timestamp": datetime.now(UTC)
                }

        except Exception as e:
            logger.error(f"Error fetching price for {token_id}: {e}")
            return None

    async def fetch_midpoint(self, token_id: str) -> Optional[float]:
        """
        Fetch mid-point price (average of best bid and ask).

        Args:
            token_id: Polymarket token ID

        Returns:
            Mid-point price as float
        """
        try:
            session = await self._get_session()

            async with session.get(
                f"{self.base_url}/midpoint",
                params={"tokenID": token_id},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return float(data.get("midpoint", 0))

        except Exception as e:
            logger.error(f"Error fetching midpoint for {token_id}: {e}")
            return None

    async def fetch_spread(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current spread for a token.

        Args:
            token_id: Polymarket token ID

        Returns:
            Dict with spread information
        """
        try:
            session = await self._get_session()

            async with session.get(
                f"{self.base_url}/spread",
                params={"tokenID": token_id},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                data = await response.json()

                return {
                    "token_id": token_id,
                    "spread": float(data.get("spread", 0)),
                    "spread_pct": float(data.get("spread_pct", 0)),
                    "timestamp": datetime.now(UTC)
                }

        except Exception as e:
            logger.error(f"Error fetching spread for {token_id}: {e}")
            return None

    def _parse_order_book(self, data: Dict[str, Any], token_id: str) -> OrderBook:
        """Parse CLOB API response into OrderBook object"""
        # Parse bids (buy orders) - sorted descending by price
        bids = []
        for bid_data in data.get("bids", []):
            try:
                level = OrderBookLevel(
                    price=float(bid_data.get("price", 0)),
                    size=float(bid_data.get("size", 0)),
                    orders=int(bid_data.get("orders", 1))
                )
                bids.append(level)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse bid level: {e}")
                continue

        # Sort bids descending (highest first)
        bids.sort(key=lambda x: x.price, reverse=True)

        # Parse asks (sell orders) - sorted ascending by price
        asks = []
        for ask_data in data.get("asks", []):
            try:
                level = OrderBookLevel(
                    price=float(ask_data.get("price", 0)),
                    size=float(ask_data.get("size", 0)),
                    orders=int(ask_data.get("orders", 1))
                )
                asks.append(level)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse ask level: {e}")
                continue

        # Sort asks ascending (lowest first)
        asks.sort(key=lambda x: x.price)

        return OrderBook(
            market_id=data.get("conditionId", token_id),
            token_id=token_id,
            bids=bids,
            asks=asks,
            timestamp=datetime.now(UTC),
            sequence=int(data.get("sequence", 0)),
            min_order_size=float(data.get("minOrderSize", 0)),
            tick_size=float(data.get("tickSize", 0.01))
        )

    async def fetch_multiple_order_books(
        self,
        token_ids: List[str],
        limit: int = 10
    ) -> Dict[str, OrderBook]:
        """
        Fetch order books for multiple tokens concurrently.

        Args:
            token_ids: List of token IDs
            limit: Number of price levels per book

        Returns:
            Dict mapping token_id to OrderBook
        """
        tasks = [
            self.fetch_order_book(token_id, limit)
            for token_id in token_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        order_books = {}
        for token_id, result in zip(token_ids, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch order book for {token_id}: {result}")
            elif result is not None:
                order_books[token_id] = result

        return order_books

    async def close(self):
        """Close client connection"""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("CLOB client closed")


# Singleton instance
_clob_client: Optional[CLOBClient] = None


async def get_clob_client() -> CLOBClient:
    """Get or create singleton CLOB client"""
    global _clob_client
    if _clob_client is None:
        _clob_client = CLOBClient()
    return _clob_client
