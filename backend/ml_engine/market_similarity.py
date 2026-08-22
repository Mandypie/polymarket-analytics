"""
Market Similarity Embedding

Finds historically similar markets using feature embeddings.
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import math

from ml_engine.base_predictor import BasePredictor, PredictionResult, PredictionType

logger = logging.getLogger(__name__)


class MarketSimilarityEmbedding(BasePredictor):
    """
    Creates market embeddings and finds similar historical markets.

    Uses simplified feature-based embeddings (production would use
    trained embedding models or dimensionality reduction).
    """

    def __init__(self, model_version: str = "1.0"):
        super().__init__(model_version)
        self.embedding_dimension = 16
        self.market_embeddings: Dict[str, List[float]] = {}

    async def predict(self, market_data: Dict[str, Any]) -> PredictionResult:
        """Create embedding for a market"""
        embedding = await self.create_market_embedding(market_data)

        return PredictionResult(
            prediction_type=PredictionType.MARKET_SIMILARITY,
            market_id=market_data.get("market_id", ""),
            prediction={"embedding": embedding},
            confidence=1.0,  # Embedding creation is deterministic
            model_version=self.model_version,
            features=market_data,
            prediction_metadata={
                "embedding_dimension": len(embedding),
                "reasoning": "Market embedding created from features"
            }
        )

    async def find_similar_markets(
        self,
        market_id: str,
        all_markets: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find historically similar markets"""
        if market_id not in self.market_embeddings:
            # Need to create embedding for target market first
            target_market = next((m for m in all_markets if m.get("market_id") == market_id), None)
            if target_market:
                await self.predict(target_market)
            else:
                return []

        target_embedding = self.market_embeddings.get(market_id)
        if not target_embedding:
            return []

        similarities = []

        for market in all_markets:
            other_id = market.get("market_id")
            if other_id == market_id or other_id not in self.market_embeddings:
                continue

            other_embedding = self.market_embeddings[other_id]
            similarity = self._cosine_similarity(target_embedding, other_embedding)

            similarities.append({
                "market_id": other_id,
                "similarity": similarity,
                "market_data": market
            })

        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return similarities[:top_k]

    async def get_market_outcomes(self, market_ids: List[str]) -> List[Dict[str, Any]]:
        """Get outcomes for similar markets (placeholder)"""
        # In production, this would query historical results
        outcomes = []
        for market_id in market_ids:
            outcomes.append({
                "market_id": market_id,
                "outcome": "UNKNOWN",  # Would be actual outcome
                "resolution_price": 0.5,
                "resolved_at": None
            })
        return outcomes

    async def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train by creating embeddings for all markets"""
        for market in training_data:
            market_id = market.get("market_id")
            if market_id:
                embedding = self._create_embedding_from_features(market)
                self.market_embeddings[market_id] = embedding

        logger.info(f"Created embeddings for {len(self.market_embeddings)} markets")

        return {
            "markets_embedded": len(self.market_embeddings),
            "embedding_dimension": self.embedding_dimension
        }

    async def create_market_embedding(self, market_data: Dict[str, Any]) -> List[float]:
        """Create embedding vector for a market"""
        embedding = self._create_embedding_from_features(market_data)
        market_id = market_data.get("market_id")

        if market_id:
            self.market_embeddings[market_id] = embedding

        return embedding

    def _create_embedding_from_features(self, market_data: Dict[str, Any]) -> List[float]:
        """Create embedding vector from market features"""
        features = []

        # Price features (4 dimensions)
        yes_price = market_data.get("yes_price", 0.5)
        no_price = market_data.get("no_price", 0.5)
        features.extend([yes_price, no_price, yes_price - no_price, yes_price + no_price])

        # Liquidity and volume (4 dimensions, log-transformed)
        liquidity = market_data.get("liquidity", 0)
        volume_24h = market_data.get("volume_24h", 0)
        features.extend([
            math.log(liquidity + 1) / 10,
            math.log(volume_24h + 1) / 12,
            liquidity / 100000,  # Normalized
            volume_24h / 1000000  # Normalized
        ])

        # Category embedding (4 dimensions, one-hot for major categories)
        category = market_data.get("category", "").lower()
        categories = ["politics", "crypto", "sports", "culture"]
        for cat in categories:
            features.append(1.0 if cat in category else 0.0)

        # Momentum features (4 dimensions)
        price_history = market_data.get("price_history", [])
        if len(price_history) >= 5:
            prices = [d.get("yes_price", yes_price) for d in price_history[-5:]]
            momentum_5 = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
            features.append(momentum_5)
        else:
            features.append(0.0)

        if len(price_history) >= 24:
            prices = [d.get("yes_price", yes_price) for d in price_history[-24:]]
            momentum_24 = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
            features.append(momentum_24)
        else:
            features.append(momentum_5)  # Use short-term as fallback

        # Volatility (2 dimensions)
        if len(price_history) >= 2:
            prices = [d.get("yes_price", yes_price) for d in price_history]
            changes = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = sum(abs(c) for c in changes) / len(changes) if changes else 0
            features.append(volatility)
        else:
            features.append(0.02)  # Default volatility

        features.append(1.0)  # Bias term

        # Pad or truncate to exact dimension
        while len(features) < self.embedding_dimension:
            features.append(0.0)

        return features[:self.embedding_dimension]

    def _cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if len(embedding1) != len(embedding2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(b * b for b in embedding2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)
