"""
Price Movement Predictor

Predicts price movements at specified time horizons.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

from ml_engine.base_predictor import BasePredictor, PredictionResult, PredictionType

logger = logging.getLogger(__name__)


class PriceMovementPredictor(BasePredictor):
    """
    Predicts price movements at different time horizons.

    Uses trend analysis and momentum extrapolation to predict
    where prices will be in 1, 6, 24, 72 hours.
    """

    def __init__(self, model_version: str = "1.0"):
        super().__init__(model_version)
        self.prediction_horizons = [1, 6, 24, 72]  # hours
        self.feature_columns = [
            'current_price',
            'momentum_short',
            'momentum_medium',
            'volatility',
            'volume_trend'
        ]

    async def predict(self, market_data: Dict[str, Any], horizon_hours: int = 24) -> PredictionResult:
        """Predict price movement at specified horizon"""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call train() first.")

        current_price = market_data.get("yes_price", 0.5)

        # Extract features
        features = self._extract_features(market_data)

        # Calculate predicted price movement
        predicted_change = self._calculate_price_change(features, horizon_hours)
        predicted_price = current_price + predicted_change

        # Calculate confidence based on prediction strength
        confidence = self._calculate_prediction_confidence(features, predicted_change)

        return PredictionResult(
            prediction_type=PredictionType.PRICE_MOVEMENT,
            market_id=market_data.get("market_id", ""),
            prediction={
                "current_price": current_price,
                "predicted_price": max(0.01, min(0.99, predicted_price)),  # Clamp to valid range
                "predicted_change": predicted_change,
                "change_percent": (predicted_change / current_price * 100) if current_price > 0 else 0
            },
            confidence=confidence,
            model_version=self.model_version,
            features=features,
            prediction_metadata={
                "horizon_hours": horizon_hours,
                "reasoning": self._generate_reasoning(features, predicted_change, horizon_hours)
            },
            horizon_hours=horizon_hours
        )

    async def predict_batch(self, markets: List[Dict[str, Any]], horizon_hours: int = 24) -> List[PredictionResult]:
        """Predict price movements for multiple markets"""
        results = []
        for market in markets:
            try:
                result = await self.predict(market, horizon_hours)
                results.append(result)
            except Exception as e:
                logger.error(f"Error predicting price movement: {e}")

        return results

    async def get_prediction_intervals(self, market_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Get prediction intervals for all horizons"""
        intervals = {}

        for horizon in self.prediction_horizons:
            try:
                result = await self.predict(market_data, horizon)
                intervals[f"{horizon}h"] = result.to_dict()
            except Exception as e:
                logger.error(f"Error predicting for {horizon}h horizon: {e}")

        return intervals

    async def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train the price movement predictor"""
        # Analyze historical price movements
        total_examples = len(training_data)

        # Calculate average volatility
        volatilities = []
        for data in training_data:
            price_history = data.get("price_history", [])
            if len(price_history) >= 2:
                prices = [d.get("yes_price", 0.5) for d in price_history]
                changes = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                volatility = sum(abs(c) for c in changes) / len(changes) if changes else 0
                volatilities.append(volatility)

        avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0.02

        logger.info(f"Model trained on {total_examples} examples, avg volatility: {avg_volatility:.4f}")

        return {
            "training_examples": total_examples,
            "avg_volatility": avg_volatility,
            "prediction_horizons": self.prediction_horizons
        }

    def _calculate_price_change(self, features: Dict[str, float], horizon_hours: int) -> float:
        """Calculate predicted price change based on features"""
        current_price = features.get("current_price", 0.5)
        momentum_short = features.get("momentum_short", 0)
        momentum_medium = features.get("momentum_medium", 0)
        volatility = features.get("volatility", 0.02)

        # Combine momentum signals
        if horizon_hours <= 6:
            # Short-term: emphasize short momentum
            momentum_weight = 0.7
            predicted_change = momentum_short * momentum_weight * current_price
        else:
            # Longer-term: emphasize medium momentum
            momentum_weight = 0.5
            predicted_change = momentum_medium * momentum_weight * current_price

        # Add volatility-based adjustment
        volatility_adjustment = volatility * 0.1 * current_price
        predicted_change += volatility_adjustment

        # Time decay (predict less change further out)
        time_decay = max(0.3, 1 - (horizon_hours / 72))
        predicted_change *= time_decay

        return predicted_change

    def _calculate_prediction_confidence(self, features: Dict[str, float], predicted_change: float) -> float:
        """Calculate confidence based on signal strength"""
        momentum_short = features.get("momentum_short", 0)
        momentum_medium = features.get("momentum_medium", 0)

        # Stronger momentum = higher confidence
        momentum_strength = max(abs(momentum_short), abs(momentum_medium))

        # Volatility reduces confidence (more uncertainty)
        volatility = features.get("volatility", 0.02)
        volatility_penalty = min(volatility * 5, 0.3)

        confidence = max(0.3, min(momentum_strength * 2, 0.9))
        confidence -= volatility_penalty

        return max(0.1, confidence)

    def _generate_reasoning(self, features: Dict[str, float], predicted_change: float, horizon_hours: int) -> str:
        """Generate human-readable reasoning"""
        parts = []

        momentum_short = features.get("momentum_short", 0)
        momentum_medium = features.get("momentum_medium", 0)

        if predicted_change > 0:
            parts.append(f"Predicts +{predicted_change/features.get('current_price', 0.5)*100:.2f}% price increase")
            if momentum_short > 0:
                parts.append(f"Supported by positive momentum ({momentum_short:.3f})")
        else:
            parts.append(f"Predicts {predicted_change/features.get('current_price', 0.5)*100:.2f}% price decrease")
            if momentum_short < 0:
                parts.append(f"Driven by negative momentum ({momentum_short:.3f})")

        parts.append(f"Horizon: {horizon_hours}h")

        return "; ".join(parts)
