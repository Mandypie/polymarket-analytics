"""
Signal Freshness Tracker

Tracks signal age and applies time-based decay.
Ensures signals remain relevant and actionable.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class FreshnessLevel(Enum):
    """Signal freshness levels"""
    FRESH = "FRESH"           # < 5 minutes old
    RECENT = "RECENT"         # < 30 minutes old
    AGED = "AGED"             # < 2 hours old
    STALE = "STALE"           # < 6 hours old
    EXPIRED = "EXPIRED"       # >= 6 hours old


@dataclass
class FreshnessInfo:
    """Freshness information for a signal"""
    signal_id: str
    created_at: datetime
    last_updated: datetime
    current_age_seconds: int
    freshness_level: FreshnessLevel
    decay_factor: float  # 0 to 1 (1 = fresh, 0 = fully decayed)
    is_active: bool


class SignalFreshnessTracker:
    """
    Tracks signal freshness and applies time-based decay.

    Different pattern types decay at different rates based on
    how quickly market conditions change.
    """

    def __init__(self):
        # Freshness decay rates per pattern type (per hour)
        self.decay_rates = {
            "momentum_reversal": 0.15,    # 15% decay per hour (fast-changing)
            "liquidity_trap": 0.08,        # 8% decay per hour
            "cross_market": 0.12,          # 12% decay per hour
            "resolution_prob": 0.05,       # 5% decay per hour (slow-changing)
            "sentiment": 0.10             # 10% decay per hour
        }

        # Freshness thresholds (in seconds)
        self.freshness_thresholds = {
            FreshnessLevel.FRESH: 300,      # 5 minutes
            FreshnessLevel.RECENT: 1800,    # 30 minutes
            FreshnessLevel.AGED: 7200,      # 2 hours
            FreshnessLevel.STALE: 21600     # 6 hours
        }

        # Track signals by pattern type and market
        self.signals_by_pattern: Dict[str, Dict[str, Dict]] = defaultdict(dict)
        # {pattern_type: {market_id: {signal_id: signal_data}}}

    async def register_signal(
        self,
        signal_id: str,
        pattern_type: str,
        market_id: str,
        created_at: datetime
    ) -> None:
        """Register a new signal for freshness tracking"""
        # Ensure nested defaultdict structure
        if pattern_type not in self.signals_by_pattern:
            self.signals_by_pattern[pattern_type] = defaultdict(dict)
        if market_id not in self.signals_by_pattern[pattern_type]:
            self.signals_by_pattern[pattern_type][market_id] = {}

        self.signals_by_pattern[pattern_type][market_id][signal_id] = {
            "created_at": created_at,
            "last_updated": created_at
        }

    async def update_freshness(self, signal_id: str, pattern_type: str, market_id: str) -> FreshnessInfo:
        """Update freshness for a signal"""
        signal_data = self.signals_by_pattern.get(pattern_type, {}).get(market_id, {}).get(signal_id)

        if not signal_data:
            return None

        created_at = signal_data["created_at"]
        now = datetime.now()
        age_seconds = int((now - created_at).total_seconds())

        # Determine freshness level
        freshness_level = self._determine_freshness_level(age_seconds)

        # Calculate decay factor
        decay_rate = self.decay_rates.get(pattern_type, 0.10)
        hours_old = age_seconds / 3600
        decay_factor = max(0, 1 - (decay_rate * hours_old))

        # Check if still active
        is_active = freshness_level != FreshnessLevel.EXPIRED

        return FreshnessInfo(
            signal_id=signal_id,
            created_at=created_at,
            last_updated=now,
            current_age_seconds=age_seconds,
            freshness_level=freshness_level,
            decay_factor=decay_factor,
            is_active=is_active
        )

    async def get_active_signals(
        self,
        pattern_type: Optional[str] = None,
        market_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active (non-expired) signals.

        Args:
            pattern_type: Filter by pattern type
            market_id: Filter by market ID

        Returns:
            List of active signal info
        """
        active_signals = []

        patterns_to_check = [pattern_type] if pattern_type else list(self.signals_by_pattern.keys())

        for pt in patterns_to_check:
            signals_by_market = self.signals_by_pattern.get(pt, {})

            markets_to_check = [market_id] if market_id else list(signals_by_market.keys())

            for mid in markets_to_check:
                signals = signals_by_market.get(mid, {})

                for signal_id, signal_data in signals.items():
                    created_at = signal_data["created_at"]
                    age_seconds = int((datetime.now() - created_at).total_seconds())
                    freshness = self._determine_freshness_level(age_seconds)

                    if freshness != FreshnessLevel.EXPIRED:
                        decay_rate = self.decay_rates.get(pt, 0.10)
                        decay_factor = max(0, 1 - (decay_rate * age_seconds / 3600))

                        active_signals.append({
                            "signal_id": signal_id,
                            "pattern_type": pt,
                            "market_id": mid,
                            "created_at": created_at.isoformat(),
                            "age_seconds": age_seconds,
                            "freshness_level": freshness.value,
                            "decay_factor": decay_factor
                        })

        return active_signals

    async def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """
        Remove expired signals from tracking.

        Args:
            max_age_hours: Maximum age to keep signals

        Returns:
            Number of signals removed
        """
        removed_count = 0
        cutoff = datetime.now() - timedelta(hours=max_age_hours)

        for pattern_type in list(self.signals_by_pattern.keys()):
            for market_id in list(self.signals_by_pattern[pattern_type].keys()):
                for signal_id in list(self.signals_by_pattern[pattern_type][market_id].keys()):
                    signal_data = self.signals_by_pattern[pattern_type][market_id][signal_id]
                    if signal_data["created_at"] < cutoff:
                        del self.signals_by_pattern[pattern_type][market_id][signal_id]
                        removed_count += 1

                # Clean up empty market dicts
                if not self.signals_by_pattern[pattern_type][market_id]:
                    del self.signals_by_pattern[pattern_type][market_id]

            # Clean up empty pattern type dicts
            if not self.signals_by_pattern[pattern_type]:
                del self.signals_by_pattern[pattern_type]

        logger.info(f"Cleaned up {removed_count} expired signals")
        return removed_count

    def _determine_freshness_level(self, age_seconds: int) -> FreshnessLevel:
        """Determine freshness level from age in seconds"""
        if age_seconds < self.freshness_thresholds[FreshnessLevel.FRESH]:
            return FreshnessLevel.FRESH
        elif age_seconds < self.freshness_thresholds[FreshnessLevel.RECENT]:
            return FreshnessLevel.RECENT
        elif age_seconds < self.freshness_thresholds[FreshnessLevel.AGED]:
            return FreshnessLevel.AGED
        elif age_seconds < self.freshness_thresholds[FreshnessLevel.STALE]:
            return FreshnessLevel.STALE
        else:
            return FreshnessLevel.EXPIRED

    async def apply_decay_to_signal(
        self,
        enhanced_signal,
        pattern_type: str
    ) -> Dict[str, Any]:
        """
        Apply time-based decay to an enhanced signal.

        Args:
            enhanced_signal: The signal to decay
            pattern_type: Pattern type for decay rate

        Returns:
            Signal with decayed confidence and updated info
        """
        signal_dict = enhanced_signal.to_dict()
        created_at = enhanced_signal.generated_at
        age_seconds = int((datetime.now() - created_at).total_seconds())

        # Calculate decay
        decay_rate = self.decay_rates.get(pattern_type, 0.10)
        hours_old = age_seconds / 3600
        decay_factor = max(0.2, 1 - (decay_rate * hours_old))  # Minimum 20%

        # Apply decay to confidence
        original_confidence = signal_dict["confidence"]
        decayed_confidence = original_confidence * decay_factor

        signal_dict["confidence"] = decayed_confidence
        signal_dict["decay_factor"] = decay_factor
        signal_dict["signal_age_seconds"] = age_seconds
        signal_dict["freshness_level"] = self._determine_freshness_level(age_seconds).value
        signal_dict["is_active"] = decay_factor > 0.3

        return signal_dict
