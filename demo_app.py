"""
Polymarket Analytics Platform - Standalone Demo

This version doesn't require database or external APIs.
It shows the dashboard with mock data to demonstrate the UI and functionality.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="Polymarket Analytics - Demo",
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
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def generate_mock_markets(count=20):
    """Generate mock market data"""
    categories = ["Politics", "Sports", "Crypto", "Culture"]
    questions = [
        "Will Bitcoin exceed $100K by 2026?",
        "Republicans win House majority?",
        "Ethereum above $5K by EOY?",
        "Super Bowl winner: Chiefs or 49ers?",
        "Crypto market cap > $5T?",
        "Will the Fed cut rates in 2026?",
        "Solana reaches $200?",
        "Oscar Best Picture: Drama vs Comedy?",
        "US enters recession in 2026?",
        "XRP wins SEC lawsuit?"
    ]

    markets = []
    for i in range(min(count, len(questions))):
        import random
        yes_price = round(random.uniform(0.3, 0.7), 2)
        markets.append({
            "market_id": f"market_{i+1}",
            "question": questions[i],
            "yes_price": yes_price,
            "no_price": round(1 - yes_price, 2),
            "volume_24h": random.randint(100000, 5000000),
            "liquidity": random.randint(50000, 2000000),
            "category": random.choice(categories),
            "updated_at": datetime.now().isoformat()
        })
    return markets


def generate_mock_performance():
    """Generate mock performance data"""
    return [
        {"category": "Politics", "total_markets": 45, "yes_outcomes": 28, "no_outcomes": 17},
        {"category": "Sports", "total_markets": 32, "yes_outcomes": 15, "no_outcomes": 17},
        {"category": "Crypto", "total_markets": 28, "yes_outcomes": 19, "no_outcomes": 9},
        {"category": "Culture", "total_markets": 18, "yes_outcomes": 11, "no_outcomes": 7}
    ]


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
        st.caption(f"Category: {market['category']}")

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
    """Main demo application"""

    # Demo banner
    st.markdown('<div class="success-box">🎯 <strong>DEMO MODE</strong> - Running with mock data (no database required)</div>', unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">📊 Polymarket Analytics Platform</h1>', unsafe_allow_html=True)
    st.markdown("Real-time analytics and insights for Polymarket prediction markets")

    # Sidebar
    st.sidebar.title("Demo Controls")

    category_filter = st.sidebar.selectbox(
        "Category",
        options=["All", "Politics", "Sports", "Crypto", "Culture"],
        index=0
    )

    market_count = st.sidebar.slider("Markets to display", 5, 20, 10)

    st.sidebar.divider()
    st.sidebar.info("💡 This is a demo version showing the UI and functionality with mock data.")

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Live Markets",
        "🧪 Mock Data",
        "✅ Resolved Results",
        "📊 Analytics"
    ])

    # Tab 1: Live Markets
    with tab1:
        st.header("Live Markets (Demo)")
        st.caption("Mock market data to demonstrate the interface")

        markets = generate_mock_markets(market_count)

        if category_filter != "All":
            markets = [m for m in markets if m["category"] == category_filter]

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Markets", len(markets))
        with col2:
            avg_liquidity = sum(m["liquidity"] for m in markets) / len(markets)
            st.metric("Avg Liquidity", format_number(avg_liquidity, "$"))
        with col3:
            total_volume = sum(m["volume_24h"] for m in markets)
            st.metric("Total Volume", format_number(total_volume, "$"))
        with col4:
            tight_spreads = sum(1 for m in markets if abs(m["yes_price"] - m["no_price"]) < 0.02)
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
                file_name=f"demo_markets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    # Tab 2: Mock Data
    with tab2:
        st.header("Mock Data (Demo)")
        st.info("🧪 In the full version, this tab shows simulated markets for backtesting strategies")
        st.write("Features coming in the full production version:")
        st.markdown("""
        - Strategy simulation
        - Historical scenario testing
        - Edge validation
        - Risk-free backtesting environment
        """)

    # Tab 3: Resolved Results
    with tab3:
        st.header("Resolved Results (Demo)")
        st.info("📅 In the full version, this tab shows historical market outcomes")

        performance = generate_mock_performance()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Resolved", sum(p["total_markets"] for p in performance))
        with col2:
            st.metric("YES Outcomes", sum(p["yes_outcomes"] for p in performance))
        with col3:
            st.metric("NO Outcomes", sum(p["no_outcomes"] for p in performance))

        st.divider()

        st.subheader("Category Performance")
        df = pd.DataFrame(performance)
        st.dataframe(df, use_container_width=True)

    # Tab 4: Analytics
    with tab4:
        st.header("Analytics Dashboard")
        st.info("📊 In the full version, this tab shows detailed performance analytics")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Signal Performance")
            st.write("Confidence-based win rates:")
            st.metric("80%+ Confidence", "72% win rate")
            st.metric("70-79% Confidence", "65% win rate")
            st.metric("60-69% Confidence", "58% win rate")

        with col2:
            st.subheader("ROI Analysis")
            st.write("Average returns by category:")
            st.metric("Crypto", "+12.4% ROI")
            st.metric("Politics", "+8.7% ROI")
            st.metric("Sports", "+5.2% ROI")

    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <strong>Polymarket Analytics Platform - Demo Version</strong><br>
        Built with FastAPI, PostgreSQL + TimescaleDB, and Streamlit<br>
        <a href="https://github.com/Polymarket/py-sdk">Powered by Polymarket Python SDK</a>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
