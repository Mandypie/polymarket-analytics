"""
Pattern Detection Module

Detects trading patterns in market data for signal generation.
"""

from .base_detector import BaseDetector, PatternResult
from .momentum_reversal import MomentumReversalDetector
from .liquidity_trap import LiquidityTrapDetector
from .cross_market_correlation import CrossMarketCorrelationDetector
from .resolution_probability import ResolutionProbabilityDetector
from .sentiment_analyzer import SentimentAnalyzer

__all__ = [
    'BaseDetector',
    'PatternResult',
    'MomentumReversalDetector',
    'LiquidityTrapDetector',
    'CrossMarketCorrelationDetector',
    'ResolutionProbabilityDetector',
    'SentimentAnalyzer',
]
