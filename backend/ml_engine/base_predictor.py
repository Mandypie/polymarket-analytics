"""
Base ML Predictor

Abstract base class for all machine learning predictors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class PredictionType(Enum):
    """Types of predictions"""
    MARKET_OUTCOME = "market_outcome"  # YES/NO prediction
    PRICE_MOVEMENT = "price_movement"  # Price change prediction
    LIQUIDITY_FORECAST = "liquidity_forecast"  # Liquidity prediction
    MARKET_SIMILARITY = "market_similarity"  # Market similarity


@dataclass
class PredictionResult:
    """Result of a ML prediction"""
    prediction_type: PredictionType
    market_id: str
    prediction: Any  # The actual prediction (could be class, probability, etc.)
    confidence: float  # 0 to 1
    model_version: str
    features: Dict[str, float]  # Feature values used
    prediction_metadata: Dict[str, Any] = None
    created_at: datetime = None
    horizon_hours: Optional[int] = None
    valid_until: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "prediction_type": self.prediction_type.value,
            "market_id": self.market_id,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "model_version": self.model_version,
            "features": self.features,
            "metadata": self.prediction_metadata or {},
            "created_at": self.created_at.isoformat(),
            "horizon_hours": self.horizon_hours,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None
        }

    def is_valid(self) -> bool:
        """Check if prediction is still valid"""
        if self.valid_until is None:
            return True
        return datetime.now() < self.valid_until


class BasePredictor(ABC):
    """Abstract base class for ML predictors"""

    def __init__(self, model_version: str = "1.0"):
        self.model_version = model_version
        self.model = None  # To be loaded by subclass
        self.feature_columns = []

    @abstractmethod
    async def predict(self, market_data: Dict[str, Any]) -> PredictionResult:
        """
        Make a prediction for a single market.

        Args:
            market_data: Market data including prices, volume, etc.

        Returns:
            PredictionResult with prediction and confidence
        """
        pass

    @abstractmethod
    async def predict_batch(self, markets: List[Dict[str, Any]]) -> List[PredictionResult]:
        """
        Make predictions for multiple markets.

        Args:
            markets: List of market data

        Returns:
            List of PredictionResult objects
        """
        pass

    @abstractmethod
    async def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train or update the model.

        Args:
            training_data: Historical data for training

        Returns:
            Training metrics and results
        """
        pass

    def _extract_features(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract features from market data.

        Override in subclass for specific feature engineering.
        """
        features = {}

        # Basic price features
        yes_price = market_data.get("yes_price", 0.5)
        no_price = market_data.get("no_price", 0.5)
        liquidity = market_data.get("liquidity", 0)
        volume_24h = market_data.get("volume_24h", 0)

        features["yes_price"] = yes_price
        features["no_price"] = no_price
        features["liquidity"] = liquidity
        features["volume_24h"] = volume_24h

        # Price spread
        features["price_spread"] = abs(yes_price - no_price)

        # Price momentum (if historical data available)
        price_history = market_data.get("price_history", [])
        if len(price_history) >= 5:
            recent_prices = [d.get("yes_price", yes_price) for d in price_history[-5:]]
            momentum_5 = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] if recent_prices[0] > 0 else 0
            features["momentum_5"] = momentum_5

        if len(price_history) >= 24:
            recent_prices = [d.get("yes_price", yes_price) for d in price_history[-24:]]
            momentum_24 = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] if recent_prices[0] > 0 else 0
            features["momentum_24"] = momentum_24

        return features

    def _validate_features(self, features: Dict[str, float]) -> bool:
        """Validate that required features are present"""
        return all(feature in features for feature in self.feature_columns)
