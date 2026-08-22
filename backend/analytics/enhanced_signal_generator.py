"""
Enhanced Signal Generation Module

Extends the original signal generator with pattern detection integration
and multi-factor scoring.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .patterns import (
    MomentumReversalDetector,
    LiquidityTrapDetector,
    CrossMarketCorrelationDetector,
    ResolutionProbabilityDetector,
    SentimentAnalyzer
)
from .pattern_enhancement import (
    MultiFactorScorer,
    SignalFreshnessTracker,
    PerformanceAttribution,
    EnhancedSignal
)
from .edge_calculator import calculate_edge
from .signal_generator import SignalGenerator, TradingSignal, SignalStrength, SignalDirection

logger = logging.getLogger(__name__)


class MultiFactorSignalGenerator(SignalGenerator):
    """
    Enhanced signal generator with pattern detection integration.

    Combines the original edge-based signal generation with
    sophisticated pattern detection and multi-factor scoring.
    """

    def __init__(self):
        super().__init__()
        self.pattern_detectors = {}
        self.multi_factor_scorer: Optional[MultiFactorScorer] = None
        self.freshness_tracker: Optional[SignalFreshnessTracker] = None
        self.performance_tracker: Optional[PerformanceAttribution] = None
        self.patterns_initialized = False

    async def initialize(self) -> None:
        """Initialize the enhanced signal generator"""
        await super().initialize()

        if not self.patterns_initialized:
            # Initialize pattern detectors
            self.pattern_detectors = {
                "momentum_reversal": MomentumReversalDetector(),
                "liquidity_trap": LiquidityTrapDetector(),
                "cross_market": CrossMarketCorrelationDetector(),
                "resolution_probability": ResolutionProbabilityDetector(),
                "sentiment": SentimentAnalyzer()
            }

            # Initialize enhancement modules
            self.multi_factor_scorer = MultiFactorScorer()
            self.freshness_tracker = SignalFreshnessTracker()
            self.performance_tracker = PerformanceAttribution()

            self.patterns_initialized = True
            logger.info("Enhanced signal generator initialized with pattern detection")

    async def generate_enhanced_signal(
        self,
        market_data: Dict[str, Any],
        all_markets: Optional[List[Dict]] = None
    ) -> Optional[EnhancedSignal]:
        """
        Generate an enhanced signal with multi-factor analysis.

        Args:
            market_data: Market data including prices, liquidity, etc.
            all_markets: All markets for cross-market correlation analysis

        Returns:
            EnhancedSignal with multi-factor scoring or None
        """
        if not self.patterns_initialized:
            await self.initialize()

        market_id = market_data.get("market_id", "")
        if not market_id:
            return None

        # Step 1: Run pattern detection
        patterns = await self._detect_all_patterns(market_data, all_markets)

        # Step 2: Get edge data
        edge_data = self._extract_edge_data(market_data)

        # Step 3: Calculate composite score
        enhanced_signal = await self.multi_factor_scorer.calculate_composite_score(
            market_data, patterns, edge_data
        )

        if enhanced_signal:
            # Register signal for freshness tracking
            await self.freshness_tracker.register_signal(
                signal_id=f"signal_{market_id}_{datetime.now().timestamp()}",
                pattern_type="composite",
                market_id=market_id,
                created_at=enhanced_signal.generated_at
            )

            logger.info(f"Generated enhanced signal for {market_id} with score {enhanced_signal.composite_score:.2f}")

        return enhanced_signal

    async def generate_enhanced_batch_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[EnhancedSignal]:
        """Generate enhanced signals for multiple markets"""
        signals = []

        for market in markets:
            try:
                signal = await self.generate_enhanced_signal(market, markets)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating enhanced signal for market: {e}")

        return signals

    async def _detect_all_patterns(
        self,
        market_data: Dict[str, Any],
        all_markets: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Run all pattern detectors and return results"""
        patterns = []

        for detector_name, detector in self.pattern_detectors.items():
            try:
                if detector_name == "cross_market" and all_markets:
                    # Cross-market detector needs all markets
                    result = await detector.detect(market_data, None, all_markets)
                else:
                    result = await detector.detect(market_data)

                if result:
                    patterns.append(result.to_dict())

            except Exception as e:
                logger.error(f"Error in {detector_name} detector: {e}")

        return patterns

    def _extract_edge_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract edge calculation data from market data"""
        yes_price = market_data.get("yes_price", 0.5)

        # Calculate edge from market-implied probability
        edge_result = calculate_edge(
            confidence=yes_price,  # Market-implied probability as base confidence
            market_prob=yes_price
        )

        return {
            "value": edge_result.edge if edge_result else 0,
            "confidence": yes_price,
            "signal": "BUY" if yes_price > 0.5 else "SELL",
            "strength": edge_result.strength.value if edge_result else "NONE"
        }

    async def get_active_enhanced_signals(
        self,
        min_composite_score: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Get all active enhanced signals above minimum score"""
        if not self.patterns_initialized:
            await self.initialize()

        # Get all active signals from freshness tracker
        active_signals = await self.freshness_tracker.get_active_signals()

        # Filter by composite score and apply decay
        results = []
        for signal_info in active_signals:
            # Apply decay
            decayed_signal = await self.freshness_tracker.apply_decay_to_signal(
                signal_info,
                "composite"
            )

            if decayed_signal["composite_score"] >= min_composite_score:
                results.append(decayed_signal)

        # Sort by composite score descending
        results.sort(key=lambda x: x["composite_score"], reverse=True)
        return results

    async def get_factor_attribution(self, market_id: str) -> Dict[str, Any]:
        """Get factor attribution for a specific market"""
        if not self.patterns_initialized:
            await self.initialize()

        # Get the latest enhanced signal for this market
        signals = await self.get_active_enhanced_signals()
        market_signals = [s for s in signals if s["market_id"] == market_id]

        if not market_signals:
            return {}

        latest_signal = market_signals[0]

        # Convert to EnhancedSignal object for attribution
        enhanced = EnhancedSignal(
            market_id=latest_signal["market_id"],
            direction=latest_signal["direction"],
            composite_score=latest_signal["composite_score"],
            confidence=latest_signal["confidence"],
            factor_scores=[],  # Would need to reconstruct from latest_signal
            strength_level=latest_signal["strength_level"],
            signal_age_seconds=latest_signal["signal_age_seconds"],
            is_active=latest_signal["is_active"],
            generated_at=datetime.fromisoformat(latest_signal["generated_at"])
        )

        return await self.multi_factor_scorer.factor_attribution(enhanced)

    async def record_pattern_outcome(
        self,
        signal_id: str,
        pattern_type: str,
        market_id: str,
        entry_price: float,
        exit_price: float
    ) -> None:
        """Record the outcome of a pattern-based signal"""
        if not self.patterns_initialized:
            await self.initialize()

        from analytics.pattern_enhancement.performance_attribution import OutcomeType

        # Calculate PnL
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100

        outcome = OutcomeType.SUCCESS if pnl_percent > 0 else OutcomeType.FAILURE

        await self.performance_tracker.record_signal_outcome(
            signal_id=signal_id,
            market_id=market_id,
            pattern_type=pattern_type,
            direction="LONG",  # Simplified
            entry_price=entry_price,
            exit_price=exit_price,
            outcome=outcome,
            pnl=pnl_percent
        )

        logger.info(f"Recorded outcome for {signal_id}: {outcome.value} ({pnl_percent:.2f}%)")

    async def get_pattern_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics by pattern type"""
        if not self.patterns_initialized:
            await self.initialize()

        return await self.performance_tracker.get_all_performance()

    async def cleanup_old_data(self, hours: int = 24) -> Dict[str, int]:
        """Clean up old signals and patterns"""
        if not self.patterns_initialized:
            await self.initialize()

        # Clean up old signals
        removed_signals = await self.freshness_tracker.cleanup_expired(hours)

        # Clean up old generated signals from base class
        self.clear_old_signals(hours)

        return {
            "signals_removed": removed_signals,
            "total_patterns_cleaned": len(self.generated_signals)
        }


# Global enhanced signal generator instance
_enhanced_signal_generator: Optional[MultiFactorSignalGenerator] = None


async def get_enhanced_signal_generator() -> MultiFactorSignalGenerator:
    """Get or create the enhanced signal generator"""
    global _enhanced_signal_generator
    if _enhanced_signal_generator is None:
        _enhanced_signal_generator = MultiFactorSignalGenerator()
        await _enhanced_signal_generator.initialize()
    return _enhanced_signal_generator
