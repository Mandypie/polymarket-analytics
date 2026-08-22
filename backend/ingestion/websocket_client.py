"""
WebSocket Client for Polymarket Analytics Platform.

Handles real-time market data streaming from Polymarket WebSocket API.
Subscribes to market updates and dispatches to callbacks.
"""

import asyncio
import json
import logging
from typing import Callable, Dict, Set, Optional, Any
from datetime import datetime, UTC

try:
    import websockets
except ImportError:
    websockets = None
    logging.warning("websockets library not installed - WebSocket features disabled")

logger = logging.getLogger(__name__)


class PolymarketWebSocket:
    """
    WebSocket client for Polymarket real-time data.

    Connects to Polymarket WebSocket API for live market updates,
    order book changes, and trade notifications.
    """

    def __init__(
        self,
        url: str = "wss://api.polymarket.us/v1/ws/markets",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ):
        self.url = url
        self.api_key = api_key
        self.api_secret = api_secret
        self._websocket = None
        self._subscriptions: Dict[str, Set[Callable]] = {}
        self._running = False
        self._reconnect_delay = 5  # seconds
        self._max_reconnect_attempts = 10

    async def connect(self):
        """Connect to WebSocket server with automatic reconnection"""
        if websockets is None:
            logger.error("websockets library not installed")
            return False

        reconnect_count = 0

        while not self._running and reconnect_count < self._max_reconnect_attempts:
            try:
                logger.info(f"Connecting to WebSocket: {self.url}")

                # Build headers if authentication is provided
                extra_headers = {}
                if self.api_key:
                    timestamp = str(int(datetime.now(UTC).timestamp() * 1000))
                    extra_headers["X-PM-Access-Key"] = self.api_key
                    extra_headers["X-PM-Timestamp"] = timestamp
                    # Note: Signature would be calculated here if using authenticated endpoints

                self._websocket = await websockets.connect(
                    self.url,
                    extra_headers=extra_headers
                )

                self._running = True
                logger.info("WebSocket connected successfully")

                # Start message handler
                asyncio.create_task(self._message_handler())

                # Resubscribe to all subscriptions after reconnect
                await self._resubscribe_all()

                return True

            except Exception as e:
                logger.error(f"WebSocket connection failed (attempt {reconnect_count + 1}): {e}")
                reconnect_count += 1
                if reconnect_count < self._max_reconnect_attempts:
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, 60)  # Exponential backoff, max 60s

        logger.error("Max reconnection attempts reached")
        return False

    async def disconnect(self):
        """Disconnect from WebSocket server"""
        self._running = False
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
            logger.info("WebSocket disconnected")

    async def _message_handler(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self._websocket:
                try:
                    data = json.loads(message)
                    await self._dispatch_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed, attempting to reconnect...")
            self._running = False
            await self.connect()

    async def _dispatch_message(self, data: Dict[str, Any]):
        """Dispatch message to appropriate subscribers"""
        msg_type = data.get("type", data.get("message_type", ""))

        # Market data message
        if msg_type in ["market_update", "price_update", "book_update"]:
            market_id = data.get("market_id", data.get("token_id", ""))
            if market_id and market_id in self._subscriptions:
                for callback in self._subscriptions[market_id]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                    except Exception as e:
                        logger.error(f"Error in subscriber callback for {market_id}: {e}")

        # Global message (broadcast to all subscribers)
        elif msg_type in ["heartbeat", "system"]:
            # Handle system messages
            if msg_type == "heartbeat":
                logger.debug("WebSocket heartbeat received")

    async def subscribe_to_market(
        self,
        market_id: str,
        callback: Callable,
        subscription_type: int = 1
    ):
        """
        Subscribe to updates for a specific market.

        Args:
            market_id: Market/token identifier
            callback: Function to call with updates
            subscription_type: 1=full orderbook, 2=lightweight price data, 3=trades
        """
        if market_id not in self._subscriptions:
            self._subscriptions[market_id] = set()

        self._subscriptions[market_id].add(callback)

        # Send subscription message to server
        if self._websocket and self._running:
            try:
                subscribe_msg = {
                    "type": "subscribe",
                    "request_id": f"sub_{market_id}_{len(self._subscriptions[market_id])}",
                    "subscription_type": subscription_type,
                    "market_slugs": [market_id] if not market_id.startswith("0x") else []
                }
                await self._websocket.send(json.dumps(subscribe_msg))
                logger.info(f"Subscribed to market: {market_id} (type {subscription_type})")
            except Exception as e:
                logger.error(f"Failed to send subscription for {market_id}: {e}")

    async def unsubscribe_from_market(self, market_id: str, callback: Optional[Callable] = None):
        """Unsubscribe from market updates"""
        if market_id in self._subscriptions:
            if callback:
                self._subscriptions[market_id].discard(callback)
            else:
                # Remove all subscribers for this market
                self._subscriptions[market_id].clear()

            # If no subscribers left, send unsubscribe message
            if not self._subscriptions[market_id]:
                del self._subscriptions[market_id]
                if self._websocket and self._running:
                    try:
                        unsubscribe_msg = {
                            "type": "unsubscribe",
                            "market_slugs": [market_id]
                        }
                        await self._websocket.send(json.dumps(unsubscribe_msg))
                        logger.info(f"Unsubscribed from market: {market_id}")
                    except Exception as e:
                        logger.error(f"Failed to send unsubscribe for {market_id}: {e}")

    async def unsubscribe_all(self):
        """Unsubscribe from all markets"""
        for market_id in list(self._subscriptions.keys()):
            await self.unsubscribe_from_market(market_id)

    async def _resubscribe_all(self):
        """Resubscribe to all markets after reconnection"""
        for market_id in list(self._subscriptions.keys()):
            # Re-add subscriptions (subscribers will be notified)
            callbacks = self._subscriptions[market_id].copy()
            self._subscriptions[market_id].clear()
            for callback in callbacks:
                await self.subscribe_to_market(market_id, callback)

    def get_subscriptions(self) -> Set[str]:
        """Get list of currently subscribed markets"""
        return set(self._subscriptions.keys())

    def get_subscription_count(self) -> int:
        """Get total number of active subscriptions"""
        return sum(len(callbacks) for callbacks in self._subscriptions.values())

    async def send_ping(self):
        """Send ping message to keep connection alive"""
        if self._websocket and self._running:
            try:
                ping_msg = {"type": "ping", "timestamp": int(datetime.now(UTC).timestamp() * 1000)}
                await self._websocket.send(json.dumps(ping_msg))
            except Exception as e:
                logger.error(f"Failed to send ping: {e}")

    async def close(self):
        """Close WebSocket connection and cleanup"""
        await self.disconnect()
        self._subscriptions.clear()


# Singleton instance
_websocket_client: Optional[PolymarketWebSocket] = None


async def get_websocket_client(
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None
) -> PolymarketWebSocket:
    """Get or create singleton WebSocket client"""
    global _websocket_client
    if _websocket_client is None:
        _websocket_client = PolymarketWebSocket(url or "wss://api.polymarket.us/v1/ws/markets")
    return _websocket_client
