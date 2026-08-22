/* =========================================================
   Polymarket Odds Feed (DEMO MODE - Mock Data)
   Real API disabled for demo, using realistic mock data
========================================================= */

import mockPolymarketData from "../mock-data/polymarket-markets.json";

const CACHE = {};
const TTL = 15_000; // 15 seconds

// Demo mode: Return realistic mock odds
export async function getPolymarketOdds(symbol) {
  const now = Date.now();
  const cacheKey = `${symbol}_odds`;

  if (CACHE[cacheKey] && now - CACHE[cacheKey].ts < TTL) {
    return CACHE[cacheKey].data;
  }

  // Demo: Use mock data with realistic odds
  const mockOdds = {
    BTC: { yesPrice: 0.52, noPrice: 0.48, marketProb: 0.52, liquidity: 8500000 },
    ETH: { yesPrice: 0.58, noPrice: 0.42, marketProb: 0.58, liquidity: 6200000 },
    SOL: { yesPrice: 0.61, noPrice: 0.39, marketProb: 0.61, liquidity: 4500000 },
    XRP: { yesPrice: 0.45, noPrice: 0.55, marketProb: 0.45, liquidity: 3200000 }
  };

  const data = mockOdds[symbol] || {
    yesPrice: 0.50,
    noPrice: 0.50,
    marketProb: 0.50,
    liquidity: 5000000
  };

  CACHE[cacheKey] = { data, ts: now };
  return data;
}
