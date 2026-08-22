"""
Resolution Probability Detector

Predicts market outcomes from order flow and market structure.
Analyzes betting patterns to estimate true probability of YES/NO.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from .base_detector import BaseDetector, PatternResult, PatternType, PatternStrength

logger = logging.getLogger(__name__)


class ResolutionProbabilityDetector(BaseDetector):
    """
    Detects resolution probability from order flow analysis.

    Uses order book imbalance, volume patterns, and price trends
    to predict the likely outcome of a market.
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.RESOLUTION_PROB
        self.imbalance_threshold = 0.6  # 60% order imbalance significant
        self.volume_surge_threshold = 2.0  # 2x normal volume
        self.pattern_ttl_hours = 24  # Probabilities stable over longer term

    async def detect(
        self,
        market_data: Dict[str, Any],
        historical_data: List[Dict] = None
    ) -> PatternResult:
        """Detect resolution probability pattern"""
        if not self._validate_market_data(market_data):
            return self._no_pattern_result(market_data.get("market_id", ""))

        market_id = market_data.get("market_id")
        current_price = market_data.get("yes_price", 0.5)
        volume_24h = market_data.get("volume_24h", 0)
        liquidity = market_data.get("liquidity", 0)

        try:
            # Analyze order flow and market structure
            probability_detected, direction, confidence, metadata = self._analyze_resolution_probability(
                market_data, historical_data
            )

            if probability_detected:
                strength = self._calculate_strength(confidence, metadata.get("probability_score", 0.5))

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
            logger.error(f"Error detecting resolution probability for {market_id}: {e}")
            return self._no_pattern_result(market_id)

    async def detect_batch(self, markets: List[Dict[str, Any]]) -> List[PatternResult]:
        """Detect resolution probabilities across multiple markets"""
        results = []
        for market in markets:
            historical = market.get("price_history", [])
            result = await self.detect(market, historical)
            results.append(result)
        return results

    def _analyze_resolution_probability(
        self,
        market_data: Dict,
        historical_data: List[Dict] = None
    ) -> Tuple[bool, str, float, Dict]:
        """
        Analyze order flow to predict resolution.

        Returns: (detected, direction, confidence, metadata)
        """
        current_price = market_data.get("yes_price", 0.5)
        volume_24h = market_data.get("volume_24h", 0)
        liquidity = market_data.get("liquidity", 0)

        # Get order book data
        order_book = market_data.get("order_book", {})
        bids = order_book.get("bids", [])
        asks = order_book.get("asks", [])

        # Analyze order flow indicators
        signals = []
        yes_signals = 0
        no_signals = 0

        # 1. Order book imbalance
        if bids and asks:
            bid_volume = sum(b.get("size", 0) for b in bids)
            ask_volume = sum(a.get("size", 0) for a in asks)
            total_volume = bid_volume + ask_volume

            if total_volume > 0:
                yes_ratio = bid_volume / total_volume
                if yes_ratio > self.imbalance_threshold:
                    yes_signals += 1
                elif yes_ratio < (1 - self.imbalance_threshold):
                    no_signals += 1

        # 2. Price momentum (from historical data)
        if historical_data and len(historical_data) >= 5:
            prices = [d.get("yes_price", current_price) for d in historical_data] + [current_price]
            momentum = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] > 0 else 0

            if momentum > 0.05:
                yes_signals += 1
            elif momentum < -0.05:
                no_signals += 1

        # 3. Volume surge analysis
        if historical_data and len(historical_data) >= 24:
            recent_volumes = [d.get("volume_24h", volume_24h) for d in historical_data[-24:]]
            avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else volume_24h

            if avg_volume > 0:
                volume_ratio = volume_24h / avg_volume
                if volume_ratio > self.volume_surge_threshold:
                    # Volume surge - check direction
                    if current_price > 0.6:
                        yes_signals += 1
                    elif current_price < 0.4:
                        no_signals += 1

        # 4. Liquidity quality
        if liquidity > 100000:
            # High liquidity markets more efficient
            yes_signals += 0.5
        elif liquidity < 10000:
            # Low liquidity - less reliable
            yes_signals -= 0.5

        # Aggregate signals
        total_signals = yes_signals + no_signals
        if total_signals < 1:
            return False, "NEUTRAL", 0.0, {}

        # Calculate confidence based on signal strength
        confidence = min(0.5 + (total_signals / 4) * 0.5, 1.0)

        # Determine direction
        if yes_signals > no_signals:
            direction = "LONG"
            probability_score = yes_signals / max(total_signals, 1)
        else:
            direction = "SHORT"
            probability_score = no_signals / max(total_signals, 1)

        # Minimum confidence threshold
        if confidence < self.min_confidence:
            return False, "NEUTRAL", 0.0, {}

        metadata = {
            "probability_type": "order_flow_analysis",
            "yes_signals": yes_signals,
            "no_signals": no_signals,
            "probability_score": probability_score,
            "current_price": current_price,
            "order_flow_bias": "YES" if yes_signals > no_signals else "NO",
            "reasoning": self._generate_reasoning(yes_signals, no_signals, direction)
        }

        return True, direction, confidence, metadata

    def _generate_reasoning(self, yes_signals: float, no_signals: float, direction: str) -> str:
        """Generate human-readable reasoning"""
        parts = []

        if direction == "LONG":
            parts.append(f"Order flow favors YES ({yes_signals:.1f} vs {no_signals:.1f} signals)")
        else:
            parts.append(f"Order flow favors NO ({no_signals:.1f} vs {yes_signals:.1f} signals)")

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
            metadata={"reason": "No clear resolution probability detected"}
        )
