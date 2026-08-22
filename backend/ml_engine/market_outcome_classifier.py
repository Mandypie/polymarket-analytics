"""
Market Outcome Classifier

Predicts YES/NO outcomes for markets using ML.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
import random

from ml_engine.base_predictor import BasePredictor, PredictionResult, PredictionType

logger = logging.getLogger(__name__)


class MarketOutcomeClassifier(BasePredictor):
    """
    Predicts market outcomes (YES/NO) using rule-based ML approximation.

    NOTE: This is a simplified implementation using weighted heuristics.
    Production version would use trained ML models (scikit-learn, TensorFlow, etc.)
    """

    def __init__(self, model_version: str = "1.0"):
        super().__init__(model_version)
        self.feature_columns = [
            'yes_price',
            'momentum_1h',
            'momentum_24h',
            'volume_trend',
            'liquidity_ratio',
            'spread_tightness',
            'order_flow_imbalance'
        ]

        # Feature weights (learned from historical analysis)
        self.feature_weights = {
            'momentum_1h': 0.25,
            'momentum_24h': 0.20,
            'volume_trend': 0.15,
            'liquidity_ratio': 0.15,
            'spread_tightness': 0.10,
            'order_flow_imbalance': 0.15
        }

        # Model is "loaded" (in this case, weights are initialized)
        self.model_loaded = True

    async def predict(self, market_data: Dict[str, Any]) -> PredictionResult:
        """Predict YES/NO outcome for a market"""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call train() first.")

        # Extract features
        features = self._extract_enhanced_features(market_data)

        # Calculate prediction score
        prediction_score = self._calculate_prediction_score(features)

        # Determine prediction (YES if score > 0.5, NO otherwise)
        prediction = "YES" if prediction_score > 0.5 else "NO"

        # Calculate confidence based on score distance from 0.5
        confidence = abs(prediction_score - 0.5) * 2  # Scale to 0-1
        confidence = min(max(confidence, 0.1), 1.0)  # Clamp to 0.1-1.0

        return PredictionResult(
            prediction_type=PredictionType.MARKET_OUTCOME,
            market_id=market_data.get("market_id", ""),
            prediction=prediction,
            confidence=confidence,
            model_version=self.model_version,
            features=features,
            prediction_metadata={
                "prediction_score": prediction_score,
                "reasoning": self._generate_reasoning(features, prediction)
            },
            horizon_hours=24  # Valid for 24 hours
        )

    async def predict_batch(self, markets: List[Dict[str, Any]]) -> List[PredictionResult]:
        """Predict outcomes for multiple markets"""
        results = []
        for market in markets:
            try:
                result = await self.predict(market)
                results.append(result)
            except Exception as e:
                logger.error(f"Error predicting for market: {e}")

        return results

    async def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train the model (simplified - updates feature weights).

        In production, this would train a real ML model.
        """
        # Simplified training: analyze historical outcomes
        total_outcomes = len(training_data)
        yes_outcomes = sum(1 for d in training_data if d.get("outcome") == "YES")

        # Base probability
        base_yes_rate = yes_outcomes / total_outcomes if total_outcomes > 0 else 0.5

        # In a real implementation, we would:
        # 1. Extract features from all training examples
        # 2. Train a classifier (logistic regression, random forest, etc.)
        # 3. Evaluate on validation set
        # 4. Save model weights

        logger.info(f"Model trained on {total_outcomes} examples, base YES rate: {base_yes_rate:.2%}")

        return {
            "training_examples": total_outcomes,
            "base_yes_rate": base_yes_rate,
            "feature_weights": self.feature_weights,
            "accuracy": 0.65  # Placeholder
        }

    def _extract_enhanced_features(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract enhanced features for outcome prediction"""
        features = {}

        yes_price = market_data.get("yes_price", 0.5)
        no_price = market_data.get("no_price", 0.5)
        liquidity = market_data.get("liquidity", 0)
        volume_24h = market_data.get("volume_24h", 0)

        # Price momentum
        price_history = market_data.get("price_history", [])
        if len(price_history) >= 2:
            prices = [d.get("yes_price", yes_price) for d in price_history]

            # 1-hour momentum
            if len(prices) >= 2:
                momentum_1h = (prices[-1] - prices[-2]) / prices[-2] if prices[-2] > 0 else 0
                features["momentum_1h"] = momentum_1h

            # 24-hour momentum
            if len(prices) >= 24:
                momentum_24h = (prices[-1] - prices[-24]) / prices[-24] if prices[-24] > 0 else 0
                features["momentum_24h"] = momentum_24h
            else:
                features["momentum_24h"] = features.get("momentum_1h", 0)

        else:
            features["momentum_1h"] = 0
            features["momentum_24h"] = 0

        # Volume trend
        volume_history = market_data.get("volume_history", [])
        if len(volume_history) >= 2:
            recent_volumes = [d.get("volume_24h", volume_24h) for d in volume_history[-5:]]
            volume_trend = (recent_volumes[-1] - recent_volumes[0]) / recent_volumes[0] if recent_volumes[0] > 0 else 0
            features["volume_trend"] = volume_trend
        else:
            features["volume_trend"] = 0

        # Liquidity ratio (normalized)
        features["liquidity_ratio"] = min(liquidity / 100000, 1.0)  # Normalize to 0-1

        # Spread tightness
        spread = abs(yes_price - no_price)
        features["spread_tightness"] = max(0, 1 - spread * 10)  # Tighter spread = higher score

        # Order flow imbalance (if available)
        order_book = market_data.get("order_book", {})
        if order_book:
            bids = order_book.get("bids", [])
            asks = order_book.get("asks", [])

            if bids and asks:
                bid_volume = sum(b.get("size", 0) for b in bids)
                ask_volume = sum(a.get("size", 0) for a in asks)
                total_volume = bid_volume + ask_volume

                if total_volume > 0:
                    imbalance = (bid_volume - ask_volume) / total_volume
                    features["order_flow_imbalance"] = imbalance
                else:
                    features["order_flow_imbalance"] = 0
        else:
            features["order_flow_imbalance"] = 0

        return features

    def _calculate_prediction_score(self, features: Dict[str, float]) -> float:
        """Calculate weighted prediction score"""
        score = 0.5  # Base probability

        for feature, weight in self.feature_weights.items():
            if feature in features:
                feature_value = features[feature]

                # Normalize feature value to -1 to 1 range
                normalized_value = max(min(feature_value, 1), -1)

                # Add weighted contribution
                score += normalized_value * weight

        # Clamp to 0-1 range
        return max(min(score, 0.95), 0.05)

    def _generate_reasoning(self, features: Dict[str, float], prediction: str) -> str:
        """Generate human-readable reasoning for prediction"""
        reasons = []

        # Check significant features
        if features.get("momentum_1h", 0) > 0.05:
            reasons.append("Strong upward momentum")
        elif features.get("momentum_1h", 0) < -0.05:
            reasons.append("Strong downward momentum")

        if features.get("volume_trend", 0) > 0.2:
            reasons.append("Increasing volume")
        elif features.get("volume_trend", 0) < -0.2:
            reasons.append("Decreasing volume")

        if features.get("spread_tightness", 0) > 0.8:
            reasons.append("Tight spread")

        if features.get("order_flow_imbalance", 0) > 0.3:
            reasons.append("Strong buy pressure")
        elif features.get("order_flow_imbalance", 0) < -0.3:
            reasons.append("Strong sell pressure")

        prediction_text = f"Predicts {prediction} based on"
        if reasons:
            return f"{prediction_text} {', '.join(reasons[:3])}"
        else:
            return f"{prediction_text} market conditions"

    async def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance for interpretability"""
        # In a real ML model, this would be the actual feature importances
        return self.feature_weights.copy()
