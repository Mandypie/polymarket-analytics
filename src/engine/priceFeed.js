/* =========================================================
   Demo Price Feed - Mock Data Mode
   Real API disabled, using realistic mock data for demo
========================================================= */

import mockCandles from "../mock-data/candles-enhanced.json";

const MOCK_PRICES = {
  BTC: 90225.56,
  ETH: 3191.90,
  SOL: 131.00,
  XRP: 2.00
};

export async function getLivePrice(symbol) {
  // Demo mode: Return realistic mock prices with small fluctuations
  const basePrice = MOCK_PRICES[symbol];
  if (!basePrice) return null;

  // Add small realistic fluctuation
  const fluctuation = (Math.random() - 0.5) * (basePrice * 0.001);
  return basePrice + fluctuation;
}
