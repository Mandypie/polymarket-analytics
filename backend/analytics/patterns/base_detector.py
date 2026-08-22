"""
Base Pattern Detector

Abstract base class for all pattern detectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class PatternType(Enum):
    """Pattern types"""
    MOMENTUM_REVERSAL = "momentum_reversal"
    LIQUIDITY_TRAP = "liquidity_trap"
    CROSS_MARKET = "cross_market"
    RESOLUTION_PROB = "resolution_prob"
    SENTIMENT = "sentiment"


class PatternStrength(Enum):
    """Pattern strength levels"""
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"
    EXTREME = "EXTREME"


@dataclass
class PatternResult:
    """Result of pattern detection"""
    pattern_type: PatternType
    market_id: str
    detected: bool
    confidence: float  # 0 to 1
    strength: PatternStrength
    direction: str  # "LONG", "SHORT", "NEUTRAL"
    detected_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "pattern_type": self.pattern_type.value,
            "market_id": self.market_id,
            "detected": self.detected,
            "confidence": self.confidence,
            "strength": self.strength.value,
            "direction": self.direction,
            "detected_at": self.detected_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata or {}
        }

    def is_active(self) -> bool:
        """Check if pattern is still active"""
        if self.expires_at is None:
            return True
        return datetime.now() < self.expires_at


class BaseDetector(ABC):
    """Abstract base class for pattern detectors"""

    def __init__(self):
        self.pattern_type: PatternType = None
        self.min_confidence: float = 0.6
        self.pattern_ttl_hours: int = 24  # Time to live for patterns

    @abstractmethod
    async def detect(self, market_data: Dict[str, Any], historical_data: List[Dict] = None) -> PatternResult:
        """
        Detect pattern in market data

        Args:
            market_data: Current market data
            historical_data: Historical price/volume data

        Returns:
            PatternResult with detection outcome
        """
        pass

    @abstractmethod
    async def detect_batch(self, markets: List[Dict[str, Any]]) -> List[PatternResult]:
        """
        Detect patterns across multiple markets

        Args:
            markets: List of market data

        Returns:
            List of PatternResult objects
        """
        pass

    def _calculate_strength(self, confidence: float, signal_strength: float) -> PatternStrength:
        """Calculate pattern strength from confidence and signal strength"""
        score = (confidence * 0.6) + (signal_strength * 0.4)

        if score >= 0.9:
            return PatternStrength.EXTREME
        elif score >= 0.8:
            return PatternStrength.VERY_STRONG
        elif score >= 0.7:
            return PatternStrength.STRONG
        elif score >= 0.6:
            return PatternStrength.MODERATE
        else:
            return PatternStrength.WEAK

    def _calculate_expiry(self, base_hours: int = None) -> datetime:
        """Calculate pattern expiry time"""
        ttl = base_hours or self.pattern_ttl_hours
        return datetime.now() + datetime.timedelta(hours=ttl)

    def _validate_market_data(self, market_data: Dict[str, Any]) -> bool:
        """Validate market data has required fields"""
        required_fields = ['market_id', 'yes_price', 'liquidity', 'volume_24h']
        return all(field in market_data for field in required_fields)
