"""
Backtesting Module

Provides strategy definition, backtesting engine, and performance metrics.
"""

from .strategy import (
    SignalType,
    StrategyType,
    TradingSignal,
    StrategyConfig,
    Strategy,
    EdgeBasedStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
    LiquidityStrategy,
    CombinedStrategy,
    create_strategy
)

from .backtester import (
    BacktestStatus,
    Trade,
    BacktestConfig,
    BacktestResult,
    Backtester,
    get_backtester
)

from .metrics import (
    PerformanceMetrics,
    calculate_metrics,
    calculate_roi_metrics,
    calculate_drawdown_metrics,
    format_metrics_summary
)

__all__ = [
    # Strategy exports
    "SignalType",
    "StrategyType",
    "TradingSignal",
    "StrategyConfig",
    "Strategy",
    "EdgeBasedStrategy",
    "MeanReversionStrategy",
    "MomentumStrategy",
    "LiquidityStrategy",
    "CombinedStrategy",
    "create_strategy",

    # Backtester exports
    "BacktestStatus",
    "Trade",
    "BacktestConfig",
    "BacktestResult",
    "Backtester",
    "get_backtester",

    # Metrics exports
    "PerformanceMetrics",
    "calculate_metrics",
    "calculate_roi_metrics",
    "calculate_drawdown_metrics",
    "format_metrics_summary"
]
