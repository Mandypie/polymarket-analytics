# 📊 Polymarket Analytics Platform

**Production-quality analytics application for Polymarket prediction markets**

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red.svg)

---

## 🎯 Overview

The Polymarket Analytics Platform transforms raw Polymarket data into actionable insights. It provides real-time market monitoring, strategy backtesting, and historical performance analysis with clear separation between:

- **Live Data** - Real-time markets from Gamma API + CLOB
- **Mock Data** - Simulated markets for strategy validation
- **Resolved Historical Results** - Settled markets for accuracy analysis

---

## ✨ Key Features

### 📈 Real-Time Market Monitoring
- Live market data ingestion from Polymarket Gamma API
- Category-based filtering (Politics, Sports, Crypto, Culture)
- Price tracking with spread analysis
- Liquidity monitoring

### 🧪 Strategy Backtesting
- Mock data generation for simulation
- Strategy validation against historical data
- Performance metrics (ROI, winrate, edge)
- Confidence-based analytics

### 📊 Performance Analytics
- Category performance breakdown
- Signal performance by confidence level
- Win rate and ROI calculations
- Historical trend analysis

### 🚀 Production Ready
- Docker containerization
- PostgreSQL + TimescaleDB for time-series data
- FastAPI backend with async operations
- Streamlit dashboard frontend
- Comprehensive error handling and logging

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Polymarket Analytics Platform                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Frontend   │  │   Backend    │  │   Database   │          │
│  │              │  │   (Python)   │  │ (PostgreSQL) │          │
│  │  Streamlit   │◄─┤   FastAPI    │◄─┤ + TimescaleDB│          │
│  │    MVP       │  │              │  │              │          │
│  └──────────────┘  └──────┬───────┘  └──────────────┘          │
│                           │                                     │
│                    ┌──────┴───────┐                            │
│                    │  Data Pipeline│                            │
│                    │              │                            │
│              ┌─────┴────────┬─────┴────┐                       │
│              │              │           │                       │
│         ┌────▼───┐    ┌────▼───┐  ┌───▼────┐                 │
│         │ Gamma  │    │  CLOB  │  │  Mock  │                 │
│         │   API  │    │   API  │  │  Data  │                 │
│         └────────┘    └────────┘  └────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
polymarket-analytics/
├── backend/                      # Python backend
│   ├── database/
│   │   ├── migrations/          # SQL migration files
│   │   ├── connection.py        # Database connection
│   │   └── models.py            # Data models
│   ├── ingestion/               # Data pipeline
│   │   ├── gamma_client.py      # Gamma API client
│   │   ├── clob_client.py       # CLOB API client
│   │   ├── websocket_client.py  # WebSocket client
│   │   └── ingestion_service.py # Main ingestion service
│   ├── analytics/               # Analytics modules
│   │   ├── edge_calculator.py   # Edge calculations
│   │   ├── confidence_analytics.py
│   │   ├── roi_calculator.py
│   │   └── signal_analytics.py
│   ├── backtesting/             # Backtesting engine
│   │   ├── strategy.py
│   │   ├── backtester.py
│   │   └── metrics.py
│   ├── monitoring/              # Logging & monitoring
│   │   └── logger.py
│   └── main.py                  # FastAPI application
│
├── frontend/                     # Streamlit dashboard
│   ├── app.py                   # Main dashboard
│   ├── pages/                   # Page components
│   └── utils/                   # Utilities
│       ├── api_client.py       # Backend API client
│       └── charts.py           # Chart utilities
│
├── docker/                       # Docker configuration
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
├── requirements.txt              # Backend dependencies
├── requirements-frontend.txt     # Frontend dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (if running locally)
- PostgreSQL 16+ (if running locally)

### Option 1: Docker (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd polymarket-analytics
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

5. **Stop services**
```bash
docker-compose down
```

### Option 2: Local Development

1. **Install dependencies**
```bash
# Backend
pip install -r requirements.txt

# Frontend
pip install -r requirements-frontend.txt
```

