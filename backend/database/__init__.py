"""
Database Module for Polymarket Analytics Platform.

Provides connection management and repositories for:
- Live Markets
- Mock Data
- Resolved Historical Results
"""

from .connection import (
    DatabaseConfig,
    DatabaseConnection,
    get_db,
    close_db
)

from .repositories import (
    LiveMarketsRepository,
    MockMarketsRepository,
    ResolvedMarketsRepository,
    MarketPricesRepository,
    get_repositories
)

__all__ = [
    "DatabaseConfig",
    "DatabaseConnection",
    "get_db",
    "close_db",
    "LiveMarketsRepository",
    "MockMarketsRepository",
    "ResolvedMarketsRepository",
    "MarketPricesRepository",
    "get_repositories"
]
