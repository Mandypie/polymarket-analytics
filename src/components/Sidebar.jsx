import { useState } from "react";
import LastWinningBet from "./cards/LastWinningBet";
import SidebarMarketCards from "./SidebarMarketCards";
import polymarketMarkets from "../mock-data/polymarket-markets.json";

const categories = [
  { label: "Top Markets", icon: "🔥", filter: "top", count: 10 },
  { label: "High Probability", icon: "🎯", filter: "high_prob", count: 8 },
  { label: "Trending", icon: "📈", filter: "trending", count: 10 },
  { label: "New Markets", icon: "🆕", filter: "new", count: 6 },
  { label: "Crypto", icon: "₿", filter: "crypto", count: 10 },
  { label: "Politics", icon: "🏛️", filter: "politics", count: 6 },
  { label: "Sports", icon: "🏆", filter: "sports", count: 15 },
  { label: "Economy", icon: "🌍", filter: "economy", count: 10 },
];

export default function Sidebar() {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [filteredMarkets, setFilteredMarkets] = useState([]);

  const handleCategoryClick = (category) => {
    setSelectedCategory(category.label);

    // Filter markets based on category
    let markets = [];

    if (category.filter === "top") {
      markets = [
        ...polymarketMarkets.politics,
        ...polymarketMarkets.crypto,
        ...polymarketMarkets.sports,
        ...polymarketMarkets.culture
      ].sort((a, b) => b.volume24h - a.volume24h).slice(0, 10);
    } else if (category.filter === "high_prob") {
      markets = [
        ...polymarketMarkets.politics,
        ...polymarketMarkets.crypto,
        ...polymarketMarkets.sports,
        ...polymarketMarkets.culture
      ].filter(m => m.confidence >= 0.70).slice(0, 8);
    } else if (category.filter === "trending") {
      markets = [
        ...polymarketMarkets.politics,
        ...polymarketMarkets.crypto,
        ...polymarketMarkets.sports,
        ...polymarketMarkets.culture
      ].filter(m => m.trend === "up").slice(0, 10);
    } else if (category.filter === "new") {
      markets = [
        ...polymarketMarkets.politics.slice(-2),
        ...polymarketMarkets.crypto.slice(-2),
        ...polymarketMarkets.culture.slice(-2)
      ].slice(0, 6);
    } else if (category.filter === "crypto") {
      markets = polymarketMarkets.crypto;
    } else if (category.filter === "politics") {
      markets = polymarketMarkets.politics;
    } else if (category.filter === "sports") {
      markets = polymarketMarkets.sports;
    } else if (category.filter === "economy") {
      markets = polymarketMarkets.politics.filter(m =>
        m.question.includes("Fed") || m.question.toLowerCase().includes("economy")
      );
    }

    setFilteredMarkets(markets);
  };

  return (
    <>
      <aside className="w-64 bg-premiumDark border-r border-white/5 p-4 space-y-4">

        {/* BRAND */}
        <div className="text-xl font-semibold">
          Polymarket <span className="opacity-60">Premium</span>
        </div>

        {/* 🔥 WINNING CLAIM — MOVED TO TOP */}
        <LastWinningBet />

        {/* CATEGORIES */}
        <nav className="space-y-1">
          {categories.map((c) => (
            <div
              key={c.label}
              onClick={() => handleCategoryClick(c)}
              className={`flex items-center justify-between px-3 py-2
                       rounded-lg text-sm cursor-pointer
                       text-white/80 hover:bg-white/5
                       ${selectedCategory === c.label ? "bg-emerald-500/20 border border-emerald-500/30" : ""}`}
            >
              <div className="flex items-center gap-2">
                <span>{c.icon}</span>
                <span>{c.label}</span>
              </div>
              <span className="text-[11px] text-white/40">
                {c.count} bets
              </span>
            </div>
          ))}
        </nav>

        {/* ONGOING + UPCOMING */}
        <SidebarMarketCards />

      </aside>

      {/* FILTERED MARKETS OVERLAY */}
      {selectedCategory && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedCategory(null)}
        >
          <div
            className="bg-gradient-to-br from-gray-900 to-black border border-emerald-500/30 rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-white/10">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-white">{selectedCategory}</h3>
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="text-white/50 hover:text-white text-2xl"
                >
                  ×
                </button>
              </div>
              <div className="text-sm text-white/50 mt-1">
                {filteredMarkets.length} markets found
              </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {filteredMarkets.map((market) => (
                <div
                  key={market.id}
                  className="bg-white/5 rounded-lg p-4 mb-3 hover:bg-white/10 transition"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <div className="text-sm text-white/60 mb-1">{market.category}</div>
                      <div className="font-semibold text-white mb-2">{market.question}</div>
                      <div className="flex items-center gap-4 text-xs text-white/50">
                        <span>Vol: ${(market.volume24h / 1000000).toFixed(1)}M</span>
                        <span>Liq: ${(market.liquidity / 1000000).toFixed(1)}M</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-white">
                        {(market.yesPrice * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-white/50">YES</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        market.trend === "up" ? "bg-emerald-500/20 text-emerald-400" :
                        market.trend === "down" ? "bg-red-500/20 text-red-400" :
                        "bg-neutral-500/20 text-neutral-400"
                      }`}>
                        {market.trend === "up" ? "↑" : market.trend === "down" ? "↓" : "→"} {market.trend || "stable"}
                      </span>
                      <span className="text-xs text-white/50">
                        Confidence: {(market.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <a
                      href="https://polymarket.com"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold text-center"
                    >
                      View Market
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
