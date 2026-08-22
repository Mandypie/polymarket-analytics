# 🎬 Video Demo Script - Polymarket Analytics Platform

## 📹 How to Record

### Using Windows Built-in Screen Recording:

1. **Open the demos** (already open in Chrome):
   - http://localhost:8502 (working app)
   - pipeline_demo.html (static demo)

2. **Start Recording**:
   - Press `Win + G` to open Game Bar
   - Click the **Record** button (or press `Win + Alt + R`)
   - Wait for "Recording started" notification

3. **Follow This Script** (2-3 minutes):

---

## 🎥 Video Script

### **0:00-0:15 - Introduction**
"Hey, I'm showing you the Polymarket Analytics Platform I built. It's a production-quality analytics application for prediction markets."

### **0:15-0:45 - Project Overview**
(Point to the screen showing the app)
"The platform has a complete data pipeline that ingests from Polymarket's Gamma API, CLOB API, and WebSocket. It separates data into three schemas: Live, Mock, and Resolved."

### **0:45-1:30 - Live Markets Demo**
(Click on "Live Markets" tab)
"Here's the Live Markets view. You can see real-time market data with YES/NO prices, volume, liquidity, and spreads. The sidebar lets you filter by category - Politics, Crypto, Sports, Culture."

(Point to the metrics row)
"These top metrics show total markets, average liquidity, total volume, and how many have tight spreads - all key indicators for trading."

### **1:30-2:00 - Other Tabs**
(Switch between tabs)
"The Mock Data tab is for backtesting strategies. The Resolved Results tab shows historical outcomes. The Analytics tab shows performance by category and signal strength."

### **2:00-2:30 - Technical Stack**
(Open the pipeline_demo.html or show code)
"Under the hood, it's built with:
- Python 3.10+ with FastAPI for the backend
- PostgreSQL + TimescaleDB for time-series data
- Async data ingestion from multiple APIs
- Streamlit for the dashboard
- Docker-ready deployment"

### **2:30-3:00 - Code Structure**
(Show the project folder)
"The repository is properly structured with:
- `/backend/ingestion/` - Data pipeline clients
- `/backend/database/` - SQL migrations and repositories
- `/backend/analytics/` - Edge calculator and signal generator
- `/backend/backtesting/` - Strategy testing engine
- `/frontend/` - Streamlit dashboard"

### **3:00-3:30 - Wrap Up**
"So that's the Polymarket Analytics Platform. Complete data pipeline, three separate database schemas, analytics engine, backtesting module, and a working dashboard. Ready to deploy via Docker."

---

## 🎬 Stop Recording

1. Press `Win + Shift + R` or click **Stop** in Game Bar
2. Video saves to: `C:\Users\YourName\Videos\Captures\`
3. Find the file and share it!

---

## 📝 Alternative: Use PowerPoint

If Game Bar doesn't work:
1. Open PowerPoint
2. **Insert** → **Screen Recording**
3. Select Chrome window
4. Record your demo
5. Save the video

---

## 🔗 What to Show

**MUST SHOW**:
- ✅ Working app at localhost:8502
- ✅ Live Markets tab with data
- ✅ Sidebar filters
- ✅ Metrics display
- ✅ Category tabs (Live/Mock/Resolved/Analytics)

**NICE TO SHOW**:
- Project folder structure
- Database schema files
- Backend code
- Docker setup

---

**Total video length: 2-3 minutes maximum**