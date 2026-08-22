"""
Pattern Enhancement Module

Enhances signals with multi-factor scoring, freshness tracking, and performance attribution.
"""

from .multi_factor_scorer import MultiFactorScorer, EnhancedSignal
from .freshness_tracker import SignalFreshnessTracker, FreshnessLevel
from .performance_attribution import PerformanceAttribution, OutcomeType

__all__ = [
    'MultiFactorScorer',
    'EnhancedSignal',
    'SignalFreshnessTracker',
    'FreshnessLevel',
    'PerformanceAttribution',
    'OutcomeType',
]
