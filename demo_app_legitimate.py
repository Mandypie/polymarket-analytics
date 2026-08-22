"""
Polymarket Analytics Platform - Legitimate Fintech Edition
Professional, clean interface inspired by Bloomberg/TradingView/Polymarket
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# Page configuration
st.set_page_config(
    page_title="Polymarket Analytics",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional fintech CSS - Clean, minimal, data-focused
st.markdown("""
<style>
    /* Reset and base styles - Clean fintech aesthetic */
    .main {
        background-color: #ffffff !important;
    }

    /* Typography - System fonts like real trading platforms */
    html, body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #1a1a1a;
        background-color: #ffffff;
    }

    /* Header - Simple and professional */
    .app-header {
        background: #ffffff;
        border-bottom: 1px solid #e5e7eb;
        padding: 1rem 0;
        margin-bottom: 1.5rem;
    }

    .header-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #111827;
        margin: 0;
    }

    .header-subtitle {
        font-size: 0.875rem;
        color: #6b7280;
        margin: 0.25rem 0 0 0;
    }

    /* KPI row - Clean stat tiles */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .kpi-tile {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 4px;
        padding: 1rem;
    }

    .kpi-label {
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .kpi-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #111827;
        font-family: "SF Mono", "Monaco", "Courier New", monospace;
    }

    .kpi-change {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.25rem;
    }

    .kpi-change.positive {
        color: #059669;
    }

    .kpi-change.negative {
        color: #dc2626;
    }

    /* Data table - Professional spreadsheet style */
    .market-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.875rem;
    }

    .market-table thead {
        background: #f3f4f6;
        border-bottom: 1px solid #d1d5db;
    }

    .market-table th {
        padding: 0.5rem 0.75rem;
        text-align: left;
        font-weight: 600;
        color: #374151;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .market-table td {
        padding: 0.625rem 0.75rem;
        border-bottom: 1px solid #e5e7eb;
        color: #1f2937;
    }

    .market-table tbody tr:hover {
        background: #f9fafb;
    }

    /* Value alignment */
    .text-right { text-align: right; }
    .text-center { text-align: center; }

    /* Price colors - Subtle, not flashy */
    .price-up { color: #059669; }
    .price-down { color: #dc2626; }
    .price-neutral { color: #6b7280; }

    /* Signal badge - Minimal */
    .signal-badge {
        display: inline-block;
        padding: 0.125rem 0.375rem;
        font-size: 0.7rem;
        font-weight: 500;
        border-radius: 2px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .signal-yes {
        background: #d1fae5;
        color: #065f46;
    }

    .signal-no {
        background: #fee2e2;
        color: #991b1b;
    }

    /* Category tag */
    .category-tag {
        display: inline-block;
        padding: 0.125rem 0.5rem;
        font-size: 0.7rem;
        background: #e5e7eb;
        color: #374151;
        border-radius: 2px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Section divider */
    .section-divider {
        border-top: 1px solid #d1d5db;
        margin: 1.5rem 0;
    }

    /* Override Streamlit defaults */
    [data-testid="stMetricValue"] {
        font-family: "SF Mono", "Monaco", "Courier New", monospace;
        color: #111827;
    }

    [data-testid="stSidebar"] {
        background: #f9fafb !important;
        border-right: 1px solid #e5e7eb;
    }

    /* Tabs - Minimal */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        border-bottom: 1px solid #d1d5db;
        gap: 0;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 0;
        padding: 0.625rem 1rem;
        color: #6b7280;
        font-weight: 500;
        font-size: 0.875rem;
    }

    .stTabs [aria-selected="true"] {
        background: transparent;
        color: #111827;
        border-bottom-color: #2563eb;
    }

    /* Table container */
    .table-container {
        border: 1px solid #e5e7eb;
        border-radius: 4px;
        overflow: hidden;
    }

    .table-header {
        background: #f9fafb;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .table-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #111827;
    }

    .table-count {
        font-size: 0.75rem;
        color: #6b7280;
    }

    /* Chart container */
    .chart-container {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Footer */
    .app-footer {
        text-align: center;
        padding: 2rem 0;
        color: #9ca3af;
        font-size: 0.75rem;
        border-top: 1px solid #e5e7eb;
        margin-top: 2rem;
    }

    /* Status indicator */
    .status-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-right: 0.375rem;
    }

    .status-dot.online { background: #059669; }
    .status-dot.offline { background: #dc2626; }

    /* Data quality indicator */
    .quality-badge {
        font-size: 0.7rem;
        padding: 0.125rem 0.375rem;
        background: #ecfdf5;
        color: #047857;
        border-radius: 2px;
        margin-left: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def generate_mock_markets(count=25):
    """Generate realistic mock market data"""
    categories = ["Crypto", "Politics", "Economics", "Sports", "Technology", "World Events"]

    questions = [
        "Will Bitcoin exceed $100,000 by December 2026?",
        "Will Republicans control the House after 2026 midterms?",
        "Will the Fed cut interest rates before March 2026?",
        "Will Ethereum trade above $5,000 in 2026?",
        "Will the US enter a recession in 2026?",
        "Will Solana reach $200 by June 2026?",
        "Will XRP win its SEC lawsuit?",
        "Will crypto market cap exceed $5 trillion in 2026?",
        "Will Tesla announce a new product line in 2026?",
        "Will Polymarket launch derivatives trading?",
        "Will Bitcoin spot ETF exceed $50B AUM?",
        "Will Ethereum flip Bitcoin market cap?",
        "Will the US pass stablecoin legislation in 2026?",
        "Will a major AI company IPO in 2026?",
        "Will the S&P 500 reach 6,000 in 2026?",
        "Will unemployment exceed 6% in 2026?",
        "Will inflation fall below 2% by mid-2026?",
        "Will the US debt exceed $40 trillion?",
        "Will China's GDP growth exceed 5% in 2026?",
        "Will the EU regulate AI more strictly than the US?",
        "Will a major central bank adopt Bitcoin?",
        "Will the SEC approve a crypto options ETF?",
        "Will DeFi TVL exceed $200 billion?",
        "Will a major bank enter the crypto custody market?",
        "Will NFT trading volume exceed $10 billion?"
    ]

    markets = []

    for i in range(min(count, len(questions))):
        # Generate realistic prices
        yes_price = round(random.uniform(0.15, 0.85), 3)
        no_price = round(1 - yes_price, 3)

        # Volume and liquidity
        volume = random.randint(50000, 5000000)
        liquidity = round(volume * random.uniform(0.5, 2.0), 0)

        # Price history for simple charts
        base_price = yes_price
        price_history = []
        for j in range(30):
            change = round(random.uniform(-0.05, 0.05), 4)
            base_price = max(0.01, min(0.99, base_price + change))
            price_history.append(round(base_price, 3))

        # 24h change
        price_change_24h = round(random.uniform(-0.15, 0.15), 3)

        markets.append({
            "id": f"mkt_{i+1:04d}",
            "question": questions[i],
            "category": random.choice(categories),
            "yes_price": yes_price,
            "no_price": no_price,
            "volume_24h": volume,
            "liquidity": liquidity,
            "price_change_24h": price_change_24h,
            "price_history": price_history,
            "end_date": (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
            "traders": random.randint(500, 15000),
            "last_updated": datetime.now()
        })

    # Sort by volume
    markets.sort(key=lambda m: m["volume_24h"], reverse=True)

    return markets


def format_currency(value):
    """Format currency values"""
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:.0f}"


def format_percent(value):
    """Format percentage values"""
    return f"{value*100:.1f}%"


def render_kpi_tiles(markets):
    """Render KPI stat tiles"""
    total_volume = sum(m["volume_24h"] for m in markets)
    total_liquidity = sum(m["liquidity"] for m in markets)
    avg_price = sum(m["yes_price"] for m in markets) / len(markets) if markets else 0
    active_traders = sum(m["traders"] for m in markets)

    # 24h changes for display
    volume_change = round(random.uniform(-10, 15), 1)
    liquidity_change = round(random.uniform(-5, 8), 1)
    price_change = round(random.uniform(-3, 5), 1)
    trader_change = round(random.uniform(-2, 7), 1)

    html = f"""
    <div class="kpi-row">
        <div class="kpi-tile">
            <div class="kpi-label">24h Volume</div>
            <div class="kpi-value">{format_currency(total_volume)}</div>
            <div class="kpi-change {'positive' if volume_change >= 0 else 'negative'}">
                {'+' if volume_change >= 0 else ''}{volume_change}% vs yesterday
            </div>
        </div>
        <div class="kpi-tile">
            <div class="kpi-label">Total Liquidity</div>
            <div class="kpi-value">{format_currency(total_liquidity)}</div>
            <div class="kpi-change {'positive' if liquidity_change >= 0 else 'negative'}">
                {'+' if liquidity_change >= 0 else ''}{liquidity_change}% vs yesterday
            </div>
        </div>
        <div class="kpi-tile">
            <div class="kpi-label">Active Markets</div>
            <div class="kpi-value">{len(markets)}</div>
            <div class="kpi-change">
                Avg price: {format_percent(avg_price)}
            </div>
        </div>
        <div class="kpi-tile">
            <div class="kpi-label">Active Traders</div>
            <div class="kpi-value">{format_currency(active_traders)}</div>
            <div class="kpi-change {'positive' if trader_change >= 0 else 'negative'}">
                {'+' if trader_change >= 0 else ''}{trainer_change}% this week
            </div>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_markets_table(markets):
    """Render markets data table"""
    html = """
    <div class="table-container">
        <div class="table-header">
            <span class="table-title">Active Markets</span>
            <span class="table-count">""" + str(len(markets)) + """ markets</span>
        </div>
        <table class="market-table">
            <thead>
                <tr>
                    <th>Market</th>
                    <th>Category</th>
                    <th class="text-center">Signal</th>
                    <th class="text-right">Yes Price</th>
                    <th class="text-right">No Price</th>
                    <th class="text-right">24h Volume</th>
                    <th class="text-right">Liquidity</th>
                    <th class="text-right">24h Change</th>
                    <th class="text-center">Traders</th>
                    <th class="text-center">End Date</th>
                </tr>
            </thead>
            <tbody>
    """

    for market in markets:
        price_change_class = "price-up" if market["price_change_24h"] > 0 else "price-down" if market["price_change_24h"] < 0 else "price-neutral"
        signal_direction = "YES" if market["yes_price"] > 0.5 else "NO"
        signal_class = "signal-yes" if signal_direction == "YES" else "signal-no"

        html += f"""
                <tr>
                    <td>
                        <div style="font-weight: 500;">{market['question'][:60]}...</div>
                    </td>
                    <td><span class="category-tag">{market['category']}</span></td>
                    <td class="text-center"><span class="signal-badge {signal_class}">{signal_direction}</span></td>
                    <td class="text-right">{format_percent(market['yes_price'])}</td>
                    <td class="text-right">{format_percent(market['no_price'])}</td>
                    <td class="text-right">{format_currency(market['volume_24h'])}</td>
                    <td class="text-right">{format_currency(market['liquidity'])}</td>
                    <td class="text-right {price_change_class}">{'+' if market['price_change_24h'] > 0 else ''}{format_percent(market['price_change_24h'])}</td>
                    <td class="text-center">{format_currency(market['traders'])}</td>
                    <td class="text-center">{market['end_date']}</td>
                </tr>
        """

    html += """
            </tbody>
        </table>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_category_summary(markets):
    """Render category breakdown table"""
    categories = {}
    for market in markets:
        cat = market["category"]
        if cat not in categories:
            categories[cat] = {"count": 0, "volume": 0, "liquidity": 0}
        categories[cat]["count"] += 1
        categories[cat]["volume"] += market["volume_24h"]
        categories[cat]["liquidity"] += market["liquidity"]

    html = """
    <div class="table-container">
        <div class="table-header">
            <span class="table-title">Category Summary</span>
        </div>
        <table class="market-table">
            <thead>
                <tr>
                    <th>Category</th>
                    <th class="text-right">Markets</th>
                    <th class="text-right">24h Volume</th>
                    <th class="text-right">Total Liquidity</th>
                    <th class="text-right">Avg Volume/Market</th>
                </tr>
            </thead>
            <tbody>
    """

    for cat, data in sorted(categories.items(), key=lambda x: x[1]["volume"], reverse=True):
        avg_volume = data["volume"] / data["count"]
        html += f"""
                <tr>
                    <td><span class="category-tag">{cat}</span></td>
                    <td class="text-right">{data['count']}</td>
                    <td class="text-right">{format_currency(data['volume'])}</td>
                    <td class="text-right">{format_currency(data['liquidity'])}</td>
                    <td class="text-right">{format_currency(avg_volume)}</td>
                </tr>
        """

    html += """
            </tbody>
        </table>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def main():
    """Main application"""

    # Header
    st.markdown("""
    <div class="app-header">
        <div class="header-title">Polymarket Analytics</div>
        <div class="header-subtitle">Real-time market data and analytics platform</div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown("""
    <div style="margin-bottom: 1rem;">
        <div style="font-size: 0.875rem; font-weight: 600; color: #111827; margin-bottom: 0.75rem;">Filters</div>
    </div>
    """, unsafe_allow_html=True)

    category_filter = st.sidebar.multiselect(
        "Category",
        options=["Crypto", "Politics", "Economics", "Sports", "Technology", "World Events"],
        default=["Crypto", "Politics", "Economics", "Sports", "Technology", "World Events"]
    )

    min_volume = st.sidebar.slider(
        "Minimum 24h Volume",
        min_value=0,
        max_value=1000000,
        value=50000,
        step=10000,
        format="$%d"
    )

    min_liquidity = st.sidebar.slider(
        "Minimum Liquidity",
        min_value=0,
        max_value=1000000,
        value=100000,
        step=50000,
        format="$%d"
    )

    st.sidebar.divider()

    # System status
    st.sidebar.markdown("""
    <div style="font-size: 0.75rem; color: #6b7280;">
        <div style="margin-bottom: 0.5rem;">
            <span class="status-dot online"></span>
            <span>Data Source: Mock (Demo)</span>
        </div>
        <div style="margin-bottom: 0.5rem;">
            <span class="status-dot online"></span>
            <span>Last Update: Just now</span>
        </div>
        <div>
            <span class="status-dot online"></span>
            <span>Update Frequency: Real-time</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Generate data
    all_markets = generate_mock_markets(25)

    # Apply filters
    filtered_markets = [
        m for m in all_markets
        if m["category"] in category_filter
        and m["volume_24h"] >= min_volume
        and m["liquidity"] >= min_liquidity
    ]

    # Main tabs
    tab1, tab2, tab3 = st.tabs([
        "Markets",
        "Categories",
        "Analytics"
    ])

    # Tab 1: Markets
    with tab1:
        if filtered_markets:
            render_kpi_tiles(filtered_markets)
            render_markets_table(filtered_markets)
        else:
            st.info("No markets match your current filters. Try adjusting the filter criteria.")

    # Tab 2: Categories
    with tab2:
        if filtered_markets:
            render_category_summary(filtered_markets)
        else:
            st.info("No market data available for current filters.")

    # Tab 3: Analytics
    with tab3:
        st.markdown("""
        <div class="table-container">
            <div class="table-header">
                <span class="table-title">Market Analytics</span>
                <span class="quality-badge">Live Data</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="chart-container">
                <div style="font-size: 0.875rem; font-weight: 600; color: #111827; margin-bottom: 1rem;">
                    Volume by Category
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="chart-container">
                <div style="font-size: 0.875rem; font-weight: 600; color: #111827; margin-bottom: 1rem;">
                    Price Distribution
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Performance metrics table
        st.markdown("""
        <div class="table-container">
            <div class="table-header">
                <span class="table-title">Market Performance Metrics</span>
            </div>
            <table class="market-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th class="text-right">Value</th>
                        <th class="text-right">24h Change</th>
                        <th class="text-right">7d Change</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Total Markets</td>
                        <td class="text-right">25</td>
                        <td class="text-right price-up">+2</td>
                        <td class="text-right price-up">+5</td>
                    </tr>
                    <tr>
                        <td>Total Volume</td>
                        <td class="text-right">$48.2M</td>
                        <td class="text-right price-up">+12.3%</td>
                        <td class="text-right price-up">+8.7%</td>
                    </tr>
                    <tr>
                        <td>Average Spread</td>
                        <td class="text-right">0.8%</td>
                        <td class="text-right price-down">-0.1%</td>
                        <td class="text-right price-up">+0.2%</td>
                    </tr>
                    <tr>
                        <td>Active Traders</td>
                        <td class="text-right">18.4K</td>
                        <td class="text-right price-up">+4.2%</td>
                        <td class="text-right price-up">+15.1%</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="app-footer">
        Polymarket Analytics Platform | Data refreshes every 30 seconds | Mock data for demonstration purposes
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
