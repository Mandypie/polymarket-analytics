"""
Momentum Reversal Detector

Detects momentum reversals before price reflects them.
Identifies when a strong trend is about to reverse.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np

from .base_detector import BaseDetector, PatternResult, PatternType, PatternStrength

logger = logging.getLogger(__name__)


class MomentumReversalDetector(BaseDetector):
    """
    Detects momentum reversals in market prices.

    Uses RSI, MACD-style indicators, and price velocity
    to identify when momentum is about to reverse.
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.MOMENTUM_REVERSAL
        self.rsi_overbought = 70.0
        self.rsi_oversold = 30.0
        self.velocity_threshold = 0.02  # 2% price change threshold
        self.pattern_ttl_hours = 6  # Reversals happen quickly

    async def detect(
        self,
        market_data: Dict[str, Any],
        historical_data: List[Dict] = None
    ) -> PatternResult:
        """Detect momentum reversal pattern"""
        if not self._validate_market_data(market_data):
            return self._no_pattern_result(market_data.get("market_id", ""))

        market_id = market_data.get("market_id")
        current_price = market_data.get("yes_price", 0.5)
        volume = market_data.get("volume_24h", 0)
        liquidity = market_data.get("liquidity", 0)

        # Need historical data for momentum calculations
        if not historical_data or len(historical_data) < 10:
            return self._no_pattern_result(market_id)

        try:
            prices = [d.get("yes_price", current_price) for d in historical_data]
            prices.append(current_price)

            # Calculate indicators
            rsi = self._calculate_rsi(prices)
            momentum = self._calculate_momentum(prices)
            velocity = self._calculate_velocity(prices)
            macd_signal = self._calculate_macd_signal(prices)

            # Detect reversal conditions
            reversal_detected, direction, confidence = self._detect_reversal(
                rsi, momentum, velocity, macd_signal, current_price, volume, liquidity
            )

            if reversal_detected:
                strength = self._calculate_strength(confidence, abs(momentum))

                return PatternResult(
                    pattern_type=self.pattern_type,
                    market_id=market_id,
                    detected=True,
                    confidence=confidence,
                    strength=strength,
                    direction=direction,
                    detected_at=datetime.now(),
                    expires_at=self._calculate_expiry(self.pattern_ttl_hours),
                    metadata={
                        "rsi": rsi,
                        "momentum": momentum,
                        "velocity": velocity,
                        "macd_signal": macd_signal,
                        "current_price": current_price,
                        "reasoning": self._generate_reasoning(rsi, momentum, direction)
                    }
                )
            else:
                return self._no_pattern_result(market_id)

        except Exception as e:
            logger.error(f"Error detecting momentum reversal for {market_id}: {e}")
            return self._no_pattern_result(market_id)

    async def detect_batch(self, markets: List[Dict[str, Any]]) -> List[PatternResult]:
        """Detect momentum reversals across multiple markets"""
        results = []
        for market in markets:
            historical = market.get("price_history", [])
            result = await self.detect(market, historical)
            results.append(result)
        return results

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral

        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_momentum(self, prices: List[float], period: int = 5) -> float:
        """Calculate price momentum"""
        if len(prices) < period + 1:
            return 0.0

        current = prices[-1]
        past = prices[-period - 1]
        momentum = (current - past) / past if past > 0 else 0
        return momentum

    def _calculate_velocity(self, prices: List[float]) -> float:
        """Calculate price velocity (rate of change)"""
        if len(prices) < 3:
            return 0.0

        # Second derivative approximation
        recent_changes = [
            (prices[i] - prices[i-1]) / prices[i-1] if prices[i-1] > 0 else 0
            for i in range(1, len(prices))
        ]

        if len(recent_changes) < 2:
            return 0.0

        velocity = recent_changes[-1] - recent_changes[-2]
        return velocity

    def _calculate_macd_signal(self, prices: List[float]) -> str:
        """Calculate MACD-style signal"""
        if len(prices) < 26:
            return "NEUTRAL"

        # Simple MACD approximation
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)

        macd = ema_12 - ema_26

        if macd > 0.01:
            return "BULLISH"
        elif macd < -0.01:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices)

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _detect_reversal(
        self,
        rsi: float,
        momentum: float,
        velocity: float,
        macd_signal: str,
        current_price: float,
        volume: float,
        liquidity: float
    ) -> tuple:
        """
        Detect if momentum is about to reverse.

        Returns: (detected: bool, direction: str, confidence: float)
        """
        signals = []
        confidence_score = 0.0

        # RSI reversal signals
        if rsi > self.rsi_overbought:
            # Overbought - potential bearish reversal
            signals.append(("SHORT", 0.8))
            confidence_score += 0.3
        elif rsi < self.rsi_oversold:
            # Oversold - potential bullish reversal
            signals.append(("LONG", 0.8))
            confidence_score += 0.3

        # Momentum divergence
        if abs(momentum) > self.velocity_threshold:
            if velocity < -0.01 and momentum > 0:
                # Momentum positive but slowing down - bearish reversal
                signals.append(("SHORT", 0.7))
                confidence_score += 0.25
            elif velocity > 0.01 and momentum < 0:
                # Momentum negative but slowing down - bullish reversal
                signals.append(("LONG", 0.7))
                confidence_score += 0.25

        # MACD divergence
        if macd_signal == "BULLISH" and momentum < 0:
            signals.append(("LONG", 0.6))
            confidence_score += 0.15
        elif macd_signal == "BEARISH" and momentum > 0:
            signals.append(("SHORT", 0.6))
            confidence_score += 0.15

        # Volume confirmation (higher volume = higher confidence)
        if volume > 100000:
            confidence_score += 0.1
        if liquidity > 50000:
            confidence_score += 0.05

        # Aggregate signals
        if not signals:
            return False, "NEUTRAL", 0.0

        # Count signal directions
        long_signals = sum(1 for s, w in signals if s == "LONG")
        short_signals = sum(1 for s, w in signals if s == "SHORT")

        if long_signals > short_signals:
            direction = "LONG"
            confidence = min(confidence_score, 1.0)
        elif short_signals > long_signals:
            direction = "SHORT"
            confidence = min(confidence_score, 1.0)
        else:
            return False, "NEUTRAL", 0.0

        # Minimum confidence threshold
        if confidence < self.min_confidence:
            return False, "NEUTRAL", 0.0

        return True, direction, confidence

    def _generate_reasoning(self, rsi: float, momentum: float, direction: str) -> str:
        """Generate human-readable reasoning"""
        reasons = []

        if direction == "LONG":
            if rsi < self.rsi_oversold:
                reasons.append(f"RSI oversold ({rsi:.1f})")
            if momentum < 0:
                reasons.append(f"Negative momentum fading ({momentum:.3f})")
        else:  # SHORT
            if rsi > self.rsi_overbought:
                reasons.append(f"RSI overbought ({rsi:.1f})")
            if momentum > 0:
                reasons.append(f"Positive momentum fading ({momentum:.3f})")

        return "; ".join(reasons) if reasons else "Technical reversal detected"

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
            metadata={"reason": "No momentum reversal detected"}
        )
