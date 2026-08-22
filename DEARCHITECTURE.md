# PolyMarket Analytics Platform - Architecture & Hiring Demo

## Live Dashboard
**Currently Running:** http://localhost:5173/

## Current Implementation Status

### ✅ Built & Working
| Component | Status | Tech Stack |
|-----------|--------|------------|
| Real-time Dashboard | ✅ Live | React + Vite + Tailwind CSS |
| Price Feed Integration | ✅ Live | Binance WebSocket API |
| Signal Engine | ✅ Live | Crypto15mSignalEngine.js |
| Confidence Analytics | ✅ Live | confidenceCalibrator.js |
| Liquidity Heatmap | ✅ Live | LiquidityHeatmap.jsx |
| Orderbook Visualization | ✅ Live | YesNoOrderbook.jsx |
| Performance Charts | ✅ Live | Recharts (Win Rate, PnL, Capital Curve) |
| Execution Gate | ✅ Live | Hard-disabled (read-only) |

---

## Target Architecture: 3-Tier Data System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POLYMARKET ANALYTICS PLATFORM                             │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   LIVE DATA     │  │   MOCK DATA     │  │   RESOLVED HISTORY          │  │
│  │   (Real-time)   │  │   (Testing)     │  │   (Backtesting)             │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬──────────────┘  │
│           │                    │                          │                  │
│           ▼                    ▼                          ▼                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              TIMESCALEDB HYPERTABLES (Time-Series Data)              │  │
│  │                                                                      │  │
│  │  • live_markets      • mock_markets       • resolved_markets         │  │
│  │  • price_ticks       • synthetic_orders   • settlement_results       │  │
│  │  • orderbook_depth   • test_strategies   • performance_metrics      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                   │                                          │
│                                   ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    ANALYTICS ENGINE (Python/FastAPI)                  │  │
│  │                                                                      │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │  │
│  │  │  ROI Calculator │  │  Winrate Engine │  │  Kelly Sizing      │ │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │  │
│  │  │ Volume Analysis │  │ Liquidity Calc  │  │ Edge Detection     │ │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                   │                                          │
│                                   ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     DASHBOARD (Next.js / Streamlit)                    │  │
│  │                                                                      │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │  │
│  │  │ Politics │  │  Sports  │  │  Crypto  │  │ Culture │ More...      │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘ │  │
│  │                                                                      │  │
│  │  Tab: LIVE │ Tab: MOCK │ Tab: RESOLVED                              │  │
│  │                                                                      │  │
│  │  Most Profitable Predictions | ROI by Category | Winrate Trends    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Pipeline Architecture

### Phase 1: Ingestion Layer
```python
# FastAPI WebSocket Ingestion Service
from fastapi import WebSocket
from sqlalchemy import insert
from datetime import datetime

class PolymarketIngestionService:
    """
    Separates incoming data into 3 distinct schemas:
    1. LIVE - Real-time from Gamma API + CLOB
    2. MOCK - Generated for backtesting
    3. RESOLVED - Historical settlement data
    """
    
    async def ingest_live_market(self, data: dict):
        """Store live market data with 'live' schema tag"""
        await self.db.execute(
            insert(live_markets).values(
                market_id=data['id'],
                question=data['question'],
                yes_price=data['yesPrice'],
                no_price=data['noPrice'],
                volume_24h=data['volume24h'],
                timestamp=datetime.utcnow(),
                schema_tag='live'  # Critical separation
            )
        )
    
    async def ingest_mock_data(self, synthetic_data: dict):
        """Store backtesting data with 'mock' schema tag"""
        await self.db.execute(
            insert(mock_markets).values(
                **synthetic_data,
                schema_tag='mock'  # Never mixed with live
            )
        )
    
    async def ingest_resolved(self, settled_market: dict):
        """Store resolved markets with 'resolved' schema tag"""
        await self.db.execute(
            insert(resolved_markets).values(
                **settled_market,
                schema_tag='resolved',
                settled_at=datetime.utcnow()
            )
        )
```

### Phase 2: Database Schema (TimescaleDB)
```sql
-- LIVE Markets Hypertable
CREATE TABLE live_markets (
    market_id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    category TEXT NOT NULL,  -- Politics, Sports, Crypto, Culture
    yes_price FLOAT,
    no_price FLOAT,
    volume_24h FLOAT,
    liquidity FLOAT,
    timestamp TIMESTAMPTZ NOT NULL,
    schema_tag TEXT CHECK (schema_tag = 'live')
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('live_markets', 'timestamp');

-- MOCK Markets (Isolated Schema)
CREATE TABLE mock_markets (
    market_id TEXT,
    synthetic_strategy_id TEXT,
    generated_prices JSONB,
    timestamp TIMESTAMPTZ NOT NULL,
    schema_tag TEXT CHECK (schema_tag = 'mock')
);

SELECT create_hypertable('mock_markets', 'timestamp');

-- RESOLVED Markets (Historical Truth)
CREATE TABLE resolved_markets (
    market_id TEXT PRIMARY KEY,
    question TEXT,
    outcome TEXT,  -- YES/NO
    settlement_price FLOAT,
    resolved_at TIMESTAMPTZ,
    schema_tag TEXT CHECK (schema_tag = 'resolved')
);
```

