"""
Backtesting Engine

Simulates trading strategies against historical data to evaluate performance.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .strategy import Strategy, TradingSignal, SignalType, StrategyConfig, create_strategy
from .metrics import calculate_metrics, PerformanceMetrics

logger = logging.getLogger(__name__)


class BacktestStatus(Enum):
    """Backtest execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Trade:
    """A simulated trade"""
    market_id: str
    signal: TradingSignal
    entry_price: float
    entry_time: datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    status: str = "OPEN"  # OPEN, CLOSED
    pnl: float = 0.0
    fees: float = 0.0

    def close_trade(self, exit_price: float, exit_time: datetime, fee_rate: float = 0.005) -> None:
        """Close the trade and calculate PnL"""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.status = "CLOSED"

        # Calculate PnL based on signal type
        if self.signal.signal_type == SignalType.BUY:
            # Bought YES, profit if price increased
            self.pnl = (exit_price - self.entry_price) * self.signal.size
        elif self.signal.signal_type == SignalType.SELL:
            # Sold YES (bought NO), profit if price decreased
            self.pnl = (self.entry_price - exit_price) * self.signal.size
        else:
            self.pnl = 0.0

        # Apply fees
        self.fees = (self.entry_price * self.signal.size * fee_rate) + \
                    (exit_price * self.signal.size * fee_rate)
        self.pnl -= self.fees

    def get_duration(self) -> Optional[timedelta]:
        """Get trade duration"""
        if self.exit_time and self.entry_time:
            return self.exit_time - self.entry_time
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary"""
        return {
            "market_id": self.market_id,
            "signal_type": self.signal.signal_type.value,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat(),
            "exit_price": self.exit_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "status": self.status,
            "pnl": self.pnl,
            "fees": self.fees,
            "size": self.signal.size,
            "duration_hours": self.get_duration().total_seconds() / 3600 if self.get_duration() else None
        }


@dataclass
class BacktestConfig:
    """Configuration for backtest"""
    strategy_config: StrategyConfig
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    fee_rate: float = 0.005
    max_position_size: float = 1000.0
    max_open_positions: int = 10
    allow_shorting: bool = True
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None


@dataclass
class BacktestResult:
    """Results of a backtest"""
    config: BacktestConfig
    status: BacktestStatus
    trades: List[Trade] = field(default_factory=list)
    metrics: Optional[PerformanceMetrics] = None
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "strategy_name": self.config.strategy_config.name,
            "strategy_type": self.config.strategy_config.strategy_type.value,
            "status": self.status.value,
            "period": {
                "start": self.config.start_date.isoformat(),
                "end": self.config.end_date.isoformat()
            },
            "config": {
                "initial_capital": self.config.initial_capital,
                "fee_rate": self.config.fee_rate,
                "max_position_size": self.config.max_position_size,
                "max_open_positions": self.config.max_open_positions
            },
            "summary": {
                "total_trades": len(self.trades),
                "closed_trades": len([t for t in self.trades if t.status == "CLOSED"]),
                "open_trades": len([t for t in self.trades if t.status == "OPEN"])
            },
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "equity_curve": self.equity_curve,
            "trades": [t.to_dict() for t in self.trades],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        }


class Backtester:
    """Backtesting engine for strategy evaluation"""

    def __init__(self):
        self.active_backtests: Dict[str, BacktestResult] = {}
        self.results_history: List[BacktestResult] = []

    async def run_backtest(
        self,
        config: BacktestConfig,
        historical_data: List[Dict[str, Any]]
    ) -> BacktestResult:
        """Run a backtest with the given configuration

        Args:
            config: Backtest configuration
            historical_data: List of historical market data points

        Returns:
            BacktestResult with trades and metrics
        """
        backtest_id = f"{config.strategy_config.name}_{config.start_date.strftime('%Y%m%d')}"

        logger.info(f"Starting backtest: {backtest_id}")

        # Create result object
        result = BacktestResult(
            config=config,
            status=BacktestStatus.RUNNING,
            started_at=datetime.now()
        )

        try:
            # Initialize strategy
            strategy = create_strategy(config.strategy_config)

            # Track state
            capital = config.initial_capital
            open_trades: List[Trade] = []
            equity_curve = []

            # Process historical data
            for data_point in historical_data:
                timestamp = data_point.get("timestamp")

                # Check stop loss / take profit on existing trades
                for trade in open_trades[:]:  # Copy list to modify during iteration
                    current_price = data_point.get("yes_price")
                    if not current_price:
                        continue

                    # Check stop loss
                    if config.stop_loss_pct:
                        if trade.signal.signal_type == SignalType.BUY:
                            loss_pct = (trade.entry_price - current_price) / trade.entry_price
                        else:
                            loss_pct = (current_price - trade.entry_price) / trade.entry_price

                        if loss_pct >= config.stop_loss_pct:
                            trade.close_trade(current_price, timestamp, config.fee_rate)
                            open_trades.remove(trade)
                            capital += trade.pnl
                            continue

                    # Check take profit
                    if config.take_profit_pct:
                        if trade.signal.signal_type == SignalType.BUY:
                            profit_pct = (current_price - trade.entry_price) / trade.entry_price
                        else:
                            profit_pct = (trade.entry_price - current_price) / trade.entry_price

                        if profit_pct >= config.take_profit_pct:
                            trade.close_trade(current_price, timestamp, config.fee_rate)
                            open_trades.remove(trade)
                            capital += trade.pnl
                            continue

                # Generate signal from strategy
                signal = strategy.analyze_market(data_point)

                if signal and strategy.validate_signal(signal):
                    # Check if we can open new position
                    if len(open_trades) < config.max_open_positions:
                        # Check if already have position in this market
                        if not any(t.market_id == signal.market_id for t in open_trades):
                            trade = Trade(
                                market_id=signal.market_id,
                                signal=signal,
                                entry_price=signal.price,
                                entry_time=timestamp
                            )
                            open_trades.append(trade)
                            strategy.add_signal(signal)

                # Record equity
                unrealized_pnl = sum(
                    (data_point.get("yes_price", 0) - t.entry_price) * t.signal.size
                    if t.signal.signal_type == SignalType.BUY else
                    (t.entry_price - data_point.get("yes_price", 0)) * t.signal.size
                    for t in open_trades
                )
                total_equity = capital + unrealized_pnl

                equity_curve.append({
                    "timestamp": timestamp.isoformat(),
                    "capital": capital,
                    "unrealized_pnl": unrealized_pnl,
                    "total_equity": total_equity,
                    "open_positions": len(open_trades)
                })

            # Close remaining open trades at last price
            if historical_data:
                last_price = historical_data[-1].get("yes_price")
                last_time = historical_data[-1].get("timestamp")

                for trade in open_trades:
                    if last_price:
                        trade.close_trade(last_price, last_time, config.fee_rate)
                        capital += trade.pnl

            # Store trades
            result.trades = open_trades

            # Calculate metrics
            closed_trades = [t for t in result.trades if t.status == "CLOSED"]
            if closed_trades:
                result.metrics = calculate_metrics(
                    trades=closed_trades,
                    initial_capital=config.initial_capital,
                    equity_curve=equity_curve
                )

            result.equity_curve = equity_curve
            result.status = BacktestStatus.COMPLETED
            result.completed_at = datetime.now()

            logger.info(f"Backtest completed: {backtest_id} - ROI: {result.metrics.total_return_pct:.2f}%")

        except Exception as e:
            logger.error(f"Backtest failed: {backtest_id} - Error: {e}")
            result.status = BacktestStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now()

        # Store result
        self.active_backtests[backtest_id] = result
        self.results_history.append(result)

        return result

    def get_backtest_result(self, backtest_id: str) -> Optional[BacktestResult]:
        """Get result of a backtest by ID"""
        return self.active_backtests.get(backtest_id)

    def get_all_results(self) -> List[BacktestResult]:
        """Get all backtest results"""
        return self.results_history

    def compare_strategies(
        self,
        backtest_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Compare multiple backtest results

        Returns:
            Dictionary comparing metrics across strategies
        """
        comparison = {}

        for bid in backtest_ids:
            result = self.get_backtest_result(bid)
            if result and result.metrics:
                comparison[bid] = {
                    "strategy": result.config.strategy_config.name,
                    "total_return_pct": result.metrics.total_return_pct,
                    "sharpe_ratio": result.metrics.sharpe_ratio,
                    "max_drawdown_pct": result.metrics.max_drawdown_pct,
                    "win_rate_pct": result.metrics.win_rate_pct,
                    "total_trades": len(result.trades)
                }

        return comparison


# Global backtester instance
_backtester: Optional[Backtester] = None


def get_backtester() -> Backtester:
    """Get or create the backtester instance"""
    global _backtester
    if _backtester is None:
        _backtester = Backtester()
    return _backtester
