"""
Polymarket Analytics Platform - Streamlit Dashboard

MVP Dashboard for Polymarket prediction market analytics.
Features:
- Live Markets tab
- Mock Data tab
- Resolved Results tab
- Category filtering
- Data export to CSV
"""

import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Page configuration
st.set_page_config(
    page_title="Polymarket Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .data-table {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


class APIClient:
    """Client for backend API communication"""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to API"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"API Error: {e}")
            return {"success": False, "error": str(e)}


def format_number(num: float, prefix: str = "") -> str:
    """Format number with appropriate suffixes"""
    if num >= 1_000_000:
        return f"{prefix}{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{prefix}{num/1_000:.1f}K"
    else:
        return f"{prefix}{num:.2f}"


def render_market_row(market: Dict) -> None:
    """Render a single market row"""
    col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])

    with col1:
        st.write(f"**{market.get('question', 'N/A')}**")
        st.caption(f"Category: {market.get('category', 'N/A')}")

    with col2:
        st.metric("YES", f"{market.get('yes_price', 0):.2%}")

    with col3:
        st.metric("NO", f"{market.get('no_price', 0):.2%}")

    with col4:
        st.metric("Volume", format_number(market.get('volume_24h', 0), "$"))

    with col5:
        st.metric("Liquidity", format_number(market.get('liquidity', 0), "$"))

    with col6:
        spread = abs(market.get('yes_price', 0) - market.get('no_price', 0))
        st.metric("Spread", f"{spread:.2%}")

    st.divider()


def render_category_performance(client: APIClient) -> None:
    """Render category performance analytics"""
    st.subheader("Category Performance")

    response = client.get("/api/v1/analytics/category-performance")
    if response.get("success") and response.get("performance"):
        perf_data = response["performance"]

        if perf_data:
            df = pd.DataFrame(perf_data)

            # Display metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Categories", len(df))

            with col2:
                total_markets = df["total_markets"].sum()
                st.metric("Total Markets", int(total_markets))

            with col3:
                avg_resolution = df["avg_resolution_price"].mean()
                st.metric("Avg Resolution", f"{avg_resolution:.2%}")

            # Display table
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No category performance data available yet.")
    else:
        st.warning("Category performance analytics coming soon.")


def render_signal_performance(client: APIClient) -> None:
    """Render signal performance by confidence level"""
    st.subheader("Signal Performance by Confidence")

    response = client.get("/api/v1/analytics/signal-performance")
    if response.get("success") and response.get("performance"):
        perf_data = response["performance"]

        if perf_data:
            df = pd.DataFrame(perf_data)

            # Display metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Confidence Levels", len(df))

            with col2:
                avg_win_rate = df["win_rate_pct"].mean()
                st.metric("Avg Win Rate", f"{avg_win_rate:.1f}%")

            with col3:
                total_pnl = df["avg_pnl"].sum()
                st.metric("Total Avg PnL", f"{total_pnl:.4f}")

            # Display table
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No signal performance data available yet.")
    else:
        st.warning("Signal performance analytics coming soon.")