2. **Set up PostgreSQL**
```bash
# Start PostgreSQL with TimescaleDB
docker run -d -p 5432:5432 \
  -e POSTGRES_DB=polymarket \
  -e POSTGRES_USER=polymarket \
  -e POSTGRES_PASSWORD=your_password \
  timescale/timescaledb:latest-pg16
```

3. **Run migrations**
```bash
psql -h localhost -U polymarket -d polymarket -f backend/database/migrations/001_create_schemas.sql
psql -h localhost -U polymarket -d polymarket -f backend/database/migrations/002_create_live_markets.sql
psql -h localhost -U polymarket -d polymarket -f backend/database/migrations/003_create_mock_data.sql
psql -h localhost -U polymarket -d polymarket -f backend/database/migrations/004_create_resolved_markets.sql
```

4. **Start backend**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

5. **Start frontend**
```bash
cd frontend
streamlit run app.py --server.port 8501
```

---

## 📡 API Endpoints

### Health & Info
- `GET /` - API information
- `GET /health` - Health check

### Markets
- `GET /api/v1/markets/live` - Live markets (category, limit params)
- `GET /api/v1/markets/mock` - Mock markets (scenario_id, limit params)
- `GET /api/v1/markets/resolved` - Resolved markets (category, limit params)

### Analytics
- `GET /api/v1/analytics/category-performance` - Performance by category
- `GET /api/v1/analytics/signal-performance` - Performance by confidence level

### Interactive API Documentation
Visit http://localhost:8000/docs for interactive API documentation.

---

## 🗄️ Database Schema

### Schemas

1. **`live`** - Real-time market data
   - `markets` - Active market information
   - `market_prices` - Time-series price history (TimescaleDB hypertable)

2. **`mock`** - Simulated data for backtesting
   - `markets` - Simulated market scenarios
   - `signals` - Simulated trading signals

3. **`resolved`** - Historical results
   - `markets` - Settled market outcomes
   - `signals` - Historical signal performance
   - Views: `category_performance`, `signal_performance`

---

## 🔧 Configuration

### Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=polymarket
DB_PASSWORD=your_password
DB_NAME=polymarket

# API URLs
GAMMA_API_URL=https://gamma-api.polymarket.com
CLOB_API_URL=https://clob.polymarket.com
WS_URL=wss://api.polymarket.us/v1/ws/markets

# Application
LOG_LEVEL=INFO
TZ=UTC

# Frontend
BACKEND_URL=http://localhost:8000
```

---

## 📊 Dashboard Features

### Live Markets Tab
- Real-time market data from Polymarket
- Category filtering (Politics, Sports, Crypto, Culture)
- Price, volume, and liquidity metrics
- Spread analysis
- Export to CSV

### Mock Data Tab
- Simulated market scenarios
- Strategy validation data
- Backtesting results

### Resolved Results Tab
- Historical market outcomes
- Category performance breakdown
- Winning/losing outcome analysis
- Export to CSV

### Analytics Tab
- Category performance metrics
- Signal performance by confidence level
- Win rate and ROI statistics
- Trend analysis

---

## 🧪 Development

### Running Tests
```bash
# Backend tests
pytest backend/tests/

# Analytics module tests
pytest backend/analytics/tests/
```

### Database Migrations
```bash
# Create new migration
# Add SQL file to backend/database/migrations/
# Run: psql -h localhost -U polymarket -d polymarket -f migration_file.sql
```

### Adding New Features
1. Backend: Add new endpoint in `backend/main.py`
2. Frontend: Update `frontend/app.py`
3. Database: Create migration in `backend/database/migrations/`

---

## 📈 Monitoring & Logging

### Logs Location
- Backend: `backend/logs/`
- Docker: Container logs (`docker-compose logs`)

### Health Monitoring
- API health: `GET /health`
- Database health: Included in health check
- Service status: Check sidebar in dashboard

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🔗 Links & Resources

- [Polymarket Documentation](https://docs.polymarket.com/)
- [Polymarket Python SDK](https://github.com/Polymarket/py-sdk)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [TimescaleDB Documentation](https://docs.timescale.com/)

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: [Your contact information]

---

**Built with ❤️ for the Polymarket community**
