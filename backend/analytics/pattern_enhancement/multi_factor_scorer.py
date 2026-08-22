"""
Multi-Factor Signal Scorer

Combines multiple pattern signals into weighted composite scores.
Provides factor attribution for explainability.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FactorType(Enum):
    """Factor types for multi-factor scoring"""
    EDGE = "edge"
    MOMENTUM_REVERSAL = "momentum_reversal"
    LIQUIDITY_TRAP = "liquidity_trap"
    CROSS_MARKET = "cross_market"
    RESOLUTION_PROBABILITY = "resolution_prob"
    SENTIMENT = "sentiment"


@dataclass
class FactorScore:
    """Score for a single factor"""
    factor_type: FactorType
    raw_score: float  # 0 to 1
    weight: float  # Weight in composite score
    weighted_score: float  # raw_score * weight
    direction: str  # "LONG", "SHORT", "NEUTRAL"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedSignal:
    """Enhanced trading signal with multi-factor analysis"""
    market_id: str
    direction: str  # "LONG", "SHORT", "NEUTRAL"
    composite_score: float  # 0 to 1
    confidence: float  # 0 to 1
    factor_scores: List[FactorScore]
    strength_level: str  # "WEAK", "MODERATE", "STRONG", "VERY_STRONG", "EXTREME"
    signal_age_seconds: int
    is_active: bool
    generated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "market_id": self.market_id,
            "direction": self.direction,
            "composite_score": self.composite_score,
            "confidence": self.confidence,
            "factor_scores": [
                {
                    "factor_type": fs.factor_type.value,
                    "raw_score": fs.raw_score,
                    "weight": fs.weight,
                    "weighted_score": fs.weighted_score,
                    "direction": fs.direction,
                    "metadata": fs.metadata
                }
                for fs in self.factor_scores
            ],
            "strength_level": self.strength_level,
            "signal_age_seconds": self.signal_age_seconds,
            "is_active": self.is_active,
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata
        }


class MultiFactorScorer:
    """
    Combines multiple signals into weighted composite scores.

    Uses configurable factor weights and provides attribution
    for explainability of composite scores.
    """

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        # Default factor weights (sum = 1.0)
        self.factor_weights = {
            FactorType.EDGE.value: 0.30,
            FactorType.MOMENTUM_REVERSAL.value: 0.20,
            FactorType.LIQUIDITY_TRAP.value: 0.15,
            FactorType.CROSS_MARKET.value: 0.15,
            FactorType.RESOLUTION_PROBABILITY.value: 0.10,
            FactorType.SENTIMENT.value: 0.10
        }

        # Override with custom weights if provided
        if custom_weights:
            for factor, weight in custom_weights.items():
                if factor in self.factor_weights:
                    self.factor_weights[factor] = weight

        # Minimum composite score threshold
        self.min_composite_score = 0.6

    async def calculate_composite_score(
        self,
        market_data: Dict[str, Any],
        patterns: List[Dict],
        edge_data: Optional[Dict] = None
    ) -> Optional[EnhancedSignal]:
        """
        Calculate weighted composite score from multiple factors.

        Args:
            market_data: Current market data
            patterns: List of detected patterns
            edge_data: Edge calculation results

        Returns:
            EnhancedSignal with composite score or None if below threshold
        """
        market_id = market_data.get("market_id", "")
        if not market_id:
            return None

        factor_scores = []

        # 1. Edge factor (from existing edge calculation)
        if edge_data:
            edge_factor = self._score_edge_factor(edge_data)
            if edge_factor:
                factor_scores.append(edge_factor)

        # 2. Pattern factors
        for pattern in patterns:
            if not pattern.get("detected"):
                continue

            pattern_type = pattern.get("pattern_type")
            pattern_confidence = pattern.get("confidence", 0)
            pattern_direction = pattern.get("direction", "NEUTRAL")

            factor_score = FactorScore(
                factor_type=FactorType(pattern_type),
                raw_score=pattern_confidence,
                weight=self.factor_weights.get(pattern_type, 0.1),
                weighted_score=pattern_confidence * self.factor_weights.get(pattern_type, 0.1),
                direction=pattern_direction,
                metadata={
                    "strength": pattern.get("strength", ""),
                    "reasoning": pattern.get("metadata", {}).get("reasoning", "")
                }
            )
            factor_scores.append(factor_score)

        if not factor_scores:
            return None

        # Calculate composite score
        composite_score = sum(fs.weighted_score for fs in factor_scores)

        # Determine overall direction (weighted voting)
        long_weight = sum(fs.weighted_score for fs in factor_scores if fs.direction == "LONG")
        short_weight = sum(fs.weighted_score for fs in factor_scores if fs.direction == "SHORT")

        if long_weight > short_weight:
            direction = "LONG"
            confidence = min(composite_score * 1.5, 1.0)  # Boost confidence for directional agreement
        elif short_weight > long_weight:
            direction = "SHORT"
            confidence = min(composite_score * 1.5, 1.0)
        else:
            direction = "NEUTRAL"
            confidence = composite_score * 0.5  # Reduce confidence for neutral

        # Check minimum score threshold
        if composite_score < self.min_composite_score:
            return None

        # Determine strength level
        strength_level = self._calculate_strength_level(composite_score)

        return EnhancedSignal(
            market_id=market_id,
            direction=direction,
            composite_score=composite_score,
            confidence=confidence,
            factor_scores=factor_scores,
            strength_level=strength_level,
            signal_age_seconds=0,
            is_active=True,
            generated_at=datetime.now(),
            metadata={
                "total_factors": len(factor_scores),
                "long_weight": long_weight,
                "short_weight": short_weight
            }
        )

    def _score_edge_factor(self, edge_data: Dict) -> Optional[FactorScore]:
        """Score the edge factor"""
        edge_value = edge_data.get("value", 0)
        edge_confidence = edge_data.get("confidence", 0)
        edge_signal = edge_data.get("signal", "NEUTRAL")

        # Convert edge to score (0-1)
        edge_score = min(abs(edge_value) * 10, 1.0)

        # Determine direction from edge signal
        if edge_signal == "BUY":
            direction = "LONG"
        elif edge_signal == "SELL":
            direction = "SHORT"
        else:
            direction = "NEUTRAL"

        return FactorScore(
            factor_type=FactorType.EDGE,
            raw_score=edge_score,
            weight=self.factor_weights[FactorType.EDGE.value],
            weighted_score=edge_score * self.factor_weights[FactorType.EDGE.value],
            direction=direction,
            metadata={
                "edge_value": edge_value,
                "edge_strength": edge_data.get("strength", "")
            }
        )

    def _calculate_strength_level(self, composite_score: float) -> str:
        """Calculate strength level from composite score"""
        if composite_score >= 0.9:
            return "EXTREME"
        elif composite_score >= 0.8:
            return "VERY_STRONG"
        elif composite_score >= 0.7:
            return "STRONG"
        elif composite_score >= 0.6:
            return "MODERATE"
        else:
            return "WEAK"

    async def factor_attribution(self, enhanced_signal: EnhancedSignal) -> Dict[str, Any]:
        """
        Break down composite score by factor contribution.

        Returns attribution showing which factors contributed most.
        """
        if not enhanced_signal or not enhanced_signal.factor_scores:
            return {}

        # Sort factors by contribution
        sorted_factors = sorted(
            enhanced_signal.factor_scores,
            key=lambda fs: fs.weighted_score,
            reverse=True
        )

        # Calculate attribution percentages
        total_weighted_score = sum(fs.weighted_score for fs in sorted_factors)
        if total_weighted_score == 0:
            return {}

        attribution = {}
        for fs in sorted_factors:
            contribution = (fs.weighted_score / total_weighted_score) * 100
            attribution[fs.factor_type.value] = {
                "contribution_percent": contribution,
                "raw_score": fs.raw_score,
                "direction": fs.direction,
                "reasoning": fs.metadata.get("reasoning", "")
            }

        return {
            "market_id": enhanced_signal.market_id,
            "composite_score": enhanced_signal.composite_score,
            "direction": enhanced_signal.direction,
            "factor_attribution": attribution,
            "top_factor": sorted_factors[0].factor_type.value if sorted_factors else None
        }

    async def score_batch(
        self,
        market_list: List[Dict[str, Any]],
        patterns_map: Dict[str, List[Dict]],
        edge_map: Dict[str, Dict]
    ) -> List[EnhancedSignal]:
        """
        Calculate composite scores for multiple markets.

        Args:
            market_list: List of market data
            patterns_map: Map of market_id to list of patterns
            edge_map: Map of market_id to edge data

        Returns:
            List of EnhancedSignal objects
        """
        results = []

        for market in market_list:
            market_id = market.get("market_id", "")
            patterns = patterns_map.get(market_id, [])
            edge = edge_map.get(market_id)

            signal = await self.calculate_composite_score(market, patterns, edge)
            if signal:
                results.append(signal)

        return results