def main():
    """Main application"""

    # Header
    st.markdown('<h1 class="main-header">📊 Polymarket Analytics Platform</h1>', unsafe_allow_html=True)
    st.markdown("Real-time analytics and insights for Polymarket prediction markets")

    # Initialize API client
    client = APIClient()

    # Sidebar
    st.sidebar.title("Filters")

    category_filter = st.sidebar.selectbox(
        "Category",
        options=["All", "Politics", "Sports", "Crypto", "Culture"],
        index=0
    )

    limit = st.sidebar.slider("Markets per page", 10, 100, 50)

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(datetime.now() - timedelta(days=7), datetime.now())
    )

    st.sidebar.divider()

    # Health check
    health = client.get("/health")
    if health.get("status") == "healthy":
        st.sidebar.success("✅ System Healthy")
    else:
        st.sidebar.error("❌ System Issues")

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Live Markets",
        "🧪 Mock Data",
        "✅ Resolved Results",
        "📊 Analytics"
    ])

    # Tab 1: Live Markets
    with tab1:
        st.header("Live Markets")
        st.caption("Real-time market data from Polymarket Gamma API")

        params = {"limit": limit}
        if category_filter != "All":
            params["category"] = category_filter

        response = client.get("/api/v1/markets/live", params)

        if response.get("success") and response.get("markets"):
            markets = response["markets"]

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
                tight_spreads = sum(
                    1 for m in markets
                    if abs(m.get("yes_price", 0) - m.get("no_price", 0)) < 0.02
                )
                st.metric("Tight Spreads", tight_spreads)

            st.divider()

            # Markets list
            st.subheader(f"Markets ({len(markets)})")

            for market in markets:
                render_market_row(market)

            # Export button
            if st.button("📥 Export to CSV", key="export_live"):
                df = pd.DataFrame(markets)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"live_markets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("No live markets available. Check backend connection.")

    # Tab 2: Mock Data
    with tab2:
        st.header("Mock Data (Backtesting)")
        st.caption("Simulated market data for strategy validation")

        # Scenario selector
        scenario = st.text_input("Scenario ID", placeholder="Enter scenario ID...")

        params = {"limit": limit}
        if scenario:
            params["scenario_id"] = scenario

        response = client.get("/api/v1/markets/mock", params)

        if response.get("success") and response.get("markets"):
            markets = response["markets"]

            st.info(f"📊 Found {len(markets)} mock markets")

            # Display mock markets
            for market in markets:
                render_market_row(market)
        else:
            st.info("💡 Mock data will be populated when backtesting scenarios are run.")
            st.write("To create mock data:")
            st.write("1. Navigate to the **Analytics** tab")
            st.write("2. Configure and run a backtesting strategy")
            st.write("3. Results will be stored as mock data for validation")

    # Tab 3: Resolved Results
    with tab3:
        st.header("Resolved Results")
        st.caption("Historical market outcomes for accuracy analysis")

        params = {"limit": limit}
        if category_filter != "All":
            params["category"] = category_filter

        response = client.get("/api/v1/markets/resolved", params)

        if response.get("success") and response.get("markets"):
            markets = response["markets"]

            # Summary metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Resolved Markets", len(markets))

            with col2:
                yes_outcomes = sum(1 for m in markets if m.get("winning_outcome") == "YES")
                st.metric("YES Outcomes", yes_outcomes)

            with col3:
                no_outcomes = sum(1 for m in markets if m.get("winning_outcome") == "NO")
                st.metric("NO Outcomes", no_outcomes)

            st.divider()

            # Resolved markets list
            st.subheader(f"Resolved Markets ({len(markets)})")

            for market in markets:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(f"**{market.get('question', 'N/A')}**")
                    if market.get("resolved_at"):
                        resolved_date = datetime.fromisoformat(market["resolved_at"])
                        st.caption(f"Resolved: {resolved_date.strftime('%Y-%m-%d %H:%M')}")

                with col2:
                    outcome = market.get("winning_outcome", "N/A")
                    if outcome == "YES":
                        st.success(f"**{outcome}**")
                    elif outcome == "NO":
                        st.error(f"**{outcome}**")
                    else:
                        st.info(f"**{outcome}**")

                with col3:
                    st.metric("Resolution Price", f"{market.get('resolution_price', 0):.2%}")

                st.divider()

            # Export button
            if st.button("📥 Export to CSV", key="export_resolved"):
                df = pd.DataFrame(markets)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"resolved_markets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("📅 Resolved markets will appear here as markets settle.")

    # Tab 4: Analytics
    with tab4:
        st.header("Analytics Dashboard")
        st.caption("Performance metrics and insights")

        analytics_tab1, analytics_tab2 = st.tabs(["Category Performance", "Signal Performance"])

        with analytics_tab1:
            render_category_performance(client)

        with analytics_tab2:
            render_signal_performance(client)


if __name__ == "__main__":
    main()
