import { useEffect, useRef, useState } from "react";
import { getActive15mSignals } from "../engine/Crypto15mSignalEngine";
import ConfidenceExplanation from "./ConfidenceExplanation";

const ASSETS = ["BTC", "ETH", "SOL", "XRP"];

function formatTime(ms) {
  if (!Number.isFinite(ms) || ms <= 0) return "0:00";
  const m = Math.floor(ms / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function Crypto15mSignalGrid() {
  const [signals, setSignals] = useState({});
  const [selectedSignal, setSelectedSignal] = useState(null);
  const stripRef = useRef(null);

  useEffect(() => {
    const tick = () => setSignals(getActive15mSignals());
    tick();
    const i = setInterval(tick, 1000);
    return () => clearInterval(i);
  }, []);

  const handleSignalClick = (asset, signal) => {
    const priceComparison = {
      asset,
      currentPrice: signal.priceAtStart,
      entryPrice: signal.priceAtStart,
      targetPrice: signal.priceAtStart * 1.02, // 2% target for demo
      confidence: (signal.confidence * 100).toFixed(0),
      direction: signal.direction,
      timeframe: "15m",
      edge: signal.edge ? (signal.edge * 100).toFixed(1) : "N/A",
      recommendation: signal.direction === "LEANS_YES" ? "LONG" : "SHORT"
    };
    setSelectedSignal(priceComparison);
  };

  return (
    <div
      ref={stripRef}
      className="
        grid
        w-full
        grid-cols-1
        sm:grid-cols-2
        lg:grid-cols-4
        gap-5
      "
    >
      {ASSETS.map((asset) => {
        const s = signals[asset];
        if (!s) return null;

        const remaining = s.resolveAt ? (s.resolveAt - Date.now()) : (s.observeUntil - Date.now());
        const confidencePct = Math.round(s.confidence * 100);
        const isUrgent = remaining < 5 * 60 * 1000;

        return (
          <div
            key={s.id}
            onClick={() => handleSignalClick(asset, s)}
            className={`
              card
              p-5
              space-y-4
              bg-gradient-to-br from-black/80 to-black/95
              cursor-pointer
              hover:border-emerald-500/50
              transition-all
              ${isUrgent ? "resolve-border" : ""}
            `}
          >
            {/* HEADER */}
            <div className="flex justify-between">
              <div>
                <div className="text-base font-semibold">
                  {asset} · 15m
                </div>

                <div
                  className={`text-sm font-semibold flex items-center gap-1 ${
                    isUrgent ? "fire" : "text-red-400"
                  }`}
                >
                  🔥 Resolve in {formatTime(remaining)}
                </div>
              </div>

              <div className="text-right">
                <div className="text-3xl font-extrabold leading-none">
                  {confidencePct}%
                </div>
                <div className="text-sm opacity-70">
                  {s.direction || s.bias}
                </div>
              </div>
            </div>

            {/* PRICE INFO FOR COMPARISON */}
            <div className="text-xs text-white/50">
              Current: ${s.priceAtStart?.toFixed(2) || "N/A"}
            </div>

            {/* ANALYTICS STATUS */}
            <div className="text-sm font-semibold text-white/40">
              Analytics only · Execution disabled
            </div>

            {/* ACTIONS (SAFE) */}
            <div className="flex gap-3">
              <a
                href="https://polymarket.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 py-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-white text-sm font-semibold text-center"
              >
                View Market ↗
              </a>

              <button
                onClick={() =>
                  navigator.clipboard.writeText(
                    `${asset} ${s.direction} · ${confidencePct}%\nResolve in ${formatTime(
                      remaining
                    )}`
                  )
                }
                className="flex-1 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 text-white text-sm font-semibold"
              >
                Copy Thesis
              </button>
            </div>

            {/* CONFIDENCE EXPLANATION */}
            <div className="bg-black/40 rounded-lg p-3 decay">
              <ConfidenceExplanation signal={s} />
            </div>

            {/* FOOTER */}
            <div className="flex justify-between text-sm text-white/50">
              <span>Why this signal?</span>
              <span className="italic">Model-derived analytics</span>
            </div>
          </div>
        );
      })}

      {/* PRICE COMPARISON MODAL */}
      {selectedSignal && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50"
          onClick={() => setSelectedSignal(null)}
        >
          <div
            className="bg-gradient-to-br from-gray-900 to-black border border-emerald-500/30 rounded-2xl p-6 max-w-md w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white">
                {selectedSignal.asset} Signal Analysis
              </h3>
              <button
                onClick={() => setSelectedSignal(null)}
                className="text-white/50 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              {/* Signal Summary */}
              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                <div className="text-sm text-emerald-400 mb-1">RECOMMENDATION</div>
                <div className="text-2xl font-bold text-white">{selectedSignal.recommendation}</div>
                <div className="text-sm text-white/60">{selectedSignal.direction}</div>
              </div>

              {/* Price Comparison */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white/5 rounded-lg p-3">
                  <div className="text-xs text-white/50 mb-1">CURRENT PRICE</div>
                  <div className="text-lg font-semibold text-white">
                    ${selectedSignal.currentPrice?.toFixed(2) || "N/A"}
                  </div>
                </div>
                <div className="bg-white/5 rounded-lg p-3">
                  <div className="text-xs text-white/50 mb-1">TARGET PRICE</div>
                  <div className="text-lg font-semibold text-emerald-400">
                    ${selectedSignal.targetPrice?.toFixed(2) || "N/A"}
                  </div>
                </div>
              </div>

              {/* Key Metrics */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-white/50">Confidence</span>
                  <span className="text-white font-semibold">{selectedSignal.confidence}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white/50">Expected Edge</span>
                  <span className="text-emerald-400 font-semibold">{selectedSignal.edge}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white/50">Timeframe</span>
                  <span className="text-white font-semibold">{selectedSignal.timeframe}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white/50">Potential Return</span>
                  <span className="text-emerald-400 font-semibold">
                    {selectedSignal.direction === "LEANS_YES" ? "+" : "-"}2.0%
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(selectedSignal, null, 2));
                    alert("Analysis copied to clipboard!");
                  }}
                  className="flex-1 py-3 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-white text-sm font-semibold"
                >
                  Copy Analysis
                </button>
                <a
                  href="https://polymarket.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold text-center"
                >
                  View Market ↗
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
