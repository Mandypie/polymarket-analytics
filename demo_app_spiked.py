"""
Polymarket Analytics Platform - SPIKED Demo
Dark mode terminal aesthetic with signal-focused design
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import json

# Page configuration
st.set_page_config(
    page_title="COMMAND CENTER // Polymarket Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SPIKED DESIGN CSS
st.markdown("""
<style>
    /* Core palette - Dark Terminal Aesthetic */
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-card: #1a1a24;
        --accent-success: #00ff9f;
        --accent-danger: #ff4757;
        --accent-warn: #ffa502;
        --accent-info: #2ed573;
        --accent-purple: #a855f7;
        --text-primary: #e4e4e7;
        --text-muted: #71717a;
        --border-subtle: #2a2a35;
    }

    /* Override Streamlit base */
    .main {
        background: var(--bg-primary) !important;
    }

    /* Global text overrides */
    html, body, [class*="css"]  {
        color: var(--text-primary) !important;
        background-color: var(--bg-primary) !important;
    }

    /* Command Center Header */
    .command-header {
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        border-bottom: 2px solid var(--accent-success);
        padding: 1.5rem 2rem;
        margin-bottom: 1rem;
        position: relative;
    }

    .command-header h1 {
        color: var(--accent-success) !important;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 2px;
        margin: 0;
        text-shadow: 0 0 20px rgba(0, 255, 159, 0.3);
    }

    .command-header .subtitle {
        color: var(--text-muted);
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-top: 0.5rem;
    }

    /* Signal Card Container */
    .signal-grid {
        display: grid;
        gap: 1rem;
        margin-top: 1rem;
    }

    /* Individual Signal Card */
    .signal-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-left: 4px solid var(--accent-success);
        border-radius: 8px;
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .signal-card:hover {
        border-color: var(--accent-success);
        box-shadow: 0 0 30px rgba(0, 255, 159, 0.1);
        transform: translateX(5px);
    }

    .signal-card.bearish {
        border-left-color: var(--accent-danger);
    }

    .signal-card.bearish:hover {
        border-color: var(--accent-danger);
        box-shadow: 0 0 30px rgba(255, 71, 87, 0.1);
    }

    /* Pulse Animation for Fresh Signals */
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 159, 0.3); }
        50% { box-shadow: 0 0 40px rgba(0, 255, 159, 0.6); }
    }

    .signal-card.fresh {
        animation: pulse-glow 2s ease-in-out infinite;
    }

    /* Signal Card Header */
    .signal-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1rem;
    }

    .signal-question {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.4;
    }

    .signal-badges {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .signal-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    .badge-fresh {
        background: rgba(0, 255, 159, 0.15);
        color: var(--accent-success);
        border: 1px solid var(--accent-success);
        animation: badge-pulse 1.5s ease-in-out infinite;
    }

    .badge-recent {
        background: rgba(46, 213, 115, 0.15);
        color: var(--accent-info);
        border: 1px solid var(--accent-info);
    }

    .badge-stale {
        background: rgba(113, 113, 122, 0.15);
        color: var(--text-muted);
        border: 1px solid var(--text-muted);
    }

    @keyframes badge-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    /* Pattern Strength Badges */
    .strength-very-strong {
        background: rgba(0, 255, 159, 0.2);
        color: var(--accent-success);
        border: 1px solid var(--accent-success);
    }

    .strength-strong {
        background: rgba(46, 213, 115, 0.2);
        color: var(--accent-info);
        border: 1px solid var(--accent-info);
    }

    .strength-moderate {
        background: rgba(255, 165, 2, 0.2);
        color: var(--accent-warn);
        border: 1px solid var(--accent-warn);
    }

    .strength-weak {
        background: rgba(255, 71, 87, 0.2);
        color: var(--accent-danger);
        border: 1px solid var(--accent-danger);
    }

    /* Confidence Meter */
    .confidence-section {
        margin: 1rem 0;
    }

    .confidence-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .confidence-bar {
        height: 8px;
        background: var(--bg-secondary);
        border-radius: 4px;
        overflow: hidden;
        position: relative;
    }

    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--accent-info), var(--accent-success));
        border-radius: 4px;
        position: relative;
        transition: width 0.5s ease;
    }

    .confidence-fill.high {
        background: linear-gradient(90deg, var(--accent-success), #00ffcc);
    }

    .confidence-fill.moderate {
        background: linear-gradient(90deg, var(--accent-warn), var(--accent-info));
    }

    .confidence-fill.low {
        background: linear-gradient(90deg, var(--accent-danger), var(--accent-warn));
    }

    /* Signal Factors */
    .signal-factors {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-subtle);
    }

    .factor-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }

    .factor-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0;
        font-size: 0.85rem;
        color: var(--text-primary);
    }

    .factor-check {
        color: var(--accent-success);
        font-weight: bold;
    }

    /* Stats Row */
    .stats-row {
        display: flex;
        gap: 1.5rem;
        margin-top: 1rem;
        flex-wrap: wrap;
    }

    .stat-item {
        display: flex;
        flex-direction: column;
    }

    .stat-label {
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stat-value {
        font-size: 1rem;
        font-weight: 700;
        font-family: 'Courier New', monospace;
        color: var(--text-primary);
    }

    .stat-value.success {
        color: var(--accent-success);
    }

    .stat-value.danger {
        color: var(--accent-danger);
    }

    /* KPI Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 1.25rem;
        text-align: center;
    }

    .kpi-label {
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }

    .kpi-value {
        font-size: 1.8rem;
        font-weight: 800;
        font-family: 'Courier New', monospace;
        color: var(--accent-success);
    }

    .kpi-sub {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
    }

    /* Demo Banner */
    .demo-banner {
        background: linear-gradient(90deg, rgba(0, 255, 159, 0.1), rgba(168, 85, 247, 0.1));
        border: 1px solid var(--accent-success);
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .demo-banner-text {
        color: var(--text-primary);
        font-size: 0.9rem;
    }

    /* Section Headers */
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .section-title {
        color: var(--text-primary);
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0;
    }

    .section-count {
        font-family: 'Courier New', monospace;
        color: var(--accent-success);
        font-size: 0.9rem;
    }

    /* Footer */
    .app-footer {
        text-align: center;
        color: var(--text-muted);
        padding: 2rem 0;
        font-size: 0.8rem;
        border-top: 1px solid var(--border-subtle);
        margin-top: 2rem;
    }

    /* Override Streamlit metrics */
    [data-testid="stMetricValue"] {
        color: var(--accent-success) !important;
        font-family: 'Courier New', monospace;
    }

    [data-testid="stMetricDelta"] {
        color: var(--text-muted) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: var(--bg-secondary);
        border-radius: 8px;
        padding: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-muted);
        border-radius: 4px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: var(--accent-success);
        color: var(--bg-primary) !important;
    }

    /* Divider */
    hr {
        border-color: var(--border-subtle) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
    }

    [data-testid="stSidebar"] [class*="css"] {
        color: var(--text-primary) !important;
    }

    /* Button */
    .stButton > button {
        background: var(--accent-success);
        color: var(--bg-primary);
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1.5rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: #00cc80;
        box-shadow: 0 0 20px rgba(0, 255, 159, 0.3);
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background: var(--bg-card);
        color: var(--text-primary);
        border-color: var(--border-subtle);
    }
</style>
""", unsafe_allow_html=True)


def generate_mock_signals(count=15):
    """Generate mock trading signals with confidence levels"""
    patterns = [
        ("Momentum Reversal", "whale_accumulation", "Breakout Detected"),
        ("Liquidity Trap", "order_flow_spike", " whale_positioning"),
        ("Cross-Market Correlation", "ethbtc_sync", "Convergence Signal"),
        ("Resolution Probability", "order_book_imbalance", "Outcome Prediction"),
        ("Sentiment Shift", "news_velocity", "Social Momentum")
    ]

    questions = [
        "Will Bitcoin exceed $100K by 2026?",
        "Republicans win House majority in 2026?",
        "Ethereum above $5K by EOY?",
        "Fed cut rates by 50bps in March?",
        "Solana reaches $200 before June?",
        "US enters recession in 2026?",
        "XRP wins SEC lawsuit?",
        "Crypto market cap exceeds $5T?",
        "Tesla DOGElon tweet triggers rally?",
        "Polymarket launches derivatives trading?"
    ]

    signals = []
    now = datetime.now()

    for i in range(min(count, len(questions))):
        # Generate confidence with skew toward actionable levels
        confidence = random.choices(
            [95, 88, 82, 76, 71, 65, 58, 52, 45],
            weights=[1, 2, 4, 3, 2, 2, 1, 1, 1]
        )[0]

        # Determine direction
        is_bullish = random.random() > 0.4
        direction = "YES" if is_bullish else "NO"

        # Freshness (seconds ago)
        freshness_age = random.choices(
            [120, 300, 600, 1200, 3600],
            weights=[3, 3, 2, 1, 1]
        )[0]

        # Pattern strength
        strength = random.choices(
            ["VERY_STRONG", "STRONG", "MODERATE", "WEAK"],
            weights=[2, 4, 3, 1]
        )[0]

        pattern_type, pattern_code, pattern_name = random.choice(patterns)

        # Edge percentage
        edge = round(random.uniform(3, 15), 1) if confidence >= 70 else round(random.uniform(1, 5), 1)

        # Generate factors
        factor_count = random.randint(3, 5)
        factors = [
            random.choice([
                "Momentum reversal confirmed",
                "Whale accumulation detected",
                "Cross-market signal validation",
                "Liquidity tightening pattern",
                "Order flow imbalance",
                "Historical analog match",
                "Sentiment shift detected"
            ])
            for _ in range(factor_count)
        ]

        # Target and stop prices
        current_price = round(random.uniform(0.30, 0.70), 2)
        target_price = round(current_price * (1 + edge/100 if is_bullish else 1 - edge/100), 2)
        stop_price = round(current_price * (1 - 0.08 if is_bullish else 1 + 0.08), 2)

        signals.append({
            "signal_id": f"signal_{i+1}",
            "question": questions[i],
            "direction": direction,
            "confidence": confidence,
            "freshness_age": freshness_age,
            "strength": strength,
            "pattern_type": pattern_type,
            "pattern_name": pattern_name,
            "edge_percent": edge,
            "factors": factors,
            "current_price": current_price,
            "target_price": target_price,
            "stop_price": stop_price,
            "volume_24h": random.randint(100000, 5000000),
            "category": random.choice(["Crypto", "Politics", "Economics", "Tech"])
        })

    # Sort by confidence then freshness
    signals.sort(key=lambda s: (s["confidence"], -s["freshness_age"]), reverse=True)

    return signals


def get_freshness_label(age_seconds):
    """Get freshness badge with styling"""
    if age_seconds < 300:
        return ("FRESH", "badge-fresh", "🟢")
    elif age_seconds < 1800:
        return ("RECENT", "badge-recent", "🟡")
    else:
        return ("STALE", "badge-stale", "🔴")


def get_strength_class(strength):
    """Get CSS class for strength badge"""
    return {
        "VERY_STRONG": "strength-very-strong",
        "STRONG": "strength-strong",
        "MODERATE": "strength-moderate",
        "WEAK": "strength-weak"
    }.get(strength, "strength-moderate")


def get_confidence_class(confidence):
    """Get confidence bar class"""
    if confidence >= 80:
        return "high"
    elif confidence >= 60:
        return "moderate"
    else:
        return "low"


def render_signal_card(signal):
    """Render a single signal card with spiked design"""
    freshness_label, freshness_badge, freshness_icon = get_freshness_label(signal["freshness_age"])
    strength_class = get_strength_class(signal["strength"])
    confidence_class = get_confidence_class(signal["confidence"])
    is_fresh = signal["freshness_age"] < 300
    card_class = "fresh" if is_fresh else ""

    bearish = signal["direction"] == "NO"
    bearish_class = "bearish" if bearish else ""

    html = f"""
    <div class="signal-card {card_class} {bearish_class}">
        <div class="signal-header">
            <div>
                <div class="signal-question">{signal['direction']} // {signal['question']}</div>
            </div>
            <div class="signal-badges">
                <span class="signal-badge {freshness_badge}">{freshness_icon} {freshness_label}</span>
                <span class="signal-badge {strength_class}">{signal['strength']}</span>
                <span class="signal-badge" style="border: 1px solid var(--accent-purple); color: var(--accent-purple); background: rgba(168, 85, 247, 0.1);">{signal['pattern_type']}</span>
            </div>
        </div>

        <div class="confidence-section">
            <div class="confidence-label">
                <span>CONFIDENCE</span>
                <span style="color: var(--accent-success);">{signal['confidence']}%</span>
            </div>
            <div class="confidence-bar">
                <div class="confidence-fill {confidence_class}" style="width: {signal['confidence']}%"></div>
            </div>
        </div>

        <div class="stats-row">
            <div class="stat-item">
                <span class="stat-label">Current</span>
                <span class="stat-value">${signal['current_price']:.2f}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Target</span>
                <span class="stat-value success">${signal['target_price']:.2f}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Stop</span>
                <span class="stat-value danger">${signal['stop_price']:.2f}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Edge</span>
                <span class="stat-value" style="color: var(--accent-warn);">+{signal['edge_percent']}%</span>
            </div>
        </div>

        <div class="signal-factors">
            <div class="factor-label">📊 Signal Drivers ({len(signal['factors'])} factors)</div>
            {''.join(f'<div class="factor-item"><span class="factor-check">✓</span> {factor}</div>' for factor in signal['factors'])}
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_kpi_row(signals):
    """Render KPI cards"""
    high_conf = sum(1 for s in signals if s["confidence"] >= 80)
    fresh_signals = sum(1 for s in signals if s["freshness_age"] < 300)
    avg_edge = sum(s["edge_percent"] for s in signals) / len(signals)

    html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">Active Signals</div>
            <div class="kpi-value">{len(signals)}</div>
            <div class="kpi-sub">{high_conf} high confidence</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Fresh Signals</div>
            <div class="kpi-value">{fresh_signals}</div>
            <div class="kpi-sub">Last 5 minutes</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Avg Edge</div>
            <div class="kpi-value">{avg_edge:.1f}%</div>
            <div class="kpi-sub">Across all signals</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Strong Patterns</div>
            <div class="kpi-value">{sum(1 for s in signals if s['strength'] in ['STRONG', 'VERY_STRONG'])}</div>
            <div class="kpi-sub">Multi-factor confirm</div>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def main():
    """Main spiked demo application"""

    # Demo banner
    st.markdown("""
    <div class="demo-banner">
        <span style="font-size: 1.5rem;">🎯</span>
        <div class="demo-banner-text">
            <strong>SPIKED DEMO MODE</strong> — Dark terminal aesthetic with signal intelligence // Mock data for design demonstration
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Command Center Header
    st.markdown("""
    <div class="command-header">
        <h1>⚡ COMMAND CENTER</h1>
        <div class="subtitle">// Polymarket Prediction Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar - Command Style
    st.sidebar.markdown("""
    <div style="padding: 1rem 0; border-bottom: 1px solid #2a2a35; margin-bottom: 1rem;">
        <div style="color: #00ff9f; font-weight: 700; letter-spacing: 2px; font-size: 0.8rem;">📡 SIGNAL FILTER</div>
    </div>
    """, unsafe_allow_html=True)

    # Filters
    min_confidence = st.sidebar.slider(
        "Min Confidence",
        min_value=50, max_value=95, value=70, step=5,
        help="Show only signals above this confidence level"
    )

    strength_filter = st.sidebar.multiselect(
        "Pattern Strength",
        options=["VERY_STRONG", "STRONG", "MODERATE", "WEAK"],
        default=["STRONG", "VERY_STRONG"]
    )

    direction_filter = st.sidebar.multiselect(
        "Direction",
        options=["YES", "NO"],
        default=["YES", "NO"]
    )

    st.sidebar.divider()
    st.sidebar.markdown(f"""
    <div style="color: #71717a; font-size: 0.75rem; font-family: 'Courier New', monospace;">
        ⚡ SIGNAL ENGINE: ACTIVE<br>
        🔄 UPDATE FREQ: REAL-TIME<br>
        📊 DATA SOURCE: MOCK
    </div>
    """, unsafe_allow_html=True)

    # Generate signals
    all_signals = generate_mock_signals(15)

    # Apply filters
    filtered_signals = [
        s for s in all_signals
        if s["confidence"] >= min_confidence
        and s["strength"] in strength_filter
        and s["direction"] in direction_filter
    ]

    # Main content tabs
    tab1, tab2, tab3 = st.tabs([
        "🎯 Live Signals",
        "📊 Signal Analytics",
        "⚙️ Settings"
    ])

    # Tab 1: Live Signals
    with tab1:
        st.markdown(f"""
        <div class="section-header">
            <h2 class="section-title">🎯 ACTIVE SIGNALS</h2>
            <span class="section-count">{len(filtered_signals)} signals detected</span>
        </div>
        """, unsafe_allow_html=True)

        if filtered_signals:
            render_kpi_row(filtered_signals)

            st.markdown('<div class="signal-grid">', unsafe_allow_html=True)

            for signal in filtered_signals:
                render_signal_card(signal)

            st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔭</div>
                <div>No signals match your filters</div>
                <div style="font-size: 0.85rem; margin-top: 0.5rem;">Adjust your filter criteria to see more opportunities</div>
            </div>
            """, unsafe_allow_html=True)

    # Tab 2: Signal Analytics
    with tab2:
        st.markdown("""
        <div class="section-header">
            <h2 class="section-title">📊 SIGNAL PERFORMANCE</h2>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div style="background: var(--bg-card); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border-subtle);">
                <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1rem;">Confidence Win Rate</div>
            </div>
            """, unsafe_allow_html=True)

            st.metric("80%+ Confidence", "72% win rate", "+8% vs baseline")
            st.metric("70-79% Confidence", "65% win rate", "+3% vs baseline")
            st.metric("60-69% Confidence", "58% win rate", "-2% vs baseline")

        with col2:
            st.markdown("""
            <div style="background: var(--bg-card); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border-subtle);">
                <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1rem;">Pattern Performance</div>
            </div>
            """, unsafe_allow_html=True)

            st.metric("Momentum Reversal", "78% accuracy", "⭐ Best performer")
            st.metric("Liquidity Trap", "71% accuracy", "+5% this week")
            st.metric("Cross-Market", "65% accuracy", "Stable")

    # Tab 3: Settings
    with tab3:
        st.markdown("""
        <div class="section-header">
            <h2 class="section-title">⚙️ Signal Configuration</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: var(--bg-card); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border-subtle);">
            <div style="color: var(--accent-warn); margin-bottom: 1rem;">⚠️ Demo Mode - Configuration disabled</div>
            <div style="color: var(--text-muted); font-size: 0.85rem;">
                In the full production version, you can configure:
                <ul style="margin-top: 0.5rem;">
                    <li>Signal confidence thresholds</li>
                    <li>Pattern detection sensitivity</li>
                    <li>Alert notifications (webhook, email, SMS)</li>
                    <li>Custom pattern overlays</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="app-footer">
        <div style="letter-spacing: 2px; margin-bottom: 0.5rem;">⚡ POLYMARKET ANALYTICS // SPIKED EDITION</div>
        <div style="font-size: 0.75rem; opacity: 0.7;">Dark Terminal Aesthetic // Signal Intelligence // Command Center v2.0</div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
