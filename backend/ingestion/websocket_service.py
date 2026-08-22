"""
WebSocket Service for Real-time Market Data

Provides real-time streaming of Polymarket data to connected clients.
Manages WebSocket connections, subscriptions, and message broadcasting.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Callable, Any
from datetime import datetime
from fastapi import WebSocket
from collections import defaultdict

from .websocket_client import get_websocket_client
from backend.analytics.edge_calculator import get_edge_calculator

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket client connections"""

    def __init__(self):
        # active_connections: {market_id: set of WebSockets}
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        # all_connections: all connected WebSockets
        self.all_connections: Set[WebSocket] = set()
        # client_subscriptions: {WebSocket: set of market_ids}
        self.client_subscriptions: Dict[WebSocket, Set[str]] = defaultdict(set)

    async def connect(self, websocket: WebSocket) -> str:
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.all_connections.add(websocket)
        client_id = f"client_{id(websocket)}"
        logger.info(f"Client connected: {client_id}")
        return client_id

    async def disconnect(self, websocket: WebSocket) -> None:
        """Disconnect a WebSocket client"""
        client_id = f"client_{id(websocket)}"

        # Remove from all market subscriptions
        for market_id in self.client_subscriptions.get(websocket, set()):
            self.active_connections[market_id].discard(websocket)

        # Remove from tracking
        self.all_connections.discard(websocket)
        if websocket in self.client_subscriptions:
            del self.client_subscriptions[websocket]

        logger.info(f"Client disconnected: {client_id}")

    async def subscribe_to_market(self, websocket: WebSocket, market_id: str) -> None:
        """Subscribe a client to a specific market"""
        self.active_connections[market_id].add(websocket)
        self.client_subscriptions[websocket].add(market_id)
        logger.info(f"Client subscribed to market: {market_id}")

    async def unsubscribe_from_market(self, websocket: WebSocket, market_id: str) -> None:
        """Unsubscribe a client from a specific market"""
        self.active_connections[market_id].discard(websocket)
        self.client_subscriptions[websocket].discard(market_id)
        logger.info(f"Client unsubscribed from market: {market_id}")

    async def broadcast_to_market(self, market_id: str, message: Dict[str, Any]) -> None:
        """Broadcast a message to all subscribers of a market"""
        if market_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[market_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)

    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients"""
        disconnected = set()
        for connection in self.all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.all_connections)

    def get_market_subscribers(self, market_id: str) -> int:
        """Get number of subscribers for a specific market"""
        return len(self.active_connections.get(market_id, set()))


class WebSocketService:
    """Main WebSocket service for real-time market data"""

    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.ws_client = None
        self.edge_calculator = None
        self._running = False
        self._message_handlers = {}

    async def start(self) -> None:
        """Start the WebSocket service"""
        if self._running:
            return

        logger.info("Starting WebSocket service...")

        # Initialize clients
        self.ws_client = await get_websocket_client()
        self.edge_calculator = await get_edge_calculator()

        # Connect to Polymarket WebSocket
        if await self.ws_client.connect():
            self._running = True

            # Start message processing loop
            asyncio.create_task(self._message_loop())

            logger.info("WebSocket service started")
        else:
            logger.error("Failed to connect to Polymarket WebSocket")

    async def stop(self) -> None:
        """Stop the WebSocket service"""
        if not self._running:
            return

        logger.info("Stopping WebSocket service...")
        self._running = False

        if self.ws_client:
            await self.ws_client.disconnect()

        logger.info("WebSocket service stopped")

    async def _message_loop(self) -> None:
        """Process incoming WebSocket messages"""
        while self._running:
            try:
                # Process messages from Polymarket WebSocket
                if self.ws_client and self.ws_client._connected:
                    # Messages are handled via callbacks registered in ws_client
                    pass

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                await asyncio.sleep(1)

    async def handle_client_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle incoming message from a client"""
        msg_type = message.get("type")
        data = message.get("data", {})

        if msg_type == "subscribe":
            market_id = data.get("market_id")
            if market_id:
                await self.manager.subscribe_to_market(websocket, market_id)

                # Subscribe to Polymarket WebSocket if available
                if self.ws_client:
                    await self.ws_client.subscribe_to_market(
                        market_id,
                        self._on_market_update,
                        "price"
                    )

                await websocket.send_json({
                    "type": "subscription_success",
                    "market_id": market_id,
                    "timestamp": datetime.now().isoformat()
                })

        elif msg_type == "unsubscribe":
            market_id = data.get("market_id")
            if market_id:
                await self.manager.unsubscribe_from_market(websocket, market_id)
                await websocket.send_json({
                    "type": "unsubscription_success",
                    "market_id": market_id,
                    "timestamp": datetime.now().isoformat()
                })

        elif msg_type == "ping":
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })

        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            })

    async def _on_market_update(self, market_id: str, data: Dict[str, Any]) -> None:
        """Callback for market updates from Polymarket WebSocket"""
        # Calculate edge if price data available
        if "price" in data:
            edge_data = await self._calculate_edge(market_id, data)
            data["edge"] = edge_data

        # Broadcast to subscribers
        message = {
            "type": "market_update",
            "market_id": market_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        await self.manager.broadcast_to_market(market_id, message)

    async def _calculate_edge(self, market_id: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate trading edge for a market"""
        if not self.edge_calculator:
            return {}

        try:
            yes_price = price_data.get("price")
            if yes_price is None:
                return {}

            # Calculate edge using the edge calculator
            edge = await self.edge_calculator.calculate_edge(
                market_id=market_id,
                current_price=yes_price,
                timestamp=datetime.now()
            )

            return {
                "value": edge.get("edge_value", 0),
                "confidence": edge.get("confidence", 0),
                "signal": edge.get("signal", "NEUTRAL"),
                "reasoning": edge.get("reasoning", "")
            }
        except Exception as e:
            logger.error(f"Error calculating edge: {e}")
            return {}

    async def broadcast_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Broadcast an alert to all connected clients"""
        message = {
            "type": "alert",
            "alert_type": alert_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        await self.manager.broadcast_to_all(message)

    async def broadcast_system_status(self, status: str) -> None:
        """Broadcast system status to all clients"""
        message = {
            "type": "system_status",
            "status": status,
            "connections": self.manager.get_connection_count(),
            "timestamp": datetime.now().isoformat()
        }

        await self.manager.broadcast_to_all(message)

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket service statistics"""
        return {
            "running": self._running,
            "connections": self.manager.get_connection_count(),
            "polymarket_connected": self.ws_client._connected if self.ws_client else False
        }


# Global service instance
_websocket_service: Optional[WebSocketService] = None
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the connection manager"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


async def get_websocket_service() -> WebSocketService:
    """Get or create the WebSocket service"""
    global _websocket_service
    if _websocket_service is None:
        manager = get_connection_manager()
        _websocket_service = WebSocketService(manager)
    return _websocket_service
