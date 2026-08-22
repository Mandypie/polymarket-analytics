"""
Strategy Definition and Execution

Defines trading strategies for backtesting and live trading.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class StrategyType(Enum):
    """Strategy types"""
    EDGE_BASED = "edge_based"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    LIQUIDITY = "liquidity"
    COMBINED = "combined"


@dataclass
class TradingSignal:
    """A trading signal"""
    market_id: str
    signal_type: SignalType
    confidence: float  # 0 to 1
    price: float
    size: float
    reasoning: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary"""
        return {
            "market_id": self.market_id,
            "signal_type": self.signal_type.value,
            "confidence": self.confidence,
            "price": self.price,
            "size": self.size,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }


@dataclass
class StrategyConfig:
    """Configuration for a strategy"""
    name: str
    strategy_type: StrategyType
    parameters: Dict[str, Any]
    max_position_size: float = 1000.0
    min_confidence: float = 0.6
    max_signals_per_day: int = 50


class Strategy:
    """Base class for trading strategies"""

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.signals_generated: List[TradingSignal] = []
        self.performance_metrics: Dict[str, float] = {}

    def analyze_market(self, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Analyze market data and generate a signal

        Args:
            market_data: Market data including prices, volume, liquidity

        Returns:
            TradingSignal or None if no signal generated
        """
        raise NotImplementedError("Subclasses must implement analyze_market")

    def validate_signal(self, signal: TradingSignal) -> bool:
        """Validate if a signal meets strategy criteria"""
        return (
            signal.confidence >= self.config.min_confidence and
            signal.price > 0 and
            signal.size > 0 and
            signal.size <= self.config.max_position_size
        )

    def add_signal(self, signal: TradingSignal) -> None:
        """Add a generated signal to history"""
        if self.validate_signal(signal):
            self.signals_generated.append(signal)

    def get_signal_count(self) -> int:
        """Get number of signals generated"""
        return len(self.signals_generated)

    def get_recent_signals(self, limit: int = 10) -> List[TradingSignal]:
        """Get most recent signals"""
        return self.signals_generated[-limit:]


class EdgeBasedStrategy(Strategy):
    """Strategy based on edge calculations"""

    def analyze_market(self, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generate signal based on edge value"""
        edge_value = market_data.get("edge", {}).get("value", 0)
        edge_confidence = market_data.get("edge", {}).get("confidence", 0)
        yes_price = market_data.get("yes_price", 0)

        # Edge threshold from config
        edge_threshold = self.config.parameters.get("edge_threshold", 0.05)

        if edge_value > edge_threshold and edge_confidence >= self.config.min_confidence:
            # Positive edge - BUY YES
            return TradingSignal(
                market_id=market_data.get("market_id", ""),
                signal_type=SignalType.BUY,
                confidence=edge_confidence,
                price=yes_price,
                size=self.config.parameters.get("position_size", 100),
                reasoning=f"Positive edge of {edge_value:.3f}",
                timestamp=datetime.now(),
                metadata={"edge_value": edge_value}
            )
        elif edge_value < -edge_threshold and edge_confidence >= self.config.min_confidence:
            # Negative edge - SELL YES (buy NO)
            return TradingSignal(
                market_id=market_data.get("market_id", ""),
                signal_type=SignalType.SELL,
                confidence=edge_confidence,
                price=yes_price,
                size=self.config.parameters.get("position_size", 100),
                reasoning=f"Negative edge of {edge_value:.3f}",
                timestamp=datetime.now(),
                metadata={"edge_value": edge_value}
            )

        return None


class MeanReversionStrategy(Strategy):
    """Mean reversion strategy - bet on price returning to mean"""

    def analyze_market(self, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generate mean reversion signal"""
        yes_price = market_data.get("yes_price", 0)
        volume_24h = market_data.get("volume_24h", 0)

        # Calculate z-score deviation from recent mean
        historical_prices = market_data.get("price_history", [])
        if len(historical_prices) < 10:
            return None

        mean_price = sum(historical_prices) / len(historical_prices)
        std_price = (sum((p - mean_price) ** 2 for p in historical_prices) / len(historical_prices)) ** 0.5

        if std_price == 0:
            return None

        z_score = (yes_price - mean_price) / std_price
        z_threshold = self.config.parameters.get("z_threshold", 2.0)

        if z_score > z_threshold:
            # Price too high - bet on mean reversion down (SELL)
            confidence = min(abs(z_score) / z_threshold, 1.0)
            return TradingSignal(
                market_id=market_data.get("market_id", ""),
                signal_type=SignalType.SELL,
                confidence=confidence,
                price=yes_price,
                size=self.config.parameters.get("position_size", 100),
                reasoning=f"Price {z_score:.2f}σ above mean, expecting reversion",
                timestamp=datetime.now(),
                metadata={"z_score": z_score, "mean_price": mean_price}
            )
        elif z_score < -z_threshold:
            # Price too low - bet on mean reversion up (BUY)
            confidence = min(abs(z_score) / z_threshold, 1.0)
            return TradingSignal(
                market_id=market_data.get("market_id", ""),
                signal_type=SignalType.BUY,
                confidence=confidence,
                price=yes_price,
                size=self.config.parameters.get("position_size", 100),
                reasoning=f"Price {z_score:.2f}σ below mean, expecting reversion",
                timestamp=datetime.now(),
                metadata={"z_score": z_score, "mean_price": mean_price}
            )

        return None


class MomentumStrategy(Strategy):
    """Momentum strategy - bet on price continuing trend"""

    def analyze_market(self, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generate momentum signal"""
        yes_price = market_data.get("yes_price", 0)
        price_history = market_data.get("price_history", [])

        if len(price_history) < 5:
            return None

        # Calculate price change over recent periods
        price_change = (yes_price - price_history[0]) / price_history[0] if price_history[0] > 0 else 0
        momentum_threshold = self.config.parameters.get("momentum_threshold", 0.05)

        if price_change > momentum_threshold:
            # Upward momentum - BUY
            confidence = min(abs(price_change) / momentum_threshold, 1.0)
            return TradingSignal(
                market_id=market_data.get("market_id", ""),
                signal_type=SignalType.BUY,
                confidence=confidence,
                price=yes_price,
                size=self.config.parameters.get("position_size", 100),
                reasoning=f"Upward momentum of {price_change:.2%}",
                timestamp=datetime.now(),
                metadata={"momentum": price_change}
            )
        elif price_change < -momentum_threshold:
            # Downward momentum - SELL
            confidence = min(abs(price_change) / momentum_threshold, 1.0)
            return TradingSignal(
                market_id=market_data.get("market_id", ""),
                signal_type=SignalType.SELL,
                confidence=confidence,
                price=yes_price,
                size=self.config.parameters.get("position_size", 100),
                reasoning=f"Downward momentum of {price_change:.2%}",
                timestamp=datetime.now(),
                metadata={"momentum": price_change}
            )

        return None


class LiquidityStrategy(Strategy):
    """Strategy based on liquidity and spread analysis"""

    def analyze_market(self, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generate signal based on liquidity"""
        yes_price = market_data.get("yes_price", 0)
        liquidity = market_data.get("liquidity", 0)
        volume_24h = market_data.get("volume_24h", 0)

        # Minimum liquidity threshold
        min_liquidity = self.config.parameters.get("min_liquidity", 50000)
        min_volume = self.config.parameters.get("min_volume", 100000)

        if liquidity < min_liquidity or volume_24h < min_volume:
            return None

        # Tight spread indicates good entry opportunity
        no_price = market_data.get("no_price", 1 - yes_price)
        spread = abs(yes_price - no_price)

        max_spread = self.config.parameters.get("max_spread", 0.03)

        if spread < max_spread:
            # Good liquidity with tight spread - generate signal based on edge
            edge_value = market_data.get("edge", {}).get("value", 0)

            if edge_value > 0:
                return TradingSignal(
                    market_id=market_data.get("market_id", ""),
                    signal_type=SignalType.BUY,
                    confidence=0.7,  # Base confidence on liquidity quality
                    price=yes_price,
                    size=self.config.parameters.get("position_size", 100),
                    reasoning=f"Tight spread ({spread:.2%}) with positive edge",
                    timestamp=datetime.now(),
                    metadata={"spread": spread, "liquidity": liquidity}
                )

        return None


class CombinedStrategy(Strategy):
    """Combines multiple strategies with weighted voting"""

    def __init__(self, config: StrategyConfig, sub_strategies: List[Strategy]):
        super().__init__(config)
        self.sub_strategies = sub_strategies
        self.strategy_weights = self.config.parameters.get("strategy_weights", {})

    def analyze_market(self, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generate combined signal from sub-strategies"""
        signals = []
        for strategy in self.sub_strategies:
            signal = strategy.analyze_market(market_data)
            if signal:
                weight = self.strategy_weights.get(strategy.config.name, 1.0)
                signals.append((signal, weight))

        if not signals:
            return None

        # Weighted voting
        buy_weight = sum(w for s, w in signals if s.signal_type == SignalType.BUY)
        sell_weight = sum(w for s, w in signals if s.signal_type == SignalType.SELL)

        # Average confidence weighted by strategy weight
        total_weight = buy_weight + sell_weight
        if total_weight == 0:
            return None

        avg_confidence = sum(
            s.confidence * w for s, w in signals
        ) / total_weight

        if buy_weight > sell_weight:
            # Combine reasoning from all BUY signals
            reasoning = "; ".join(
                s.reasoning for s, w in signals if s.signal_type == SignalType.BUY
            )
            return TradingSignal(
                market_id=market_data.get("market_id", ""),
                signal_type=SignalType.BUY,
                confidence=avg_confidence,
                price=market_data.get("yes_price", 0),
                size=self.config.parameters.get("position_size", 100),
                reasoning=f"Combined BUY (weight: {buy_weight:.1f}): {reasoning}",
                timestamp=datetime.now(),
                metadata={"buy_weight": buy_weight, "sell_weight": sell_weight}
            )
        elif sell_weight > buy_weight:
            reasoning = "; ".join(
                s.reasoning for s, w in signals if s.signal_type == SignalType.SELL
            )
            return TradingSignal(
                market_id=market_data.get("market_id", ""),
                signal_type=SignalType.SELL,
                confidence=avg_confidence,
                price=market_data.get("yes_price", 0),
                size=self.config.parameters.get("position_size", 100),
                reasoning=f"Combined SELL (weight: {sell_weight:.1f}): {reasoning}",
                timestamp=datetime.now(),
                metadata={"buy_weight": buy_weight, "sell_weight": sell_weight}
            )

        return None


def create_strategy(config: StrategyConfig) -> Strategy:
    """Factory function to create strategies"""
    if config.strategy_type == StrategyType.EDGE_BASED:
        return EdgeBasedStrategy(config)
    elif config.strategy_type == StrategyType.MEAN_REVERSION:
        return MeanReversionStrategy(config)
    elif config.strategy_type == StrategyType.MOMENTUM:
        return MomentumStrategy(config)
    elif config.strategy_type == StrategyType.LIQUIDITY:
        return LiquidityStrategy(config)
    elif config.strategy_type == StrategyType.COMBINED:
        # Combined strategy requires sub-strategies
        sub_configs = config.parameters.get("sub_strategies", [])
        sub_strategies = [create_strategy(StrategyConfig(**sc)) for sc in sub_configs]
        return CombinedStrategy(config, sub_strategies)
    else:
        raise ValueError(f"Unknown strategy type: {config.strategy_type}")
