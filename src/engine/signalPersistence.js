/* =========================================================
   SIGNAL PERSISTENCE (LOCAL STORAGE)
   Used for analytics + reload survival
========================================================= */

const STORAGE_KEY = "pm_resolved_signals_v1";
const MAX_SIGNALS = 500;

/* ---------------------------------------------------------
   Load persisted resolved signals
--------------------------------------------------------- */
export function loadResolvedSignals() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

/* ---------------------------------------------------------
   Persist a resolved signal (deduped)
--------------------------------------------------------- */
export function persistResolvedSignal(signal) {
  if (!signal || !signal.id || !signal.resolved) return;

  const existing = loadResolvedSignals();

  // prevent duplicates
  if (existing.find(s => s.id === signal.id)) return;

  const updated = [signal, ...existing].slice(0, MAX_SIGNALS);

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // fail silently (quota / private mode)
  }
}

/* ---------------------------------------------------------
   Seed resolved signals ONCE (dashboard never empty)
   Demo mode: Auto-seed with realistic performance data
--------------------------------------------------------- */
import seedData from "../mock-data/signal-history-seed.json";

let seeded = false;

export function seedResolvedSignals(seed = []) {
  if (seeded) return;
  seeded = true;

  const existing = loadResolvedSignals();
  if (existing.length > 0) return;

  // Use demo seed data if no custom seed provided
  const seedSignals = seed.length > 0 ? seed : seedData.signals;

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(seedSignals));
    console.log(`[Demo] Seeded ${seedSignals.length} historical signals`);
  } catch {
    // ignore
  }
}
