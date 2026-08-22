"""
Signal Generation Module

Generates automated trading signals based on market data and analytics.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .edge_calculator import calculate_edge

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels"""
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"


class SignalDirection(Enum):
    """Signal direction"""
    LONG = "LONG"      # Bet on YES
    SHORT = "SHORT"    # Bet on NO
    NEUTRAL = "NEUTRAL"


@dataclass
class TradingSignal:
    """A generated trading signal"""
    market_id: str
    direction: SignalDirection
    strength: SignalStrength
    confidence: float  # 0 to 1
    entry_price: float
    target_price: float
    stop_loss: float
    reasoning: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary"""
        return {
            "market_id": self.market_id,
            "direction": self.direction.value,
            "strength": self.strength.value,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }


class SignalGenerator:
    """Generates trading signals based on market analysis"""

    def __init__(self):
        self.generated_signals: List[TradingSignal] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the signal generator"""
        if self._initialized:
            return

        self._initialized = True
        logger.info("Signal generator initialized")

    async def generate_signal(self, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generate a trading signal for a market

        Args:
            market_data: Market data including prices, liquidity, edge

        Returns:
            TradingSignal or None if no signal generated
        """
        if not self._initialized:
            await self.initialize()

        market_id = market_data.get("market_id", "")
        yes_price = market_data.get("yes_price", 0)
        liquidity = market_data.get("liquidity", 0)
        volume_24h = market_data.get("volume_24h", 0)

        # Minimum requirements
        if yes_price <= 0 or yes_price >= 1:
            return None

        if liquidity < 10000 or volume_24h < 50000:
            return None

        # Get edge data
        edge_data = market_data.get("edge", {})
        edge_value = edge_data.get("value", 0)
        edge_confidence = edge_data.get("confidence", 0)
        edge_signal = edge_data.get("signal", "NEUTRAL")

        # Calculate spread
        no_price = 1 - yes_price
        spread = abs(yes_price - no_price)

        # Generate signal based on edge
        signal = None

        if edge_value > 0.05 and edge_confidence > 0.6 and edge_signal == "BUY":
            # Strong buy signal
            strength = self._calculate_strength(edge_value, edge_confidence, liquidity)
            direction = SignalDirection.LONG

            target_price = min(yes_price * 1.2, 0.95)  # 20% gain or cap at 0.95
            stop_loss = max(yes_price * 0.9, 0.05)   # 10% loss or floor at 0.05

            signal = TradingSignal(
                market_id=market_id,
                direction=direction,
                strength=strength,
                confidence=edge_confidence,
                entry_price=yes_price,
                target_price=target_price,
                stop_loss=stop_loss,
                reasoning=f"Positive edge of {edge_value:.3f} with {edge_confidence:.1%} confidence. Tight spread: {spread:.2%}",
                timestamp=datetime.now(),
                metadata={
                    "edge_value": edge_value,
                    "liquidity": liquidity,
                    "volume_24h": volume_24h,
                    "spread": spread
                }
            )

        elif edge_value < -0.05 and edge_confidence > 0.6 and edge_signal == "SELL":
            # Strong sell signal
            strength = self._calculate_strength(abs(edge_value), edge_confidence, liquidity)
            direction = SignalDirection.SHORT

            target_price = max(yes_price * 0.8, 0.05)  # 20% gain or floor at 0.05
            stop_loss = min(yes_price * 1.1, 0.95)     # 10% loss or cap at 0.95

            signal = TradingSignal(
                market_id=market_id,
                direction=direction,
                strength=strength,
                confidence=edge_confidence,
                entry_price=yes_price,
                target_price=target_price,
                stop_loss=stop_loss,
                reasoning=f"Negative edge of {edge_value:.3f} with {edge_confidence:.1%} confidence. Tight spread: {spread:.2%}",
                timestamp=datetime.now(),
                metadata={
                    "edge_value": edge_value,
                    "liquidity": liquidity,
                    "volume_24h": volume_24h,
                    "spread": spread
                }
            )

        # Store signal if generated
        if signal:
            self.generated_signals.append(signal)
            logger.info(f"Generated {signal.direction.value} signal for {market_id} with strength {signal.strength.value}")

        return signal

    def _calculate_strength(self, edge_value: float, confidence: float, liquidity: float) -> SignalStrength:
        """Calculate signal strength based on edge, confidence, and liquidity"""
        score = (edge_value * 10) + (confidence * 5) + (min(liquidity / 100000, 1) * 2)

        if score >= 8:
            return SignalStrength.VERY_STRONG
        elif score >= 5:
            return SignalStrength.STRONG
        elif score >= 3:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK

    async def generate_batch_signals(self, markets: List[Dict[str, Any]]) -> List[TradingSignal]:
        """Generate signals for multiple markets

        Args:
            markets: List of market data

        Returns:
            List of generated signals
        """
        signals = []

        for market in markets:
            try:
                signal = await self.generate_signal(market)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating signal for market: {e}")

        return signals

    def get_recent_signals(self, limit: int = 20) -> List[TradingSignal]:
        """Get most recently generated signals"""
        return self.generated_signals[-limit:]

    def get_signals_by_strength(self, strength: SignalStrength) -> List[TradingSignal]:
        """Get signals filtered by strength"""
        return [s for s in self.generated_signals if s.strength == strength]

    def get_signals_by_direction(self, direction: SignalDirection) -> List[TradingSignal]:
        """Get signals filtered by direction"""
        return [s for s in self.generated_signals if s.direction == direction]

    def get_signal_stats(self) -> Dict[str, Any]:
        """Get statistics about generated signals"""
        if not self.generated_signals:
            return {
                "total_signals": 0,
                "by_direction": {},
                "by_strength": {},
                "avg_confidence": 0
            }

        total = len(self.generated_signals)

        by_direction = {
            SignalDirection.LONG.value: len([s for s in self.generated_signals if s.direction == SignalDirection.LONG]),
            SignalDirection.SHORT.value: len([s for s in self.generated_signals if s.direction == SignalDirection.SHORT]),
            SignalDirection.NEUTRAL.value: len([s for s in self.generated_signals if s.direction == SignalDirection.NEUTRAL])
        }

        by_strength = {
            SignalStrength.VERY_STRONG.value: len([s for s in self.generated_signals if s.strength == SignalStrength.VERY_STRONG]),
            SignalStrength.STRONG.value: len([s for s in self.generated_signals if s.strength == SignalStrength.STRONG]),
            SignalStrength.MODERATE.value: len([s for s in self.generated_signals if s.strength == SignalStrength.MODERATE]),
            SignalStrength.WEAK.value: len([s for s in self.generated_signals if s.strength == SignalStrength.WEAK])
        }

        avg_confidence = sum(s.confidence for s in self.generated_signals) / total if total > 0 else 0

        return {
            "total_signals": total,
            "by_direction": by_direction,
            "by_strength": by_strength,
            "avg_confidence": avg_confidence
        }

    def clear_old_signals(self, hours: int = 24) -> None:
        """Clear signals older than specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        self.generated_signals = [s for s in self.generated_signals if s.timestamp > cutoff]
        logger.info(f"Cleared signals older than {hours} hours")


# Global signal generator instance
_signal_generator: Optional[SignalGenerator] = None


async def get_signal_generator() -> SignalGenerator:
    """Get or create the signal generator"""
    global _signal_generator
    if _signal_generator is None:
        _signal_generator = SignalGenerator()
        await _signal_generator.initialize()
    return _signal_generator
