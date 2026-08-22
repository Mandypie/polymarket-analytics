"""
Data Labeler Module for Polymarket Analytics Platform.

Automatically categorizes and labels incoming data into:
- Live Data: Real-time markets from Gamma API
- Mock Data: Simulated data for backtesting
- Resolved Historical Results: Settled markets
"""

import logging
from typing import Dict, Any, Optional, Literal
from datetime import datetime, UTC
from enum import Enum

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Classification of data sources"""
    LIVE = "live"           # Real-time market data
    MOCK = "mock"           # Simulated/backtesting data
    RESOLVED = "resolved"   # Historical settled markets


class MarketCategory(Enum):
    """Polymarket market categories"""
    POLITICS = "Politics"
    SPORTS = "Sports"
    CRYPTO = "Crypto"
    CULTURE = "Culture"
    ECONOMICS = "Economics"
    WORLD_EVENTS = "World Events"
    OTHER = "Other"


class DataLabeler:
    """
    Automatically labels and categorizes incoming market data.

    Determines:
    - Data source type (live/mock/resolved)
    - Market category
    - Data quality flags
    """

    def __init__(self):
        self._category_keywords = self._build_category_keywords()

    def _build_category_keywords(self) -> Dict[str, list[str]]:
        """Build keyword lists for category classification"""
        return {
            "Politics": [
                "election", "politic", "vote", "congress", "senate", "house",
                "president", "trump", "biden", "democrat", "republican",
                "gop", "primary", "caucus", "ballot", "campaign"
            ],
            "Sports": [
                "sport", "game", "team", "win", "match", "player", "coach",
                "super bowl", "nba", "nfl", "mlb", "nhl", "world cup",
                "olympics", "championship", "league", "tournament", "finals"
            ],
            "Crypto": [
                "btc", "eth", "crypto", "bitcoin", "ethereum", "solana",
                "blockchain", "defi", "nft", "altcoin", "hodl", "whale",
                "bull run", "bear market", "satoshi", "vitalik"
            ],
            "Culture": [
                "movie", "film", "oscar", "emmy", "grammy", "music",
                "celebrity", "entertainment", "tv", "series", "netflix",
                "album", "artist", "concert", "festival", "awards"
            ],
            "Economics": [
                "inflation", "recession", "gdp", "unemployment", "fed",
                "interest rate", "economy", "stock market", "bond", "treasury",
                "econ", "monetary", "fiscal", "stimulus", "data"
            ],
            "World Events": [
                "war", "conflict", "election", "referendum", "brexit",
                "climate", "disaster", "pandemic", "protest", "revolution",
                "geopolitic", "treaty", "summit", "meeting"
            ]
        }

    def label_market_data(
        self,
        market_data: Dict[str, Any],
        source_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Label and categorize incoming market data.

        Args:
            market_data: Raw market data from any source
            source_hint: Optional hint about data source ('gamma', 'mock', 'resolved')

        Returns:
            Labeled data with source type, category, and quality flags
        """
        labeled_data = market_data.copy()

        # Determine data source type
        source_type = self._classify_source_type(market_data, source_hint)
        labeled_data["data_source"] = source_type.value

        # Categorize market
        category = self._categorize_market(market_data)
        labeled_data["category"] = category.value

        # Add quality flags
        labeled_data["quality_flags"] = self._assess_data_quality(market_data)

        # Add timestamp
        labeled_data["labeled_at"] = datetime.now(UTC).isoformat()

        return labeled_data

    def _classify_source_type(
        self,
        market_data: Dict[str, Any],
        source_hint: Optional[str]
    ) -> DataSourceType:
        """Classify data source type"""

        # Explicit source hint
        if source_hint:
            if source_hint.lower() == "mock":
                return DataSourceType.MOCK
            elif source_hint.lower() == "resolved":
                return DataSourceType.RESOLVED
            elif source_hint.lower() == "gamma":
                return DataSourceType.LIVE

        # Check for resolved market indicators
        if self._is_resolved_market(market_data):
            return DataSourceType.RESOLVED

        # Check for mock data indicators
        if self._is_mock_data(market_data):
            return DataSourceType.MOCK

        # Default to live
        return DataSourceType.LIVE

    def _is_resolved_market(self, market_data: Dict[str, Any]) -> bool:
        """Check if market is resolved"""
        resolved_indicators = [
            "resolved_at", "resolution_price", "winning_outcome",
            "outcome", "settled", "closed"
        ]

        return any(
            indicator in market_data and market_data[indicator] is not None
            for indicator in resolved_indicators
        )

    def _is_mock_data(self, market_data: Dict[str, Any]) -> bool:
        """Check if data is mock/simulated"""
        mock_indicators = [
            "scenario_id", "simulation", "mock", "test",
            "backtest", "hypothetical"
        ]

        return any(
            indicator in str(market_data).lower()
            for indicator in mock_indicators
        )

    def _categorize_market(self, market_data: Dict[str, Any]) -> MarketCategory:
        """Categorize market into predefined categories"""

        # Get searchable text from market data
        searchable_text = self._get_searchable_text(market_data).lower()

        # Check against category keywords
        category_scores = {}
        for category, keywords in self._category_keywords.items():
            score = sum(
                1 for keyword in keywords
                if keyword.lower() in searchable_text
            )
            if score > 0:
                category_scores[category] = score

        # Return category with highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return MarketCategory(best_category)

        # Check explicit category field
        if "category" in market_data:
            explicit_category = market_data["category"]
            try:
                return MarketCategory(explicit_category.title())
            except ValueError:
                pass

        # Default to Other
        return MarketCategory.OTHER

    def _get_searchable_text(self, market_data: Dict[str, Any]) -> str:
        """Extract searchable text from market data"""
        fields = [
            "question", "description", "slug", "tags",
            "category", "title", "name"
        ]

        text_parts = []
        for field in fields:
            value = market_data.get(field)
            if value:
                if isinstance(value, list):
                    text_parts.extend(str(v) for v in value)
                else:
                    text_parts.append(str(value))

        return " ".join(text_parts)

    def _assess_data_quality(self, market_data: Dict[str, Any]) -> Dict[str, bool]:
        """Assess quality of market data"""
        flags = {
            "has_question": bool(market_data.get("question")),
            "has_prices": bool(
                market_data.get("yes_price") is not None and
                market_data.get("no_price") is not None
            ),
            "valid_prices": self._validate_prices(market_data),
            "has_liquidity": bool(market_data.get("liquidity") and market_data["liquidity"] > 0),
            "has_volume": bool(market_data.get("volume_24h") and market_data["volume_24h"] > 0),
            "has_end_date": bool(market_data.get("end_date") or market_data.get("resolved_at")),
            "is_complete": False
        }

        # Data is complete if all flags are True
        flags["is_complete"] = all(flags.values())

        return flags

    def _validate_prices(self, market_data: Dict[str, Any]) -> bool:
        """Validate YES/NO prices"""
        yes_price = market_data.get("yes_price")
        no_price = market_data.get("no_price")

        if yes_price is None or no_price is None:
            return False

        try:
            yes_float = float(yes_price)
            no_float = float(no_price)

            # Prices should be between 0 and 1
            if not (0 <= yes_float <= 1) or not (0 <= no_float <= 1):
                return False

            # Prices should sum close to 1 (allowing for small spread)
            spread = abs(1 - (yes_float + no_float))
            return spread <= 0.05  # 5% tolerance

        except (ValueError, TypeError):
            return False

    def get_labeling_stats(self) -> Dict[str, Any]:
        """Get statistics about labeling operations"""
        return {
            "supported_categories": [cat.value for cat in MarketCategory],
            "supported_sources": [src.value for src in DataSourceType],
            "category_keywords_count": {
                cat: len(kw) for cat, kw in self._category_keywords.items()
            }
        }


# Singleton instance
_data_labeler: Optional[DataLabeler] = None


def get_data_labeler() -> DataLabeler:
    """Get or create singleton data labeler"""
    global _data_labeler
    if _data_labeler is None:
        _data_labeler = DataLabeler()
    return _data_labeler