### Phase 3: Analytics Engine
```python
# analytics/most_profitable.py
from sqlalchemy import select, func
from models import ResolvedMarket, LiveMarket

class MostProfitablePredictions:
    """
    Ranks predictions by ROI across categories
    Uses ONLY resolved historical data (no mixing with mock)
    """
    
    def get_top_predictions(self, category: str = None, limit: int = 10):
        """
        Returns most profitable predictions by chosen category
        Pure analytics - no simulated returns
        """
        query = (
            select(
                ResolvedMarket.category,
                ResolvedMarket.question,
                (ResolvedMarket.settlement_price - ResolvedMarket.entry_price)
                .label('roi_per_token'),
                ResolvedMarket.volume_24h,
                ResolvedMarket.resolved_at
            )
            .where(ResolvedMarket.schema_tag == 'resolved')
            .order_by(desc('roi_per_token'))
        )
        
        if category:
            query = query.where(ResolvedMarket.category == category)
        
        return query.limit(limit).all()
```

---

## Implementation Roadmap

### Week 1-2: Data Pipeline Foundation
- [ ] FastAPI WebSocket server for Gamma API + CLOB
- [ ] PostgreSQL + TimescaleDB setup
- [ ] Schema separation (Live/Mock/Resolved)
- [ ] Async ingestion with schema tagging

### Week 3-4: Analytics Engine
- [ ] ROI calculator per category
- [ ] Winrate aggregation engine
- [ ] Volume & liquidity metrics
- [ ] "Most Profitable" ranking algorithm

### Week 5-6: Dashboard & Integration
- [ ] Next.js or Streamlit UI
- [ ] Category filters (Politics/Sports/Crypto/Culture)
- [ ] Tabs: Live | Mock | Resolved
- [ ] Charts + CSV export

### Week 7-8: Backtesting & Monitoring
- [ ] Mock strategy simulation engine
- [ ] Historical validation module
- [ ] Docker deployment
- [ ] Error alerts & logging

---

## Tech Stack Alignment

| Requirement | Current | Target |
|-------------|---------|--------|
| Backend | React frontend | Python FastAPI |
| Database | In-memory state | PostgreSQL + TimescaleDB |
| WebSocket | Binance feed only | Polymarket CLOB integration |
| Analytics | Basic engine | Full ROI/Winrate/Kelly engine |
| Frontend | React/Vite | Next.js or Streamlit |
| Deployment | Local dev | Docker + Cloud |

---

## Current Dashboard Features (What's Working Now)

1. **High-Confidence Signal Grid**
   - Real-time crypto signals (BTC, ETH, SOL, XRP)
   - 15-minute observation windows
   - LEANS_YES / LEANS_NO indicators

2. **Performance Analytics**
   - Confidence vs Win Rate chart
   - Entry Timing vs PnL analysis
   - Capital Curve visualization

3. **Market Intelligence**
   - Liquidity Heatmap (5m/15m/1h timeframes)
   - Orderbook depth visualization
   - Price movement tracking

4. **Safety Features**
   - Execution hard-disabled
   - Drawdown guardrails
   - Regime filtering

---

## Key Differentiator for Hiring

This project demonstrates:
- **Real working dashboard** (not just design)
- **API integration** (Gamma API, Binance WebSocket)
- **Signal engineering** (confidence calibration, edge detection)
- **Read-only architecture** (safe for compliance review)
- **Clear vision** for 3-tier data separation

The hired developer will:
1. **Productize** this working prototype
2. **Add PostgreSQL/TimescaleDB** for structured storage
3. **Implement Python FastAPI** backend
4. **Build category-based analytics** (Politics/Sports/Crypto/Culture)
5. **Add backtesting module** for mock strategies

---

## Next Steps for Demo

1. ✅ Dashboard running at http://localhost:5173/
2. 📋 Review this architecture document
3. 🎯 Discuss implementation timeline
4. 💰 Negotiate budget (3-week MVP vs 6-week full product)

---

**Project Repo:** https://github.com/DreamOfTrading/PolyMarket-Extractor
**Tech Stack:** React, Vite, Tailwind CSS, Recharts, WebSocket APIs
**Target Stack:** Python FastAPI, PostgreSQL, TimescaleDB, Next.js/Streamlit, Docker
