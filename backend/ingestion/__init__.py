"""
Data Ingestion Module for Polymarket Analytics Platform.

Provides async data ingestion from:
- Gamma API (market data)
- CLOB API (order book data)
- WebSocket (real-time updates)
"""

from .gamma_client import GammaClient, MarketData, get_gamma_client
from .clob_client import CLOBClient, OrderBook, OrderBookLevel, get_clob_client
from .websocket_client import PolymarketWebSocket, get_websocket_client
from .data_labeler import DataLabeler, DataSourceType, MarketCategory, get_data_labeler
from .ingestion_service import IngestionService, IngestionConfig, get_ingestion_service

__all__ = [
    "GammaClient",
    "MarketData",
    "get_gamma_client",
    "CLOBClient",
    "OrderBook",
    "OrderBookLevel",
    "get_clob_client",
    "PolymarketWebSocket",
    "get_websocket_client",
    "DataLabeler",
    "DataSourceType",
    "MarketCategory",
    "get_data_labeler",
    "IngestionService",
    "IngestionConfig",
    "get_ingestion_service"
]
