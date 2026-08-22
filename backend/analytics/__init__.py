"""
Analytics module for Polymarket Analytics Platform.

Contains modules for:
- Edge calculation
- Confidence analytics
- ROI calculation
- Signal analysis
- Pattern detection (Phase 4)
- ML/AI predictions (Phase 5)
- Strategy evolution (Phase 5)
"""

from .edge_calculator import (
    EdgeStrength,
    EdgeResult,
    calculate_edge,
    calculate_edge_from_prices,
    filter_by_edge
)

# ML Engine exports
from .ml_engine import (
    MLEngine,
    MarketOutcomeClassifier,
    PriceMovementPredictor,
    LiquidityForecaster,
    MarketSimilarityEmbedding,
    OutcomePrediction,
    PricePrediction,
    LiquidityForecast,
    MarketSimilarity,
    get_ml_engine
)

# Strategy Evolution exports
from .strategy_evolution import (
    StrategyEvolutionSystem,
    GeneticAlgorithmOptimizer,
    ABTestManager,
    MetaStrategySelector,
    StrategyParameters,
    StrategyPerformance,
    EvolvedStrategy,
    StrategyStatus,
    StrategyType,
    get_strategy_evolution_system
)

__all__ = [
    # Edge calculation
    "EdgeStrength",
    "EdgeResult",
    "calculate_edge",
    "calculate_edge_from_prices",
    "filter_by_edge",

    # ML Engine
    "MLEngine",
    "MarketOutcomeClassifier",
    "PriceMovementPredictor",
    "LiquidityForecaster",
    "MarketSimilarityEmbedding",
    "OutcomePrediction",
    "PricePrediction",
    "LiquidityForecast",
    "MarketSimilarity",
    "get_ml_engine",

    # Strategy Evolution
    "StrategyEvolutionSystem",
    "GeneticAlgorithmOptimizer",
    "ABTestManager",
    "MetaStrategySelector",
    "StrategyParameters",
    "StrategyPerformance",
    "EvolvedStrategy",
    "StrategyStatus",
    "StrategyType",
    "get_strategy_evolution_system"
]
