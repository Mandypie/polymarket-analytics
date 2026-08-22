"""
Cross-Market Correlation Detector

Finds opportunities across related markets moving together.
Identifies arbitrage opportunities and correlated price movements.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from .base_detector import BaseDetector, PatternResult, PatternType, PatternStrength

logger = logging.getLogger(__name__)


class CrossMarketCorrelationDetector(BaseDetector):
    """
    Detects cross-market correlations and arbitrage opportunities.

    Identifies when related markets (e.g., BTC vs ETH price predictions)
    are moving together or diverging, creating opportunities.
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.CROSS_MARKET
        self.correlation_threshold = 0.7  # Minimum correlation to consider
        self.divergence_threshold = 0.05  # 5% price divergence for arbitrage
        self.pattern_ttl_hours = 4  # Correlations change relatively quickly

        # Market category mappings for correlation analysis
        self.category_correlations = {
            "Crypto": ["BTC", "ETH", "SOL", "crypto"],
            "Politics": ["election", "trump", "biden", "congress", "vote"],
            "Sports": ["game", "team", "score", "win"]
        }

    async def detect(
        self,
        market_data: Dict[str, Any],
        historical_data: List[Dict] = None,
        all_markets: List[Dict] = None
    ) -> PatternResult:
        """Detect cross-market correlation pattern"""
        if not self._validate_market_data(market_data):
            return self._no_pattern_result(market_data.get("market_id", ""))

        market_id = market_data.get("market_id")
        current_price = market_data.get("yes_price", 0.5)
        category = market_data.get("category", "")

        # Need other markets for correlation analysis
        if not all_markets:
            return self._no_pattern_result(market_id)

        try:
            # Find correlated markets and analyze relationships
            correlation_detected, direction, confidence, metadata = self._analyze_correlations(
                market_data, all_markets, historical_data
            )

            if correlation_detected:
                strength = self._calculate_strength(confidence, metadata.get("correlation_strength", 0.5))

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
            logger.error(f"Error detecting cross-market correlation for {market_id}: {e}")
            return self._no_pattern_result(market_id)

    async def detect_batch(self, markets: List[Dict[str, Any]]) -> List[PatternResult]:
        """Detect cross-market correlations across multiple markets"""
        results = []

        # For each market, analyze against all others
        for i, market in enumerate(markets):
            other_markets = markets[:i] + markets[i+1:]
            result = await self.detect(market, None, other_markets)
            results.append(result)

        return results

    def _analyze_correlations(
        self,
        target_market: Dict,
        all_markets: List[Dict],
        historical_data: List[Dict] = None
    ) -> Tuple[bool, str, float, Dict]:
        """
        Analyze correlations between target market and other markets.

        Returns: (detected, direction, confidence, metadata)
        """
        target_id = target_market.get("market_id")
        target_price = target_market.get("yes_price", 0.5)
        target_category = target_market.get("category", "")

        correlated_markets = []
        divergent_markets = []

        for market in all_markets:
            market_id = market.get("market_id")
            if market_id == target_id:
                continue

            market_price = market.get("yes_price", 0.5)
            market_category = market.get("category", "")

            # Check if markets are related (same category or keywords)
            if not self._are_markets_related(target_market, market):
                continue

            # Calculate price correlation/divergence
            price_diff = abs(target_price - market_price)
            correlation_data = self._calculate_correlation(target_market, market)

            if correlation_data["correlation"] > self.correlation_threshold:
                # Check for divergence (arbitrage opportunity)
                if price_diff > self.divergence_threshold:
                    divergent_markets.append({
                        "market_id": market_id,
                        "price": market_price,
                        "correlation": correlation_data["correlation"],
                        "divergence": price_diff,
                        "direction": "SHORT" if market_price > target_price else "LONG"
                    })
                else:
                    # Strong correlation without divergence
                    correlated_markets.append({
                        "market_id": market_id,
                        "price": market_price,
                        "correlation": correlation_data["correlation"]
                    })

        # Determine if pattern detected
        if divergent_markets:
            # Arbitrage opportunity - strongest signal
            top_divergence = max(divergent_markets, key=lambda x: x["divergence"])
            direction = "LONG" if top_divergence["direction"] == "LONG" else "SHORT"
            confidence = min(0.6 + top_divergence["divergence"], 1.0)

            metadata = {
                "correlation_type": "divergence_arbitrage",
                "correlated_markets": divergent_markets,
                "correlation_strength": top_divergence["correlation"],
                "divergence_amount": top_divergence["divergence"],
                "target_market_price": target_price,
                "reasoning": self._generate_divergence_reasoning(top_divergence, divergent_markets)
            }

            return True, direction, confidence, metadata

        elif correlated_markets and len(correlated_markets) >= 2:
            # Multi-market correlation - confirmation signal
            avg_correlation = sum(m["correlation"] for m in correlated_markets) / len(correlated_markets)
            direction = "NEUTRAL"  # Correlation doesn't indicate direction
            confidence = min(0.5 + (avg_correlation - 0.7) * 2, 0.85)

            metadata = {
                "correlation_type": "multi_market_confirmation",
                "correlated_markets": correlated_markets,
                "correlation_strength": avg_correlation,
                "market_count": len(correlated_markets),
                "reasoning": self._generate_correlation_reasoning(correlated_markets, avg_correlation)
            }

            return True, direction, confidence, metadata

        return False, "NEUTRAL", 0.0, {}

    def _are_markets_related(self, market1: Dict, market2: Dict) -> bool:
        """Check if two markets are related (same category or keywords)"""
        category1 = market1.get("category", "").lower()
        category2 = market2.get("category", "").lower()

        # Same category
        if category1 and category2 and category1 == category2:
            return True

        # Check keyword correlations
        question1 = market1.get("question", "").lower()
        question2 = market2.get("question", "").lower()

        for category, keywords in self.category_correlations.items():
            category = category.lower()
            if any(kw in question1 for kw in keywords) and any(kw in question2 for kw in keywords):
                return True

        return False

    def _calculate_correlation(self, market1: Dict, market2: Dict) -> Dict:
        """
        Calculate correlation between two markets.

        Simplified correlation based on price movement similarity.
        In production, would use historical price data.
        """
        price1 = market1.get("yes_price", 0.5)
        price2 = market2.get("yes_price", 0.5)

        # Get recent price changes if available
        history1 = market1.get("price_history", [price1])
        history2 = market2.get("price_history", [price2])

        if len(history1) < 2 or len(history2) < 2:
            # Not enough data, use current prices
            return {
                "correlation": 0.5,  # Neutral
                "correlation_type": "unknown"
            }

        # Calculate recent changes
        changes1 = [(history1[i] - history1[i-1]) / history1[i-1] if history1[i-1] > 0 else 0
                    for i in range(1, len(history1))]
        changes2 = [(history2[i] - history2[i-1]) / history2[i-1] if history2[i-1] > 0 else 0
                    for i in range(1, len(history2))]

        if not changes1 or not changes2:
            return {"correlation": 0.5, "correlation_type": "unknown"}

        # Calculate correlation coefficient
        min_len = min(len(changes1), len(changes2))
        changes1 = changes1[-min_len:]
        changes2 = changes2[-min_len:]

        correlation = self._correlation_coefficient(changes1, changes2)

        return {
            "correlation": abs(correlation),  # Use absolute value
            "correlation_type": "positive" if correlation > 0 else "negative"
        }

    def _correlation_coefficient(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        sum_y2 = sum(yi ** 2 for yi in y)

        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        if denominator == 0:
            return 0.0

        correlation = (n * sum_xy - sum_x * sum_y) / denominator
        return correlation

    def _generate_divergence_reasoning(self, top_divergence: Dict, all_divergences: List[Dict]) -> str:
        """Generate reasoning for divergence arbitrage"""
        parts = [
            f"Price divergence of {top_divergence['divergence']:.2%}",
            f"vs correlated market ({top_divergence['market_id'][:8]}...)",
            f"Correlation: {top_divergence['correlation']:.2f}",
            f"Arbitrage opportunity: {top_divergence['direction']}"
        ]
        return "; ".join(parts)

    def _generate_correlation_reasoning(self, correlated_markets: List[Dict], avg_corr: float) -> str:
        """Generate reasoning for multi-market correlation"""
        count = len(correlated_markets)
        parts = [
            f"{count} correlated market{'s' if count > 1 else ''}",
            f"Average correlation: {avg_corr:.2f}",
            "Multi-market confirmation signal"
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
            metadata={"reason": "No cross-market correlation detected"}
        )
