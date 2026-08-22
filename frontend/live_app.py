"""
Polymarket Analytics - Frontend with LIVE Data
Connects to the production backend for real Polymarket data
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# Configuration
BACKEND_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Polymarket Analytics - LIVE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .live-indicator {
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
</style>
""", unsafe_allow_html=True)


def fetch_markets(category="All", limit=50):
    """Fetch markets from backend API"""
    try:
        params = {"limit": limit}
        if category != "All":
            params["category"] = category

        response = requests.get(f"{BACKEND_URL}/api/markets", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            return data.get("markets", [])
        return []
    except Exception as e:
        st.error(f"Error fetching markets: {e}")
        return []


def fetch_categories():
    """Get available categories"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/categories", timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            return data.get("categories", {})
        return {}
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        return {}


def format_number(num, prefix=""):
    """Format number with appropriate suffixes"""
    if num >= 1_000_000:
        return f"{prefix}{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{prefix}{num/1_000:.1f}K"
    else:
        return f"{prefix}{num:.2f}"


def render_market_row(market):
    """Render a single market row"""
    col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])

    with col1:
        st.write(f"**{market['question']}**")
        cat_color = {
            "Politics": "🔵",
            "Crypto": "🟡",
            "Sports": "🟢",
            "Culture": "🟣"
        }.get(market['category'], "⚪")
        st.caption(f"{cat_color} {market['category']}")

    with col2:
        st.metric("YES", f"{market['yes_price']:.2%}")

    with col3:
        st.metric("NO", f"{market['no_price']:.2%}")

    with col4:
        st.metric("Volume", format_number(market['volume_24h'], "$"))

    with col5:
        st.metric("Liquidity", format_number(market['liquidity'], "$"))

    with col6:
        spread = abs(market['yes_price'] - market['no_price'])
        st.metric("Spread", f"{spread:.2%}")

    st.divider()


def main():
    """Main application"""

    # Header with live indicator
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<h1 class="main-header">📊 Polymarket Analytics Platform</h1>', unsafe_allow_html=True)
    with col2:
        st.markdown('<span class="live-indicator">🔴 LIVE</span>', unsafe_allow_html=True)

    st.markdown("Real-time analytics from Polymarket")

    # Sidebar
    st.sidebar.title("Controls")

    # Health check
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        health = health_response.json()
        if health.get("status") == "healthy":
            st.sidebar.success("✅ Connected to Polymarket")
        else:
            st.sidebar.error("❌ API Issues")
    except:
        st.sidebar.error("❌ Backend Offline")

    st.sidebar.divider()

    category_filter = st.sidebar.selectbox(
        "Category",
        options=["All", "Politics", "Crypto", "Sports", "Culture"],
        index=0
    )

    limit = st.sidebar.slider("Markets to display", 10, 100, 25)

    st.sidebar.divider()

    # Main content
    st.header("📈 Live Markets from Polymarket")
    st.caption("Real-time data from Gamma API")

    # Fetch markets
    with st.spinner("Fetching live markets..."):
        markets = fetch_markets(category=category_filter, limit=limit)

    if markets:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Markets", len(markets))

        with col2:
            avg_liquidity = sum(m.get("liquidity", 0) for m in markets) / len(markets)
            st.metric("Avg Liquidity", format_number(avg_liquidity, "$"))

        with col3:
            total_volume = sum(m.get("volume_24h", 0) for m in markets)
            st.metric("Total Volume", format_number(total_volume, "$"))

        with col4:
            tight_spreads = sum(1 for m in markets if abs(m['yes_price'] - m['no_price']) < 0.02)
            st.metric("Tight Spreads", tight_spreads)

        st.divider()

        # Markets list
        st.subheader(f"Markets ({len(markets)})")

        for market in markets:
            render_market_row(market)

        # Export
        if st.button("📥 Export to CSV"):
            df = pd.DataFrame(markets)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"polymarket_markets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        # Category stats
        categories = fetch_categories()
        if categories:
            st.divider()
            st.subheader("📊 Market Distribution")
            cat_data = {
                "Category": list(categories.keys()),
                "Count": list(categories.values())
            }
            st.bar_chart(cat_data, x="Category", y="Count")

    else:
        st.warning("No markets available. Check backend connection.")


if __name__ == "__main__":
    main()
