"""
Performance Metrics Calculation

Calculates key performance metrics for backtesting results.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import math


@dataclass
class PerformanceMetrics:
    """Performance metrics for a backtest or trading strategy"""
    # Return metrics
    total_return: float
    total_return_pct: float
    annualized_return_pct: float

    # Risk metrics
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    volatility: float

    # Trading metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    win_rate_pct: float

    # PnL metrics
    total_pnl: float
    avg_pnl_per_trade: float
    avg_win_pnl: float
    avg_loss_pnl: float
    profit_factor: float

    # Additional metrics
    avg_trade_duration_hours: float
    best_trade_pnl: float
    worst_trade_pnl: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "returns": {
                "total_return": self.total_return,
                "total_return_pct": self.total_return_pct,
                "annualized_return_pct": self.annualized_return_pct
            },
            "risk": {
                "max_drawdown": self.max_drawdown,
                "max_drawdown_pct": self.max_drawdown_pct,
                "sharpe_ratio": self.sharpe_ratio,
                "sortino_ratio": self.sortino_ratio,
                "volatility": self.volatility
            },
            "trading": {
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "win_rate": self.win_rate,
                "win_rate_pct": self.win_rate_pct
            },
            "pnl": {
                "total_pnl": self.total_pnl,
                "avg_pnl_per_trade": self.avg_pnl_per_trade,
                "avg_win_pnl": self.avg_win_pnl,
                "avg_loss_pnl": self.avg_loss_pnl,
                "profit_factor": self.profit_factor
            },
            "additional": {
                "avg_trade_duration_hours": self.avg_trade_duration_hours,
                "best_trade_pnl": self.best_trade_pnl,
                "worst_trade_pnl": self.worst_trade_pnl
            }
        }


def calculate_metrics(
    trades: List[Any],
    initial_capital: float,
    equity_curve: Optional[List[Dict[str, Any]]] = None
) -> PerformanceMetrics:
    """Calculate performance metrics from trades

    Args:
        trades: List of Trade objects
        initial_capital: Starting capital for the backtest
        equity_curve: Optional equity curve data for advanced metrics

    Returns:
        PerformanceMetrics object with calculated metrics
    """

    if not trades:
        return PerformanceMetrics(
            total_return=0.0,
            total_return_pct=0.0,
            annualized_return_pct=0.0,
            max_drawdown=0.0,
            max_drawdown_pct=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            volatility=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            win_rate_pct=0.0,
            total_pnl=0.0,
            avg_pnl_per_trade=0.0,
            avg_win_pnl=0.0,
            avg_loss_pnl=0.0,
            profit_factor=0.0,
            avg_trade_duration_hours=0.0,
            best_trade_pnl=0.0,
            worst_trade_pnl=0.0
        )

    # Calculate basic PnL metrics
    total_pnl = sum(trade.pnl for trade in trades)
    total_return = total_pnl
    total_return_pct = (total_pnl / initial_capital) * 100 if initial_capital > 0 else 0

    # Calculate win/loss metrics
    winning_trades = [t for t in trades if t.pnl > 0]
    losing_trades = [t for t in trades if t.pnl < 0]

    total_trades = len(trades)
    num_winning = len(winning_trades)
    num_losing = len(losing_trades)

    win_rate = num_winning / total_trades if total_trades > 0 else 0
    win_rate_pct = win_rate * 100

    # Average PnL metrics
    avg_pnl_per_trade = total_pnl / total_trades if total_trades > 0 else 0
    avg_win_pnl = sum(t.pnl for t in winning_trades) / num_winning if num_winning > 0 else 0
    avg_loss_pnl = sum(t.pnl for t in losing_trades) / num_losing if num_losing > 0 else 0

    # Profit factor (gross wins / gross losses)
    gross_wins = sum(t.pnl for t in winning_trades)
    gross_losses = abs(sum(t.pnl for t in losing_trades))
    profit_factor = gross_wins / gross_losses if gross_losses > 0 else 0

    # Best and worst trades
    best_trade_pnl = max((t.pnl for t in trades), default=0)
    worst_trade_pnl = min((t.pnl for t in trades), default=0)

    # Average trade duration
    durations = []
    for trade in trades:
        duration = trade.get_duration()
        if duration:
            durations.append(duration.total_seconds() / 3600)  # Convert to hours

    avg_trade_duration_hours = sum(durations) / len(durations) if durations else 0

    # Calculate max drawdown from equity curve
    max_drawdown = 0.0
    max_drawdown_pct = 0.0
    volatility = 0.0
    sharpe_ratio = 0.0
    sortino_ratio = 0.0
    annualized_return_pct = 0.0

    if equity_curve and len(equity_curve) > 1:
        equity_values = [point["total_equity"] for point in equity_curve]
        peak = equity_values[0]

        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = peak - value
            drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct

        # Calculate volatility (standard deviation of returns)
        returns = []
        for i in range(1, len(equity_values)):
            if equity_values[i - 1] > 0:
                returns.append((equity_values[i] - equity_values[i - 1]) / equity_values[i - 1])

        if returns:
            volatility = math.sqrt(sum(r ** 2 for r in returns) / len(returns)) * 100

        # Calculate Sharpe ratio (assuming risk-free rate of 0)
        if volatility > 0:
            # Annualize the metrics (assuming daily data)
            trading_days = len(returns)
            annualized_return_pct = total_return_pct * (365 / trading_days) if trading_days > 0 else 0
            annualized_volatility = volatility * math.sqrt(365)
            sharpe_ratio = annualized_return_pct / annualized_volatility if annualized_volatility > 0 else 0

            # Calculate Sortino ratio (downside deviation only)
            negative_returns = [r for r in returns if r < 0]
            if negative_returns:
                downside_deviation = math.sqrt(sum(r ** 2 for r in negative_returns) / len(negative_returns))
                annualized_downside = downside_deviation * math.sqrt(365) * 100
                sortino_ratio = annualized_return_pct / annualized_downside if annualized_downside > 0 else 0

    return PerformanceMetrics(
        total_return=total_return,
        total_return_pct=total_return_pct,
        annualized_return_pct=annualized_return_pct,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        volatility=volatility,
        total_trades=total_trades,
        winning_trades=num_winning,
        losing_trades=num_losing,
        win_rate=win_rate,
        win_rate_pct=win_rate_pct,
        total_pnl=total_pnl,
        avg_pnl_per_trade=avg_pnl_per_trade,
        avg_win_pnl=avg_win_pnl,
        avg_loss_pnl=avg_loss_pnl,
        profit_factor=profit_factor,
        avg_trade_duration_hours=avg_trade_duration_hours,
        best_trade_pnl=best_trade_pnl,
        worst_trade_pnl=worst_trade_pnl
    )


def calculate_roi_metrics(initial_capital: float, final_capital: float, days: int) -> Dict[str, float]:
    """Calculate ROI-related metrics

    Args:
        initial_capital: Starting capital
        final_capital: Ending capital
        days: Number of days in the period

    Returns:
        Dictionary with ROI metrics
    """
    total_return = final_capital - initial_capital
    total_return_pct = (total_return / initial_capital * 100) if initial_capital > 0 else 0

    # Annualized return
    if days > 0:
        years = days / 365
        annualized_return_pct = ((final_capital / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
    else:
        annualized_return_pct = 0

    return {
        "total_return": total_return,
        "total_return_pct": total_return_pct,
        "annualized_return_pct": annualized_return_pct
    }


def calculate_drawdown_metrics(equity_curve: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate detailed drawdown metrics

    Args:
        equity_curve: List of equity snapshots

    Returns:
        Dictionary with drawdown metrics
    """
    if not equity_curve:
        return {
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "avg_drawdown": 0.0,
            "drawdown_duration_days": 0
        }

    equity_values = [point["total_equity"] for point in equity_curve]
    timestamps = [point.get("timestamp", "") for point in equity_curve]

    peak = equity_values[0]
    peak_idx = 0
    max_drawdown = 0.0
    max_drawdown_pct = 0.0
    drawdowns = []
    drawdown_start_idx = None

    for i, value in enumerate(equity_values):
        if value > peak:
            peak = value
            peak_idx = i
            drawdown_start_idx = None
        else:
            if drawdown_start_idx is None:
                drawdown_start_idx = peak_idx

            drawdown = peak - value
            drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0
            drawdowns.append(drawdown)

            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct

    avg_drawdown = sum(drawdowns) / len(drawdowns) if drawdowns else 0

    return {
        "max_drawdown": max_drawdown,
        "max_drawdown_pct": max_drawdown_pct,
        "avg_drawdown": avg_drawdown,
        "num_drawdown_periods": len(drawdowns)
    }


