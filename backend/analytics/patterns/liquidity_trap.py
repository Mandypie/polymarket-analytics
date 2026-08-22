"""
Liquidity Trap Detector

Detects whale-scale liquidity accumulation/distribution patterns.
Identifies when large players are positioning for moves.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from .base_detector import BaseDetector, PatternResult, PatternType, PatternStrength

logger = logging.getLogger(__name__)


class LiquidityTrapDetector(BaseDetector):
    """
    Detects liquidity traps caused by whale positioning.

    Identifies patterns where large orders are accumulating
    at specific price levels, indicating potential whale activity.
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.LIQUIDITY_TRAP
        self.whale_threshold = 10000  # Minimum order size to be considered "whale"
        self.concentration_threshold = 0.3  # 30% of liquidity in one level = trap
        self.pattern_ttl_hours = 12  # Liquidity traps persist longer

    async def detect(
        self,
        market_data: Dict[str, Any],
        historical_data: List[Dict] = None
    ) -> PatternResult:
        """Detect liquidity trap pattern"""
        if not self._validate_market_data(market_data):
            return self._no_pattern_result(market_data.get("market_id", ""))

        market_id = market_data.get("market_id")
        current_price = market_data.get("yes_price", 0.5)
        liquidity = market_data.get("liquidity", 0)
        volume_24h = market_data.get("volume_24h", 0)

        # Get order book data if available
        order_book = market_data.get("order_book", {})
        if not order_book:
            return self._no_pattern_result(market_id)

        try:
            # Analyze order book for concentration
            trap_detected, direction, confidence, metadata = self._analyze_order_book(
                order_book, current_price, liquidity, volume_24h
            )

            if trap_detected:
                strength = self._calculate_strength(confidence, metadata.get("concentration_score", 0.5))

                return PatternResult(
                    pattern_type=self.pattern_type,
                    market_id=market_id,
                    detected=True,
                    confidence=confidence,
                    strength=strength,
                    direction=direction,
                    detected_at=datetime.now(),
                    expires_at=self._calculate_expiry(self.pattern_ttl_hours),
                    metadata=metadata
                )
            else:
                return self._no_pattern_result(market_id)

        except Exception as e:
            logger.error(f"Error detecting liquidity trap for {market_id}: {e}")
            return self._no_pattern_result(market_id)

    async def detect_batch(self, markets: List[Dict[str, Any]]) -> List[PatternResult]:
        """Detect liquidity traps across multiple markets"""
        results = []
        for market in markets:
            result = await self.detect(market)
            results.append(result)
        return results

    def _analyze_order_book(
        self,
        order_book: Dict,
        current_price: float,
        liquidity: float,
        volume_24h: float
    ) -> Tuple[bool, str, float, Dict]:
        """
        Analyze order book for liquidity concentration.

        Returns: (detected, direction, confidence, metadata)
        """
        bids = order_book.get("bids", [])
        asks = order_book.get("asks", [])

        if not bids or not asks:
            return False, "NEUTRAL", 0.0, {}

        # Analyze bid side (potential support trap)
        bid_concentration, bid_levels = self._calculate_concentration(bids, current_price)
        # Analyze ask side (potential resistance trap)
        ask_concentration, ask_levels = self._calculate_concentration(asks, current_price)

        # Determine trap type
        trap_detected = False
        direction = "NEUTRAL"
        confidence = 0.0
        metadata = {}

        # Support trap (whales buying at lower levels)
        if bid_concentration > self.concentration_threshold:
            whale_bid_value = self._calculate_whale_value(bids, bid_levels)
            if whale_bid_value > self.whale_threshold:
                trap_detected = True
                direction = "LONG"
                confidence = min(0.5 + bid_concentration, 1.0)
                metadata = {
                    "trap_type": "support",
                    "concentration_score": bid_concentration,
                    "whale_value": whale_bid_value,
                    "key_levels": bid_levels,
                    "total_liquidity": liquidity,
                    "reasoning": self._generate_support_reasoning(bid_concentration, whale_bid_value, bid_levels)
                }

        # Resistance trap (whales selling at higher levels)
        elif ask_concentration > self.concentration_threshold:
            whale_ask_value = self._calculate_whale_value(asks, ask_levels)
            if whale_ask_value > self.whale_threshold:
                trap_detected = True
                direction = "SHORT"
                confidence = min(0.5 + ask_concentration, 1.0)
                metadata = {
                    "trap_type": "resistance",
                    "concentration_score": ask_concentration,
                    "whale_value": whale_ask_value,
                    "key_levels": ask_levels,
                    "total_liquidity": liquidity,
                    "reasoning": self._generate_resistance_reasoning(ask_concentration, whale_ask_value, ask_levels)
                }

        return trap_detected, direction, confidence, metadata

    def _calculate_concentration(
        self,
        orders: List[Dict],
        current_price: float
    ) -> Tuple[float, List[Dict]]:
        """
        Calculate how concentrated liquidity is at specific levels.

        Returns: (concentration_ratio, key_levels)
        """
        if not orders:
            return 0.0, []

        # Group orders by price levels (within 1% bands)
        level_groups = defaultdict(float)
        for order in orders:
            price = order.get("price", 0)
            size = order.get("size", 0) * price  # Convert to dollar value

            # Group by price level (1% bands)
            level_key = round(price * 100)
            level_groups[level_key] += size

        if not level_groups:
            return 0.0, []

        total_liquidity = sum(level_groups.values())
        if total_liquidity == 0:
            return 0.0, []

        # Find the level with maximum concentration
        max_level = max(level_groups.items(), key=lambda x: x[1])
        max_concentration = max_level[1] / total_liquidity

        # Find all levels with significant concentration (>20% of total)
        key_levels = []
        for level, value in level_groups.items():
            if value / total_liquidity > 0.2:
                key_levels.append({
                    "price": level / 100.0,
                    "liquidity": value,
                    "percentage": value / total_liquidity
                })

        # Sort by liquidity descending
        key_levels.sort(key=lambda x: x["liquidity"], reverse=True)

        return max_concentration, key_levels

    def _calculate_whale_value(self, orders: List[Dict], key_levels: List[Dict]) -> float:
        """Calculate total dollar value of whale-sized orders at key levels"""
        whale_value = 0.0

        for level in key_levels:
            level_price = level["price"]
            level_liquidity = level["liquidity"]

            # Only count if it's whale-sized
            if level_liquidity > self.whale_threshold:
                whale_value += level_liquidity

        return whale_value

    def _generate_support_reasoning(
        self,
        concentration: float,
        whale_value: float,
        levels: List[Dict]
    ) -> str:
        """Generate reasoning for support trap"""
        top_level = levels[0] if levels else {}
        top_price = top_level.get("price", 0)

        parts = [
            f"Whale support at ${top_price:.4f}",
            f"${whale_value:,.0f} concentrated",
            f"{concentration:.1%} of bids at key level"
        ]
        return "; ".join(parts)

    def _generate_resistance_reasoning(
        self,
        concentration: float,
        whale_value: float,
        levels: List[Dict]
    ) -> str:
        """Generate reasoning for resistance trap"""
        top_level = levels[0] if levels else {}
        top_price = top_level.get("price", 0)

        parts = [
            f"Whale resistance at ${top_price:.4f}",
            f"${whale_value:,.0f} concentrated",
            f"{concentration:.1%} of asks at key level"
        ]
        return "; ".join(parts)

    def _no_pattern_result(self, market_id: str) -> PatternResult:
        """Return result with no pattern detected"""
        return PatternResult(
            pattern_type=self.pattern_type,
            market_id=market_id,
            detected=False,
            confidence=0.0,
            strength=PatternStrength.WEAK,
            direction="NEUTRAL",
            detected_at=datetime.now(),
            metadata={"reason": "No liquidity trap detected"}
        )
