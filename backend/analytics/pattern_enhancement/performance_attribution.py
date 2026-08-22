"""
Performance Attribution

Tracks and analyzes signal performance to improve future predictions.
Attributes wins/losses to specific factors and patterns.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """Signal outcome types"""
    SUCCESS = "SUCCESS"  # Signal was profitable
    FAILURE = "FAILURE"  # Signal was not profitable
    PENDING = "PENDING"  # Signal still active
    CANCELLED = "CANCELLED"  # Signal was cancelled


@dataclass
class SignalOutcome:
    """Result of a signal"""
    signal_id: str
    market_id: str
    pattern_type: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    outcome: OutcomeType
    pnl: Optional[float]
    pnl_percent: Optional[float]
    hold_duration_hours: Optional[int]
    resolved_at: Optional[datetime]
    metadata: Dict[str, Any]


class PerformanceAttribution:
    """
    Tracks signal performance and attributes results to factors.

    Uses historical performance to:
    - Identify which patterns/factors are most predictive
    - Calculate win rates by pattern type
    - Optimize factor weights
    """

    def __init__(self):
        # Store signal outcomes
        self.signal_outcomes: Dict[str, SignalOutcome] = {}

        # Performance metrics by pattern type
        self.pattern_performance: Dict[str, Dict] = defaultdict(lambda: {
            "total_signals": 0,
            "successful": 0,
            "failed": 0,
            "pending": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "avg_pnl_percent": 0.0
        })

        # Factor-level performance
        self.factor_performance: Dict[str, Dict] = defaultdict(lambda: {
            "times_applied": 0,
            "successful": 0,
            "win_rate": 0.0
        })

    async def record_signal_outcome(
        self,
        signal_id: str,
        market_id: str,
        pattern_type: str,
        direction: str,
        entry_price: float,
        exit_price: Optional[float],
        outcome: OutcomeType,
        pnl: Optional[float] = None,
        hold_duration_hours: Optional[int] = None
    ) -> None:
        """Record the outcome of a signal"""
        outcome_obj = SignalOutcome(
            signal_id=signal_id,
            market_id=market_id,
            pattern_type=pattern_type,
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            outcome=outcome,
            pnl=pnl,
            pnl_percent=self._calculate_pnl_percent(entry_price, exit_price, direction),
            hold_duration_hours=hold_duration_hours,
            resolved_at=datetime.now() if outcome != OutcomeType.PENDING else None,
            metadata={}
        )

        self.signal_outcomes[signal_id] = outcome_obj
        self._update_pattern_stats(pattern_type, outcome_obj)
        logger.info(f"Recorded signal outcome: {signal_id} - {outcome.value}")

    def _calculate_pnl_percent(self, entry: float, exit: float, direction: str) -> Optional[float]:
        """Calculate PnL percentage"""
        if not exit or not entry or entry == 0:
            return None

        if direction == "LONG":
            return ((exit - entry) / entry) * 100
        elif direction == "SHORT":
            return ((entry - exit) / entry) * 100
        return None

    def _update_pattern_stats(self, pattern_type: str, outcome: SignalOutcome) -> None:
        """Update performance statistics for a pattern type"""
        stats = self.pattern_performance[pattern_type]
        stats["total_signals"] += 1

        if outcome.outcome == OutcomeType.SUCCESS:
            stats["successful"] += 1
            stats["total_pnl"] += outcome.pnl_percent or 0
        elif outcome.outcome == OutcomeType.FAILURE:
            stats["failed"] += 1
            stats["total_pnl"] += outcome.pnl_percent or 0
        elif outcome.outcome == OutcomeType.PENDING:
            stats["pending"] += 1

        # Recalculate win rate
        total_resolved = stats["successful"] + stats["failed"]
        if total_resolved > 0:
            stats["win_rate"] = stats["successful"] / total_resolved
            stats["avg_pnl_percent"] = stats["total_pnl"] / total_resolved

    async def get_pattern_performance(self, pattern_type: str) -> Dict[str, Any]:
        """Get performance metrics for a specific pattern type"""
        return self.pattern_performance.get(pattern_type, {
            "total_signals": 0,
            "successful": 0,
            "failed": 0,
            "pending": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "avg_pnl_percent": 0.0
        })

    async def get_all_performance(self) -> Dict[str, Dict]:
        """Get performance metrics for all pattern types"""
        return dict(self.pattern_performance)

    async def get_top_performing_patterns(self, min_signals: int = 10) -> List[Dict]:
        """Get patterns ranked by performance"""
        results = []

        for pattern_type, stats in self.pattern_performance.items():
            total_signals = stats["total_signals"]
            if total_signals < min_signals:
                continue

            results.append({
                "pattern_type": pattern_type,
                "total_signals": total_signals,
                "win_rate": stats["win_rate"],
                "avg_pnl_percent": stats["avg_pnl_percent"],
                "profit_factor": self._calculate_profit_factor(stats)
            })

        # Sort by win rate
        results.sort(key=lambda x: x["win_rate"], reverse=True)
        return results

    def _calculate_profit_factor(self, stats: Dict) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        # This would require more detailed PnL tracking
        # Simplified version using avg PnL
        if stats["avg_pnl_percent"] > 0:
            return stats["avg_pnl_percent"]
        return 0.0

    async def get_recent_performance(
        self,
        hours: int = 24,
        pattern_type: Optional[str] = None
    ) -> List[SignalOutcome]:
        """Get recent signal outcomes"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_outcomes = []

        for outcome in self.signal_outcomes.values():
            if outcome.resolved_at and outcome.resolved_at >= cutoff:
                if pattern_type is None or outcome.pattern_type == pattern_type:
                    recent_outcomes.append(outcome)

        return recent_outcomes

    async def calculate_confidence_adjustment(
        self,
        pattern_type: str,
        base_confidence: float
    ) -> float:
        """
        Adjust confidence based on historical performance.

        If a pattern has high win rate, boost confidence.
        If low win rate, reduce confidence.
        """
        stats = await self.get_pattern_performance(pattern_type)
        win_rate = stats.get("win_rate", 0.5)
        total_signals = stats.get("total_signals", 0)

        if total_signals < 10:
            # Not enough data, don't adjust
            return base_confidence

        # Adjustment formula: confidence * (0.5 + win_rate) / 1.5
        # This scales confidence based on how much win rate deviates from 0.5
        adjustment_factor = (0.5 + win_rate) / 1.5
        adjusted_confidence = min(base_confidence * adjustment_factor, 1.0)

        return adjusted_confidence