def format_metrics_summary(metrics: PerformanceMetrics) -> str:
    """Format metrics as a readable summary string

    Args:
        metrics: PerformanceMetrics object

    Returns:
        Formatted string summary
    """
    summary = f"""
Performance Summary
===================
Return Metrics:
  Total Return: {metrics.total_return_pct:.2f}%
  Annualized Return: {metrics.annualized_return_pct:.2f}%

Risk Metrics:
  Max Drawdown: {metrics.max_drawdown_pct:.2f}%
  Sharpe Ratio: {metrics.sharpe_ratio:.2f}
  Sortino Ratio: {metrics.sortino_ratio:.2f}
  Volatility: {metrics.volatility:.2f}%

Trading Metrics:
  Total Trades: {metrics.total_trades}
  Win Rate: {metrics.win_rate_pct:.1f}%
  Winning Trades: {metrics.winning_trades}
  Losing Trades: {metrics.losing_trades}

PnL Metrics:
  Total PnL: ${metrics.total_pnl:.2f}
  Avg PnL/Trade: ${metrics.avg_pnl_per_trade:.2f}
  Avg Win: ${metrics.avg_win_pnl:.2f}
  Avg Loss: ${metrics.avg_loss_pnl:.2f}
  Profit Factor: {metrics.profit_factor:.2f}

Additional:
  Best Trade: ${metrics.best_trade_pnl:.2f}
  Worst Trade: ${metrics.worst_trade_pnl:.2f}
  Avg Duration: {metrics.avg_trade_duration_hours:.1f} hours
"""
    return summary
