"""
Edge Calculator Module for Polymarket Analytics Platform.

Calculates the edge between model confidence and market-implied probability.
Ported from JavaScript implementation in src/engine/edgeCalculator.js
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio


class EdgeStrength(Enum):
    """Classification of edge strength"""
    STRONG = "STRONG"  # edge >= 0.05
    WEAK = "WEAK"      # edge >= 0.02
    NONE = "NONE"      # edge < 0.02


@dataclass
class EdgeResult:
    """Result of edge calculation"""
    edge: float           # Raw edge value (confidence - market_prob)
    edge_pct: float       # Edge as percentage (edge * 100)
    is_positive: bool     # True if edge > 0
    strength: EdgeStrength  # Classification of edge strength

    def __repr__(self):
        return f"EdgeResult(edge={self.edge:.4f}, strength={self.strength.value})"


def calculate_edge(
    confidence: float,
    market_prob: float
) -> Optional[EdgeResult]:
    """
    Calculate edge between model confidence and market probability.

    The edge represents the difference between what the model believes
    will happen (confidence) and what the market prices imply (market_prob).

    Args:
        confidence: Model's confidence level (0.0 to 1.0)
        market_prob: Market-implied probability (0.0 to 1.0)

    Returns:
        EdgeResult with edge, percentage, and strength classification
        Returns None if inputs are invalid

    Examples:
        >>> calculate_edge(0.8, 0.7)
        EdgeResult(edge=0.1, edge_pct=10.0, is_positive=True, strength=STRONG)

        >>> calculate_edge(0.6, 0.65)
        EdgeResult(edge=-0.05, edge_pct=-5.0, is_positive=False, strength=WEAK)
    """
    # Validate inputs
    if not isinstance(confidence, (int, float)) or not isinstance(market_prob, (int, float)):
        return None

    if not (0 <= confidence <= 1) or not (0 <= market_prob <= 1):
        return None

    # Calculate edge
    edge = confidence - market_prob
    edge_pct = round(edge * 100, 1)

    # Determine strength
    if edge >= 0.05:
        strength = EdgeStrength.STRONG
    elif edge >= 0.02:
        strength = EdgeStrength.WEAK
    else:
        strength = EdgeStrength.NONE

    return EdgeResult(
        edge=edge,
        edge_pct=edge_pct,
        is_positive=edge > 0,
        strength=strength
    )


def calculate_edge_from_prices(
    yes_price: float,
    no_price: float,
    model_confidence: float,
    model_direction: str
) -> Optional[EdgeResult]:
    """
    Calculate edge from market prices and model prediction.

    Args:
        yes_price: Market YES token price (0 to 1)
        no_price: Market NO token price (0 to 1)
        model_confidence: Model's confidence (0 to 1)
        model_direction: Model's predicted direction ("YES" or "NO")

    Returns:
        EdgeResult or None if invalid inputs
    """
    # Validate prices
    if not (0 <= yes_price <= 1) or not (0 <= no_price <= 1):
        return None

    # Determine market probability based on model direction
    if model_direction.upper() == "YES":
        market_prob = yes_price
    elif model_direction.upper() == "NO":
        market_prob = no_price
    else:
        return None

    return calculate_edge(model_confidence, market_prob)


def filter_by_edge(
    items: list[dict],
    confidence_key: str = "confidence",
    market_prob_key: str = "market_prob",
    min_edge: float = 0.02,
    only_positive: bool = True
) -> list[dict]:
    """
    Filter list of items by edge threshold.

    Args:
        items: List of dictionaries containing confidence and market_prob
        confidence_key: Key name for confidence value
        market_prob_key: Key name for market probability value
        min_edge: Minimum edge threshold
        only_positive: If True, only include items with positive edge

    Returns:
        Filtered list with edge calculation added to each item
    """
    filtered = []

    for item in items:
        confidence = item.get(confidence_key)
        market_prob = item.get(market_prob_key)

        if confidence is None or market_prob is None:
            continue

        edge_result = calculate_edge(confidence, market_prob)
        if edge_result is None:
            continue

        # Add edge calculation to item
        item_with_edge = item.copy()
        item_with_edge["edge"] = edge_result.edge
        item_with_edge["edge_pct"] = edge_result.edge_pct
        item_with_edge["edge_strength"] = edge_result.strength.value

        # Apply filters
        if abs(edge_result.edge) >= min_edge:
            if only_positive and edge_result.is_positive:
                filtered.append(item_with_edge)
            elif not only_positive:
                filtered.append(item_with_edge)

    return filtered


class EdgeCalculator:
    """Simple edge calculator for real-time WebSocket use"""

    def __init__(self):
        self._confidence_cache = {}  # Simple cache for model confidences

    async def calculate_edge(
        self,
        market_id: str,
        current_price: float,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Calculate edge for a market in real-time.

        For now, this returns a basic calculation. In production,
        this would integrate with the signal generator.
        """
        # Get cached confidence or use a default
        confidence = self._confidence_cache.get(market_id, 0.5)

        # Calculate edge
        edge_result = calculate_edge(confidence, current_price)

        if edge_result:
            return {
                "market_id": market_id,
                "edge": edge_result.edge,
                "edge_pct": edge_result.edge_pct,
                "strength": edge_result.strength.value,
                "timestamp": timestamp.isoformat()
            }

        return {}

    def set_confidence(self, market_id: str, confidence: float):
        """Set cached confidence for a market"""
        self._confidence_cache[market_id] = confidence


# Global edge calculator instance
_edge_calculator = None


async def get_edge_calculator() -> EdgeCalculator:
    """Get or create the global edge calculator instance"""
    global _edge_calculator
    if _edge_calculator is None:
        _edge_calculator = EdgeCalculator()
    return _edge_calculator


# Example usage and tests
if __name__ == "__main__":
    # Test cases
    print("Testing edge calculator:")

    # Strong positive edge
    result = calculate_edge(0.8, 0.7)
    print(f"Strong edge: {result}")

    # Weak positive edge
    result = calculate_edge(0.75, 0.72)
    print(f"Weak edge: {result}")

    # Negative edge (no edge)
    result = calculate_edge(0.6, 0.65)
    print(f"Negative edge: {result}")

    # Test filtering
    items = [
        {"id": 1, "confidence": 0.8, "market_prob": 0.7},
        {"id": 2, "confidence": 0.6, "market_prob": 0.65},
        {"id": 3, "confidence": 0.75, "market_prob": 0.72},
    ]

    filtered = filter_by_edge(items, min_edge=0.02, only_positive=True)
    print(f"\nFiltered items with positive edge: {[f['id'] for f in filtered]}")
