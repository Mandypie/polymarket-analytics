"""
Polymarket Analytics - Production Backend
Real-time data from Polymarket APIs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Polymarket Analytics API", version="1.0.0")

# Startup logging
logger.info("Polymarket Analytics API starting...")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoints
GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"

# Cache for markets
markets_cache = {"data": None, "timestamp": None, "category_counts": {}}


async def fetch_live_markets(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Fetch live markets from Polymarket Gamma API"""
    try:
        response = requests.get(
            f"{GAMMA_API}/markets",
            params={"limit": limit, "offset": offset, "active": "true"},
            timeout=10
        )
        response.raise_for_status()

        markets = response.json()

        # Process and format markets
        processed_markets = []
        for market in markets[:limit]:
            try:
                # Extract outcome prices
                outcome_prices = {}
                if market.get("outcomePrices"):
                    import json
                    prices = json.loads(market["outcomePrices"])
                    if len(prices) >= 2:
                        outcome_prices["yes_price"] = float(prices[0])
                        outcome_prices["no_price"] = float(prices[1])

                processed_market = {
                    "market_id": market.get("id", ""),
                    "question": market.get("question", ""),
                    "description": market.get("description", "")[:200] + "..." if market.get("description") else "",
                    "yes_price": outcome_prices.get("yes_price", 0.5),
                    "no_price": outcome_prices.get("no_price", 0.5),
                    "volume_24h": float(market.get("volumeNum", 0)),
                    "liquidity": float(market.get("liquidityNum", 0)),
                    "slug": market.get("slug", ""),
                    "end_date": market.get("endDate", ""),
                    "active": market.get("active", False),
                    "category": categorize_market(market.get("question", "")),
                    "updated_at": market.get("updatedAt", datetime.now().isoformat())
                }
                processed_markets.append(processed_market)
            except Exception as e:
                logger.error(f"Error processing market {market.get('id')}: {e}")
                continue

        # Update cache
        markets_cache["data"] = processed_markets
        markets_cache["timestamp"] = datetime.now()

        # Calculate category counts
        category_counts = {}
        for market in processed_markets:
            cat = market["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1
        markets_cache["category_counts"] = category_counts

        return processed_markets

    except Exception as e:
        logger.error(f"Error fetching markets: {e}")
        return []


def categorize_market(question: str) -> str:
    """Categorize market by question content"""
    question_lower = question.lower()

    # Keywords for each category
    politics_keywords = ["election", "congress", "senate", "president", "vote", "republican", "democrat", "biden", "trump", "fed", "government", "law", "supreme court", "xi jinping", "politics"]
    crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain", "solana", "xrp", "dogecoin", "defi", "nft", "token"]
    sports_keywords = ["super bowl", "world cup", "nba", "nfl", "mlb", "championship", "game", "team", "player", "win", "score", "season"]

    if any(keyword in question_lower for keyword in politics_keywords):
        return "Politics"
    elif any(keyword in question_lower for keyword in crypto_keywords):
        return "Crypto"
    elif any(keyword in question_lower for keyword in sports_keywords):
        return "Sports"
    else:
        return "Culture"


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Polymarket Analytics API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "markets": "/api/markets",
            "categories": "/api/categories",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    try:
        # Test API connection
        response = requests.get(f"{GAMMA_API}/markets?limit=1", timeout=5)
        api_healthy = response.status_code == 200
    except:
        api_healthy = False

    return {
        "status": "healthy" if api_healthy else "degraded",
        "polymarket_api": "connected" if api_healthy else "disconnected",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/markets")
async def get_markets(
    limit: int = 50,
    category: Optional[str] = None,
    offset: int = 0
):
    """Get live markets with optional filtering"""
    try:
        # Fetch fresh data
        markets = await fetch_live_markets(limit=limit + 50, offset=offset)

        # Filter by category if specified
        if category and category != "All":
            markets = [m for m in markets if m["category"] == category]

        return {
            "success": True,
            "count": len(markets),
            "category": category or "All",
            "markets": markets[:limit],
            "categories": markets_cache["category_counts"],
            "timestamp": markets_cache["timestamp"].isoformat() if markets_cache["timestamp"] else None
        }
    except Exception as e:
        logger.error(f"Error in get_markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories")
async def get_categories():
    """Get available categories and counts"""
    try:
        # Ensure we have fresh data
        if not markets_cache["data"]:
            await fetch_live_markets()

        return {
            "success": True,
            "categories": markets_cache["category_counts"],
            "total_markets": len(markets_cache["data"]) if markets_cache["data"] else 0
        }
    except Exception as e:
        logger.error(f"Error in get_categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orderbook/{token_id}")
async def get_orderbook(token_id: str, limit: int = 20):
    """Get order book for a token"""
    try:
        response = requests.get(
            f"{CLOB_API}/orderbook/{token_id}",
            params={"limit": limit},
            timeout=10
        )
        response.raise_for_status()

        orderbook = response.json()
        return {
            "success": True,
            "token_id": token_id,
            "orderbook": orderbook
        }
    except Exception as e:
        logger.error(f"Error fetching orderbook: {e}")
        return {
            "success": False,
            "error": str(e),
            "token_id": token_id
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
