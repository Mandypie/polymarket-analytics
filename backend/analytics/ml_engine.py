"""
ML/AI Engine for Polymarket Analytics Platform

Provides machine learning models for:
- Market outcome classification
- Price movement prediction
- Liquidity forecasting
- Market similarity embedding
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class PredictionDirection(Enum):
    """Prediction direction enum"""
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class ConfidenceLevel(Enum):
    """Confidence level enum"""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


@dataclass
class PredictionResult:
    """Base prediction result"""
    prediction: float
    confidence: float
    direction: PredictionDirection
    confidence_level: ConfidenceLevel
    timestamp: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "prediction": self.prediction,
            "confidence": self.confidence,
            "direction": self.direction.value,
            "confidence_level": self.confidence_level.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class OutcomePrediction(PredictionResult):
    """Market outcome prediction result"""
    yes_probability: float
    no_probability: float
    factors: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "yes_probability": self.yes_probability,
            "no_probability": self.no_probability,
            "factors": self.factors
        })
        return result


@dataclass
class PricePrediction(PredictionResult):
    """Price movement prediction result"""
    current_price: float
    predicted_price: float
    target_price: float
    stop_loss: float
    time_horizon_hours: int
    expected_move_pct: float

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "current_price": self.current_price,
            "predicted_price": self.predicted_price,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "time_horizon_hours": self.time_horizon_hours,
            "expected_move_pct": self.expected_move_pct
        })
        return result


@dataclass
class LiquidityForecast:
    """Liquidity forecast result"""
    current_volume: float
    predicted_volume: float
    current_spread: float
    predicted_spread: float
    volume_trend: str  # INCREASING, DECREASING, STABLE
    spread_trend: str
    confidence: float
    timeframe_hours: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_volume": self.current_volume,
            "predicted_volume": self.predicted_volume,
            "current_spread": self.current_spread,
            "predicted_spread": self.predicted_spread,
            "volume_trend": self.volume_trend,
            "spread_trend": self.spread_trend,
            "confidence": self.confidence,
            "timeframe_hours": self.timeframe_hours
        }


@dataclass
class MarketSimilarity:
    """Market similarity result"""
    market_id: str
    similarity_score: float
    similar_market_id: str
    similar_market_question: str
    outcome: str
    factors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_id": self.market_id,
            "similarity_score": self.similarity_score,
            "similar_market_id": self.similar_market_id,
            "similar_market_question": self.similar_market_question,
            "outcome": self.outcome,
            "factors": self.factors
        }


class MarketOutcomeClassifier:
    """
    ML-based market outcome classifier.

    Predicts YES/NO probability for binary prediction markets
    using ensemble of features including order flow, price momentum,
    liquidity dynamics, and cross-market correlations.
    """

    def __init__(self):
        self.model_trained = False
        self.feature_weights = self._initialize_feature_weights()
        self.predictions_cache = {}

    def _initialize_feature_weights(self) -> Dict[str, float]:
        """Initialize feature weights for the ensemble model"""
        return {
            "price_momentum": 0.25,
            "order_flow_imbalance": 0.20,
            "liquidity_quality": 0.15,
            "volume_surge": 0.15,
            "price_stability": 0.10,
            "cross_market_signal": 0.10,
            "time_decay": 0.05
        }

    async def predict_outcome(
        self,
        market_data: Dict[str, Any],
        order_book: Optional[Dict[str, Any]] = None,
        historical_data: Optional[List[Dict]] = None
    ) -> OutcomePrediction:
        """
        Predict market outcome (YES/NO probability).

        Args:
            market_data: Market data including prices, liquidity
            order_book: Optional order book data
            historical_data: Optional historical price data

        Returns:
            OutcomePrediction with probabilities and factors
        """
        # Extract features
        features = await self._extract_features(market_data, order_book, historical_data)

        # Calculate ensemble prediction
        yes_prob = self._calculate_ensemble_prediction(features)

        # Normalize to ensure valid probability
        yes_prob = max(0.01, min(0.99, yes_prob))
        no_prob = 1.0 - yes_prob

        # Determine direction and confidence
        direction = self._determine_direction(yes_prob)
        confidence = self._calculate_confidence(features, yes_prob)
        confidence_level = self._determine_confidence_level(confidence)

        # Build factor list
        factors = self._build_factor_explanation(features, yes_prob)

        return OutcomePrediction(
            prediction=yes_prob,
            confidence=confidence,
            direction=direction,
            confidence_level=confidence_level,
            timestamp=datetime.now(),
            metadata={"features": features},
            yes_probability=yes_prob,
            no_probability=no_prob,
            factors=factors
        )

    async def _extract_features(
        self,
        market_data: Dict[str, Any],
        order_book: Optional[Dict[str, Any]],
        historical_data: Optional[List[Dict]]
    ) -> Dict[str, float]:
        """Extract predictive features from market data"""
        features = {}

        # Price momentum (current price vs recent average)
        yes_price = market_data.get("yes_price", 0.5)
        features["price_momentum"] = self._calculate_price_momentum(
            yes_price, historical_data
        )

        # Order flow imbalance
        features["order_flow_imbalance"] = self._calculate_order_flow_imbalance(order_book)

        # Liquidity quality
        liquidity = market_data.get("liquidity", 0)
        features["liquidity_quality"] = min(1.0, liquidity / 100000.0)

        # Volume surge (2x normal baseline)
        volume_24h = market_data.get("volume_24h", 0)
        features["volume_surge"] = min(1.0, volume_24h / 50000.0)

        # Price stability (inverse of volatility)
        features["price_stability"] = self._calculate_price_stability(historical_data)

        # Cross-market signal strength
        features["cross_market_signal"] = market_data.get("cross_market_strength", 0.5)

        # Time decay (signals degrade over time)
        features["time_decay"] = 1.0  # Fresh signal

        return features

    def _calculate_price_momentum(
        self,
        current_price: float,
        historical_data: Optional[List[Dict]]
    ) -> float:
        """Calculate price momentum score"""
        if not historical_data or len(historical_data) < 3:
            return 0.5  # Neutral

        # Calculate average of recent prices
        recent_prices = [
            m.get("yes_price", 0.5) for m in historical_data[-10:]
        ]
        avg_price = sum(recent_prices) / len(recent_prices)

        # Momentum: current vs average (normalized to 0-1)
        momentum = (current_price - avg_price) / avg_price if avg_price > 0 else 0
        return max(0, min(1, 0.5 + momentum))

    def _calculate_order_flow_imbalance(
        self,
        order_book: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate order flow imbalance"""
        if not order_book:
            return 0.5  # Neutral

        bids = order_book.get("bids", [])
        asks = order_book.get("asks", [])

        if not bids or not asks:
            return 0.5

        # Calculate bid and ask volumes
        bid_volume = sum(level.get("size", 0) for level in bids)
        ask_volume = sum(level.get("size", 0) for level in asks)

        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return 0.5

        # Bid-side pressure = YES demand
        imbalance = bid_volume / total_volume
        return max(0, min(1, imbalance))

    def _calculate_price_stability(
        self,
        historical_data: Optional[List[Dict]]
    ) -> float:
        """Calculate price stability (inverse of volatility)"""
        if not historical_data or len(historical_data) < 5:
            return 0.5  # Neutral

        prices = [m.get("yes_price", 0.5) for m in historical_data[-20:]]
        if len(prices) < 2:
            return 0.5

        # Calculate standard deviation
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5

        # Stability = 1 - (normalized std dev)
        stability = 1.0 - min(1.0, std_dev / mean_price if mean_price > 0 else 0)
        return max(0, min(1, stability))

    def _calculate_ensemble_prediction(self, features: Dict[str, float]) -> float:
        """Calculate ensemble prediction using weighted features"""
        weighted_sum = 0.0
        total_weight = 0.0

        for feature_name, weight in self.feature_weights.items():
            if feature_name in features:
                weighted_sum += features[feature_name] * weight
                total_weight += weight

        if total_weight == 0:
            return 0.5

        return weighted_sum / total_weight

    def _determine_direction(self, yes_prob: float) -> PredictionDirection:
        """Determine prediction direction from probability"""
        if yes_prob > 0.6:
            return PredictionDirection.LONG
        elif yes_prob < 0.4:
            return PredictionDirection.SHORT
        else:
            return PredictionDirection.NEUTRAL

    def _calculate_confidence(
        self,
        features: Dict[str, float],
        yes_prob: float
    ) -> float:
        """Calculate prediction confidence"""
        # Base confidence from probability extremeness
        prob_confidence = abs(yes_prob - 0.5) * 2  # 0 to 1

        # Feature consistency (how aligned are features?)
        feature_values = list(features.values())
        if len(feature_values) > 1:
            mean_feature = sum(feature_values) / len(feature_values)
            variance = sum((f - mean_feature) ** 2 for f in feature_values) / len(feature_values)
            consistency = 1.0 - min(1.0, variance * 4)  # Lower variance = higher consistency
        else:
            consistency = 0.5

        # Combine
        confidence = (prob_confidence * 0.6) + (consistency * 0.4)
        return max(0, min(1, confidence))

    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level from confidence score"""
        if confidence >= 0.85:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.70:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.50:
            return ConfidenceLevel.MODERATE
        elif confidence >= 0.30:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _build_factor_explanation(
        self,
        features: Dict[str, float],
        yes_prob: float
    ) -> List[Dict[str, Any]]:
        """Build explanation of factors contributing to prediction"""
        factors = []

        for feature_name, value in features.items():
            weight = self.feature_weights.get(feature_name, 0.1)
            contribution = value * weight

            factors.append({
                "name": feature_name.replace("_", " ").title(),
                "value": value,
                "weight": weight,
                "contribution": contribution,
                "signal": "BULLISH" if value > 0.6 else "BEARISH" if value < 0.4 else "NEUTRAL"
            })

        # Sort by contribution
        factors.sort(key=lambda x: abs(x["contribution"]), reverse=True)

        return factors


class PriceMovementPredictor:
    """
    ML-based price movement predictor.

    Forecasts future price movements using technical indicators,
    momentum analysis, and liquidity dynamics.
    """

    def __init__(self):
        self.prediction_horizons = [1, 6, 24, 72]  # hours

    async def predict_price_movement(
        self,
        market_data: Dict[str, Any],
        order_book: Optional[Dict[str, Any]] = None,
        historical_data: Optional[List[Dict]] = None,
        horizon_hours: int = 24
    ) -> PricePrediction:
        """
        Predict price movement over specified horizon.

        Args:
            market_data: Current market data
            order_book: Optional order book
            historical_data: Historical price data
            horizon_hours: Prediction time horizon

        Returns:
            PricePrediction with targets and stops
        """
        current_price = market_data.get("yes_price", 0.5)

        # Calculate technical indicators
        momentum = self._calculate_momentum(historical_data)
        trend = self._calculate_trend(historical_data)
        support_resistance = self._calculate_support_resistance(historical_data)
        liquidity_pressure = self._calculate_liquidity_pressure(order_book)

        # Predict price change
        predicted_change_pct = self._predict_price_change(
            momentum, trend, support_resistance, liquidity_pressure
        )

        predicted_price = current_price * (1 + predicted_change_pct)

        # Calculate target and stop loss
        target_price = self._calculate_target(current_price, predicted_change_pct)
        stop_loss = self._calculate_stop_loss(current_price, predicted_change_pct)

        # Determine direction and confidence
        direction = self._determine_direction(predicted_change_pct)
        confidence = self._calculate_prediction_confidence(
            momentum, trend, liquidity_pressure
        )
        confidence_level = self._map_to_confidence_level(confidence)

        return PricePrediction(
            prediction=predicted_change_pct,
            confidence=confidence,
            direction=direction,
            confidence_level=confidence_level,
            timestamp=datetime.now(),
            metadata={
                "momentum": momentum,
                "trend": trend,
                "support_resistance": support_resistance,
                "liquidity_pressure": liquidity_pressure
            },
            current_price=current_price,
            predicted_price=predicted_price,
            target_price=target_price,
            stop_loss=stop_loss,
            time_horizon_hours=horizon_hours,
            expected_move_pct=predicted_change_pct * 100
        )

    def _calculate_momentum(
        self,
        historical_data: Optional[List[Dict]]
    ) -> float:
        """Calculate price momentum (-1 to 1)"""
        if not historical_data or len(historical_data) < 5:
            return 0.0

        prices = [m.get("yes_price", 0.5) for m in historical_data[-10:]]

        # Simple momentum: recent change
        if len(prices) >= 2:
            momentum = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
            return max(-1, min(1, momentum * 10))  # Scale up
        return 0.0

    def _calculate_trend(
        self,
        historical_data: Optional[List[Dict]]
    ) -> float:
        """Calculate trend direction (-1 bearish to 1 bullish)"""
        if not historical_data or len(historical_data) < 10:
            return 0.0

        prices = [m.get("yes_price", 0.5) for m in historical_data[-20:]]

        # Linear regression slope
        n = len(prices)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(prices)
        sum_xy = sum(x[i] * prices[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)

        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator

        # Normalize slope
        avg_price = sum_y / n
        normalized_slope = slope / avg_price if avg_price > 0 else 0

        return max(-1, min(1, normalized_slope * 100))

    def _calculate_support_resistance(
        self,
        historical_data: Optional[List[Dict]]
    ) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        if not historical_data or len(historical_data) < 10:
            return {"support": 0.4, "resistance": 0.6}

        prices = [m.get("yes_price", 0.5) for m in historical_data[-30:]]

        # Simple support/resistance: min/max with some buffer
        support = min(prices) * 0.98
        resistance = max(prices) * 1.02

        return {"support": max(0.01, support), "resistance": min(0.99, resistance)}

    def _calculate_liquidity_pressure(
        self,
        order_book: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate liquidity pressure (-1 to 1, positive = buy pressure)"""
        if not order_book:
            return 0.0

        bids = order_book.get("bids", [])
        asks = order_book.get("asks", [])

        if not bids or not asks:
            return 0.0

        # Weighted bid vs ask pressure
        bid_pressure = sum(
            level.get("size", 0) * level.get("price", 0.5)
            for level in bids[:5]
        )
        ask_pressure = sum(
            level.get("size", 0) * (1 - level.get("price", 0.5))
            for level in asks[:5]
        )

        total = bid_pressure + ask_pressure
        if total == 0:
            return 0.0

        pressure = (bid_pressure - ask_pressure) / total
        return max(-1, min(1, pressure * 2))

    def _predict_price_change(
        self,
        momentum: float,
        trend: float,
        support_resistance: Dict[str, float],
        liquidity_pressure: float
    ) -> float:
        """Predict price change percentage"""
        # Weighted combination of factors
        weights = {
            "momentum": 0.3,
            "trend": 0.3,
            "liquidity": 0.4
        }

        predicted_change = (
            momentum * weights["momentum"] +
            trend * weights["trend"] +
            liquidity_pressure * weights["liquidity"]
        )

        # Scale to reasonable price change (max ±5% for prediction)
        return max(-0.05, min(0.05, predicted_change * 0.5))

    def _calculate_target(
        self,
        current_price: float,
        predicted_change: float
    ) -> float:
        """Calculate target price"""
        # Target: 1.5x the predicted move in the same direction
        target_change = predicted_change * 1.5
        target = current_price * (1 + target_change)
        return max(0.01, min(0.99, target))

    def _calculate_stop_loss(
        self,
        current_price: float,
        predicted_change: float
    ) -> float:
        """Calculate stop loss level"""
        # Stop loss: 0.5x the predicted move in opposite direction
        stop_change = -predicted_change * 0.5
        stop = current_price * (1 + stop_change)
        return max(0.01, min(0.99, stop))

    def _determine_direction(self, predicted_change: float) -> PredictionDirection:
        """Determine direction from predicted change"""
        if predicted_change > 0.02:
            return PredictionDirection.LONG
        elif predicted_change < -0.02:
            return PredictionDirection.SHORT
        else:
            return PredictionDirection.NEUTRAL

    def _calculate_prediction_confidence(
        self,
        momentum: float,
        trend: float,
        liquidity_pressure: float
    ) -> float:
        """Calculate prediction confidence"""
        # Confidence based on alignment of factors
        factors = [momentum, trend, liquidity_pressure]

        # Check if factors agree on direction
        positive_count = sum(1 for f in factors if f > 0.1)
        negative_count = sum(1 for f in factors if f < -0.1)

        total_agreement = max(positive_count, negative_count) / len(factors)

        # Strength of signals
        avg_strength = sum(abs(f) for f in factors) / len(factors)

        # Combine agreement and strength
        confidence = (total_agreement * 0.6) + (min(1, avg_strength) * 0.4)

        return max(0, min(1, confidence))

    def _map_to_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Map confidence score to level"""
        if confidence >= 0.85:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.70:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.50:
            return ConfidenceLevel.MODERATE
        elif confidence >= 0.30:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


class LiquidityForecaster:
    """
    ML-based liquidity forecaster.

    Predicts future volume and spread changes based on
    historical patterns and market conditions.
    """

    def __init__(self):
        self.volume_baselines = {
            "Crypto": 100000,
            "Politics": 50000,
            "Sports": 30000,
            "Economics": 25000,
            "World": 20000,
            "Other": 15000
        }

    async def forecast_liquidity(
        self,
        market_data: Dict[str, Any],
        order_book: Optional[Dict[str, Any]] = None,
        historical_data: Optional[List[Dict]] = None,
        timeframe_hours: int = 24
    ) -> LiquidityForecast:
        """
        Forecast liquidity metrics over specified timeframe.

        Args:
            market_data: Current market data
            order_book: Optional order book
            historical_data: Historical data
            timeframe_hours: Forecast horizon

        Returns:
            LiquidityForecast with volume and spread predictions
        """
        # Current metrics
        current_volume = market_data.get("volume_24h", 0)
        current_spread = self._get_current_spread(order_book, market_data)

        # Predict volume
        predicted_volume = await self._predict_volume(
            current_volume, market_data, historical_data, timeframe_hours
        )

        # Predict spread
        predicted_spread = await self._predict_spread(
            current_spread, predicted_volume, current_volume, order_book, timeframe_hours
        )

        # Determine trends
        volume_trend = self._determine_trend(current_volume, predicted_volume)
        spread_trend = self._determine_trend(current_spread, predicted_spread)

        # Calculate confidence
        confidence = self._calculate_forecast_confidence(
            current_volume, predicted_volume, historical_data
        )

        return LiquidityForecast(
            current_volume=current_volume,
            predicted_volume=predicted_volume,
            current_spread=current_spread,
            predicted_spread=predicted_spread,
            volume_trend=volume_trend,
            spread_trend=spread_trend,
            confidence=confidence,
            timeframe_hours=timeframe_hours
        )

    def _get_current_spread(
        self,
        order_book: Optional[Dict[str, Any]],
        market_data: Dict[str, Any]
    ) -> float:
        """Get current spread from order book or market data"""
        if order_book:
            bids = order_book.get("bids", [])
            asks = order_book.get("asks", [])

            if bids and asks:
                best_bid = bids[0].get("price", 0.5)
                best_ask = asks[0].get("price", 0.5)
                return abs(best_ask - best_bid)

        # Estimate from market data
        yes_price = market_data.get("yes_price", 0.5)
        liquidity = market_data.get("liquidity", 10000)

        # Spread estimate based on liquidity
        if liquidity > 100000:
            return 0.01
        elif liquidity > 50000:
            return 0.02
        elif liquidity > 20000:
            return 0.03
        else:
            return 0.05

    async def _predict_volume(
        self,
        current_volume: float,
        market_data: Dict[str, Any],
        historical_data: Optional[List[Dict]],
        timeframe_hours: int
    ) -> float:
        """Predict future volume"""
        category = market_data.get("category", "Other")
        baseline = self.volume_baselines.get(category, 20000)

        # Volume trend from historical data
        if historical_data and len(historical_data) >= 3:
            recent_volumes = [
                m.get("volume_24h", baseline) for m in historical_data[-10:]
            ]
            avg_volume = sum(recent_volumes) / len(recent_volumes)

            # Trend direction
            trend = (recent_volumes[-1] - recent_volumes[0]) / len(recent_volumes) if recent_volumes[0] > 0 else 0
        else:
            avg_volume = current_volume
            trend = 0

        # Adjust for interest (price = interest)
        yes_price = market_data.get("yes_price", 0.5)
        interest_factor = 0.5 + abs(yes_price - 0.5)  # Higher at extremes

        # Time-based scaling
        time_factor = timeframe_hours / 24

        # Predict with trend and interest
        predicted = avg_volume * (1 + trend * 0.1) * interest_factor * time_factor

        return max(0, predicted)

    async def _predict_spread(
        self,
        current_spread: float,
        predicted_volume: float,
        current_volume: float,
        order_book: Optional[Dict[str, Any]],
        timeframe_hours: int
    ) -> float:
        """Predict future spread"""
        # Spread inversely related to volume
        volume_change_factor = predicted_volume / max(1, current_volume)

        # Higher volume = tighter spread
        spread_change = 1 / (volume_change_factor ** 0.5)

        predicted = current_spread * spread_change

        # Mean reversion (spread tends to narrow over time)
        time_decay = max(0.8, 1 - (timeframe_hours * 0.01))
        predicted = predicted * time_decay

        # Minimum spread
        return max(0.005, predicted)

    def _determine_trend(self, current: float, predicted: float) -> str:
        """Determine trend direction"""
        change_pct = (predicted - current) / current if current > 0 else 0

        if change_pct > 0.05:
            return "INCREASING"
        elif change_pct < -0.05:
            return "DECREASING"
        else:
            return "STABLE"

    def _calculate_forecast_confidence(
        self,
        current_volume: float,
        predicted_volume: float,
        historical_data: Optional[List[Dict]]
    ) -> float:
        """Calculate forecast confidence"""
        # Base confidence on data availability
        if historical_data and len(historical_data) >= 10:
            base_confidence = 0.7
        elif historical_data and len(historical_data) >= 5:
            base_confidence = 0.5
        else:
            base_confidence = 0.3

        # Adjust for volume stability
        if current_volume > 0:
            volume_ratio = predicted_volume / current_volume
            # Extreme predictions = lower confidence
            if volume_ratio > 2 or volume_ratio < 0.5:
                base_confidence *= 0.7

        return max(0, min(1, base_confidence))


class MarketSimilarityEmbedding:
    """
    Market similarity embedding system.

    Finds historical market analogs using feature-based similarity
    and embedding techniques.
    """

    def __init__(self):
        self.feature_weights = {
            "category_match": 0.3,
            "price_level": 0.2,
            "liquidity_level": 0.15,
            "volume_level": 0.15,
            "time_to_expiry": 0.1,
            "question_similarity": 0.1
        }

    async def find_similar_markets(
        self,
        market_data: Dict[str, Any],
        historical_markets: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[MarketSimilarity]:
        """
        Find similar historical markets.

        Args:
            market_data: Current market data
            historical_markets: List of resolved historical markets
            top_k: Number of similar markets to return

        Returns:
            List of MarketSimilarity results
        """
        similarities = []

        for hist_market in historical_markets:
            similarity = await self._calculate_similarity(market_data, hist_market)

            similarities.append(MarketSimilarity(
                market_id=market_data.get("market_id", ""),
                similarity_score=similarity,
                similar_market_id=hist_market.get("market_id", ""),
                similar_market_question=hist_market.get("question", ""),
                outcome=hist_market.get("outcome", "UNKNOWN"),
                factors=self._explain_similarity(market_data, hist_market)
            ))

        # Sort by similarity score
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)

        return similarities[:top_k]

    async def _calculate_similarity(
        self,
        market_data: Dict[str, Any],
        hist_market: Dict[str, Any]
    ) -> float:
        """Calculate similarity score between two markets"""
        scores = {}

        # Category match
        scores["category_match"] = self._score_category_match(
            market_data.get("category", ""),
            hist_market.get("category", "")
        )

        # Price level similarity
        scores["price_level"] = self._score_price_similarity(
            market_data.get("yes_price", 0.5),
            hist_market.get("yes_price", 0.5)
        )

        # Liquidity level similarity
        scores["liquidity_level"] = self._score_liquidity_similarity(
            market_data.get("liquidity", 0),
            hist_market.get("liquidity", 0)
        )

        # Volume level similarity
        scores["volume_level"] = self._score_volume_similarity(
            market_data.get("volume_24h", 0),
            hist_market.get("volume_24h", 0)
        )

        # Time to expiry similarity
        scores["time_to_expiry"] = self._score_time_similarity(
            market_data.get("end_date"),
            hist_market.get("end_date")
        )

        # Question keyword similarity
        scores["question_similarity"] = self._score_question_similarity(
            market_data.get("question", ""),
            hist_market.get("question", "")
        )

        # Weighted sum
        total_score = 0.0
        total_weight = 0.0

        for feature, score in scores.items():
            weight = self.feature_weights.get(feature, 0.1)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0

    def _score_category_match(self, cat1: str, cat2: str) -> float:
        """Score category similarity"""
        return 1.0 if cat1.lower() == cat2.lower() else 0.0

    def _score_price_similarity(self, price1: float, price2: float) -> float:
        """Score price level similarity"""
        diff = abs(price1 - price2)
        # Within 10% = high similarity
        return max(0, 1 - (diff / 0.1))

    def _score_liquidity_similarity(self, liq1: float, liq2: float) -> float:
        """Score liquidity similarity"""
        if liq1 == 0 and liq2 == 0:
            return 1.0

        # Log-scale comparison
        log1 = np.log1p(liq1)
        log2 = np.log1p(liq2)

        diff = abs(log1 - log2)
        return max(0, 1 - (diff / 5))  # 5x difference = 0 similarity

    def _score_volume_similarity(self, vol1: float, vol2: float) -> float:
        """Score volume similarity"""
        if vol1 == 0 and vol2 == 0:
            return 1.0

        # Log-scale comparison
        log1 = np.log1p(vol1)
        log2 = np.log1p(vol2)

        diff = abs(log1 - log2)
        return max(0, 1 - (diff / 5))

    def _score_time_similarity(self, end1: Optional[str], end2: Optional[str]) -> float:
        """Score time to expiry similarity"""
        if not end1 or not end2:
            return 0.5

        try:
            from datetime import datetime
            date1 = datetime.fromisoformat(end1.replace('Z', '+00:00'))
            date2 = datetime.fromisoformat(end2.replace('Z', '+00:00'))

            now = datetime.now()
            days1 = (date1 - now).days
            days2 = (date2 - now).days if date2 > now else 0

            diff = abs(days1 - days2)
            # Within 30 days = similar
            return max(0, 1 - (diff / 30))

        except Exception:
            return 0.5

    def _score_question_similarity(self, q1: str, q2: str) -> float:
        """Score question keyword similarity"""
        if not q1 or not q2:
            return 0.0

        # Simple keyword matching
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())

        intersection = words1.intersection(words2)

        if not intersection:
            return 0.0

        # Jaccard similarity
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0

    def _explain_similarity(
        self,
        market_data: Dict[str, Any],
        hist_market: Dict[str, Any]
    ) -> List[str]:
        """Explain why markets are similar"""
        factors = []

        if market_data.get("category") == hist_market.get("category"):
            factors.append(f"Same category: {market_data.get('category')}")

        price1 = market_data.get("yes_price", 0.5)
        price2 = hist_market.get("yes_price", 0.5)
        if abs(price1 - price2) < 0.1:
            factors.append(f"Similar price levels ({price1:.2f} vs {price2:.2f})")

        # Add keyword matches
        q1 = market_data.get("question", "")
        q2 = hist_market.get("question", "")
        if q1 and q2:
            words1 = set(q1.lower().split())
            words2 = set(q2.lower().split())
            common = words1.intersection(words2)
            if common:
                factors.append(f"Shared keywords: {', '.join(list(common)[:3])}")

        return factors


class MLEngine:
    """
    Main ML Engine orchestrator.

    Combines all ML models into a unified predictive intelligence system.
    """

    def __init__(self):
        self.outcome_classifier = MarketOutcomeClassifier()
        self.price_predictor = PriceMovementPredictor()
        self.liquidity_forecaster = LiquidityForecaster()
        self.similarity_finder = MarketSimilarityEmbedding()
        self.predictions_cache = {}

    async def generate_full_prediction(
        self,
        market_data: Dict[str, Any],
        order_book: Optional[Dict[str, Any]] = None,
        historical_data: Optional[List[Dict]] = None,
        historical_markets: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive prediction for a market.

        Args:
            market_data: Current market data
            order_book: Optional order book data
            historical_data: Historical price data
            historical_markets: Resolved historical markets for similarity

        Returns:
            Full prediction with all models
        """
        market_id = market_data.get("market_id", "unknown")

        # Generate predictions
        outcome_prediction = await self.outcome_classifier.predict_outcome(
            market_data, order_book, historical_data
        )

        price_prediction = await self.price_predictor.predict_price_movement(
            market_data, order_book, historical_data
        )

        liquidity_forecast = await self.liquidity_forecaster.forecast_liquidity(
            market_data, order_book, historical_data
        )

        # Find similar markets if historical data available
        similar_markets = []
        if historical_markets:
            similar_markets = await self.similarity_finder.find_similar_markets(
                market_data, historical_markets, top_k=3
            )

        # Cache prediction
        self.predictions_cache[market_id] = {
            "timestamp": datetime.now().isoformat(),
            "outcome": outcome_prediction.to_dict(),
            "price": price_prediction.to_dict(),
            "liquidity": liquidity_forecast.to_dict(),
            "similar_markets": [m.to_dict() for m in similar_markets]
        }

        return self.predictions_cache[market_id]

    async def get_prediction(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get cached prediction for a market"""
        return self.predictions_cache.get(market_id)

    def clear_cache(self):
        """Clear prediction cache"""
        self.predictions_cache.clear()


# Global ML engine instance
_ml_engine: Optional[MLEngine] = None


async def get_ml_engine() -> MLEngine:
    """Get or create the ML engine"""
    global _ml_engine
    if _ml_engine is None:
        _ml_engine = MLEngine()
    return _ml_engine
