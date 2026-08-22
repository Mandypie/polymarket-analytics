"""
Polymarket Analytics Platform - PROFESSIONAL Edition
Enterprise fintech aesthetic for presentation-ready dashboard
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import json

# Page configuration
st.set_page_config(
    page_title="Polymarket Analytics Platform",
    page_icon="PM",
    layout="wide",
    initial_sidebar_state="expanded"
)

# PROFESSIONAL DESIGN CSS - Enterprise Fintech Aesthetic
st.markdown("""
<style>
    /* Core palette - Enterprise Fintech */
    :root {
        --bg-primary: #0B1426;
        --bg-secondary: #111827;
        --bg-card: #1A2332;
        --bg-card-hover: #242D3D;
        --accent-gold: #C9A961;
        --accent-gold-light: #E4C98D;
        --accent-teal: #2D8B7F;
        --accent-teal-dark: #1E5F56;
        --accent-navy: #1E3A5F;
        --text-primary: #FFFFFF;
        --text-secondary: #A0AEC0;
        --text-muted: #6B7280;
        --border-subtle: #2D3748;
        --border-card: #3A4756;
        --success-green: #10B981;
        --success-green-dark: #059669;
        --danger-red: #EF4444;
        --warning-amber: #F59E0B;
        --info-blue: #3B82F6;
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

    /* Professional Header */
    .professional-header {
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        border-bottom: 1px solid var(--accent-gold);
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        position: relative;
    }

    .professional-header::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, var(--accent-gold) 0%, transparent 100%);
        opacity: 0.5;
    }

    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .header-logo {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .logo-mark {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--accent-gold) 0%, var(--accent-gold-light) 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: var(--bg-primary);
        font-size: 0.9rem;
        letter-spacing: 1px;
    }

    .header-title {
        color: var(--text-primary) !important;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: 0.5px;
    }

    .header-subtitle {
        color: var(--text-secondary);
        font-size: 0.85rem;
        margin-top: 0.25rem;
        font-weight: 400;
    }

    .header-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid var(--success-green);
        border-radius: 4px;
        font-size: 0.8rem;
        color: var(--success-green);
    }

    .status-dot {
        width: 8px;
        height: 8px;
        background: var(--success-green);
        border-radius: 50%;
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* KPI Cards - Subtle Professional */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.25rem;
        margin-bottom: 2rem;
    }

    .kpi-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
        border: 1px solid var(--border-card);
        border-radius: 12px;
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-gold) 0%, var(--accent-gold-light) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .kpi-card:hover::before {
        opacity: 1;
    }

    .kpi-card:hover {
        border-color: var(--accent-gold);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
    }

    .kpi-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
        font-weight: 500;
    }

    .kpi-value {
        font-size: 2rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }

    .kpi-sub {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .kpi-trend {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.75rem;
        margin-top: 0.5rem;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
    }

    .kpi-trend.positive {
        background: rgba(16, 185, 129, 0.15);
        color: var(--success-green);
    }

    .kpi-trend.negative {
        background: rgba(239, 68, 68, 0.15);
        color: var(--danger-red);
    }

    /* Signal Card Container */
    .signal-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
        gap: 1.25rem;
        margin-top: 1.5rem;
    }

    /* Professional Signal Card - Trading Ticket Style */
    .signal-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
        border: 1px solid var(--border-card);
        border-radius: 12px;
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .signal-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--success-green) 0%, var(--success-green-dark) 100%);
    }

    .signal-card.bearish::before {
        background: linear-gradient(180deg, var(--danger-red) 0%, #B91C1C 100%);
    }

    .signal-card:hover {
        border-color: var(--accent-gold);
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
    }

    /* Signal Card Header */
    .signal-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1.25rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-subtle);
    }

    .signal-direction {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.75rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-right: 0.75rem;
    }

    .signal-direction.bullish {
        background: rgba(16, 185, 129, 0.15);
        color: var(--success-green);
        border: 1px solid var(--success-green);
    }

    .signal-direction.bearish {
        background: rgba(239, 68, 68, 0.15);
        color: var(--danger-red);
        border: 1px solid var(--danger-red);
    }

    .signal-question {
        font-size: 1rem;
        font-weight: 500;
        color: var(--text-primary);
        line-height: 1.5;
        margin-top: 0.5rem;
    }

    .signal-badges {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .signal-badge {
        padding: 0.3rem 0.75rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .badge-fresh {
        background: rgba(16, 185, 129, 0.15);
        color: var(--success-green);
        border: 1px solid var(--success-green);
    }

    .badge-recent {
        background: rgba(59, 130, 246, 0.15);
        color: var(--info-blue);
        border: 1px solid var(--info-blue);
    }

    .badge-stale {
        background: rgba(107, 114, 128, 0.15);
        color: var(--text-muted);
        border: 1px solid var(--text-muted);
    }

    .badge-strength-very-strong {
        background: rgba(201, 169, 97, 0.2);
        color: var(--accent-gold);
        border: 1px solid var(--accent-gold);
    }

    .badge-strength-strong {
        background: rgba(45, 139, 127, 0.2);
        color: var(--accent-teal);
        border: 1px solid var(--accent-teal);
    }

    .badge-strength-moderate {
        background: rgba(245, 158, 11, 0.2);
        color: var(--warning-amber);
        border: 1px solid var(--warning-amber);
    }

    .badge-strength-weak {
        background: rgba(239, 68, 68, 0.2);
        color: var(--danger-red);
        border: 1px solid var(--danger-red);
    }

    .badge-pattern {
        background: rgba(59, 130, 246, 0.1);
        color: var(--text-secondary);
        border: 1px solid var(--border-subtle);
    }

    /* Price Information - Trading Ticket Style */
    .price-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1rem 0;
        padding: 1rem;
        background: var(--bg-primary);
        border-radius: 8px;
        border: 1px solid var(--border-subtle);
    }

    .price-item {
        display: flex;
        flex-direction: column;
    }

    .price-label {
        font-size: 0.7rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
    }

    .price-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
    }

    .price-value.success {
        color: var(--success-green);
    }

    .price-value.danger {
        color: var(--danger-red);
    }

    .price-value.highlight {
        color: var(--accent-gold);
    }

    /* Confidence Section - Professional */
    .confidence-section {
        margin: 1rem 0;
    }

    .confidence-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .confidence-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }

    .confidence-value {
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--accent-gold);
    }

    .confidence-bar {
        height: 6px;
        background: var(--bg-primary);
        border-radius: 3px;
        overflow: hidden;
        position: relative;
    }

    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--accent-gold) 0%, var(--accent-gold-light) 100%);
        border-radius: 3px;
        transition: width 0.5s ease;
        position: relative;
    }

    .confidence-fill::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%);
        animation: shimmer 2s ease-in-out infinite;
    }

    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    .confidence-fill.high {
        background: linear-gradient(90deg, var(--success-green) 0%, #34D399 100%);
    }

    .confidence-fill.moderate {
        background: linear-gradient(90deg, var(--accent-teal) 0%, var(--accent-gold) 100%);
    }

    .confidence-fill.low {
        background: linear-gradient(90deg, var(--danger-red) 0%, var(--warning-amber) 100%);
    }

    /* Signal Factors */
    .signal-factors {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-subtle);
    }

    .factor-label {
        font-size: 0.7rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }

    .factor-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0;
        font-size: 0.85rem;
        color: var(--text-primary);
    }

    .factor-check {
        color: var(--success-green);
        font-weight: 600;
        font-size: 0.9rem;
    }

    /* Section Headers */
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-subtle);
    }

    .section-title {
        color: var(--text-primary);
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: 0.5px;
    }

    .section-count {
        font-size: 0.85rem;
        color: var(--accent-gold);
        font-weight: 500;
        padding: 0.25rem 0.75rem;
        background: rgba(201, 169, 97, 0.15);
        border-radius: 4px;
    }

    /* Data Table Styles */
    .data-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1rem;
    }

    .data-table th {
        text-align: left;
        padding: 0.75rem 1rem;
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
        border-bottom: 1px solid var(--border-card);
        background: var(--bg-secondary);
    }

    .data-table td {
        padding: 0.75rem 1rem;
        font-size: 0.85rem;
        color: var(--text-primary);
        border-bottom: 1px solid var(--border-subtle);
    }

    .data-table tr:hover {
        background: var(--bg-card-hover);
    }

    /* Footer */
    .app-footer {
        text-align: center;
        color: var(--text-muted);
        padding: 2rem 0;
        font-size: 0.8rem;
        border-top: 1px solid var(--border-subtle);
        margin-top: 3rem;
    }

    .footer-brand {
        color: var(--accent-gold);
        font-weight: 500;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }

    /* Override Streamlit components */
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
    }

    [data-testid="stMetricDelta"] {
        color: var(--text-secondary) !important;
    }

    /* Tabs - Professional */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--bg-secondary);
        border-radius: 8px;
        padding: 0.5rem;
        border: 1px solid var(--border-card);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: 6px;
        padding: 0.75rem 1.25rem;
        font-weight: 500;
        font-size: 0.9rem;
    }

    .stTabs [aria-selected="true"] {
        background: var(--accent-gold);
        color: var(--bg-primary) !important;
    }

    /* Divider */
    hr {
        border-color: var(--border-subtle) !important;
        opacity: 0.5;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-card);
    }

    [data-testid="stSidebar"] [class*="css"] {
        color: var(--text-primary) !important;
    }

    /* Buttons - Professional */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-gold) 0%, var(--accent-gold-light) 100%);
        color: var(--bg-primary);
        border: none;
        border-radius: 6px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.85rem;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(201, 169, 97, 0.3);
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background: var(--bg-card);
        color: var(--text-primary);
        border-color: var(--border-card);
    }

    /* Slider */
    .stSlider > div > div > div {
        background: var(--accent-gold);
    }

    /* Demo Banner - Professional */
    .demo-banner {
        background: linear-gradient(135deg, rgba(201, 169, 97, 0.1) 0%, rgba(45, 139, 127, 0.1) 100%);
        border: 1px solid var(--accent-gold);
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .demo-banner-icon {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, var(--accent-gold) 0%, var(--accent-gold-light) 100%);
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: var(--bg-primary);
        font-size: 0.75rem;
    }

    .demo-banner-text {
        color: var(--text-primary);
        font-size: 0.9rem;
    }

    .demo-banner-text strong {
        color: var(--accent-gold);
    }

    /* Analytics Card */
    .analytics-card {
        background: var(--bg-card);
        border: 1px solid var(--border-card);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .analytics-title {
        font-size: 0.85rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 1rem;
        font-weight: 500;
    }

    /* Performance Metric */
    .performance-metric {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid var(--border-subtle);
    }

    .performance-metric:last-child {
        border-bottom: none;
    }

    .metric-name {
        font-size: 0.9rem;
        color: var(--text-primary);
    }

    .metric-values {
        text-align: right;
    }

    .metric-value {
        font-size: 1rem;
        font-weight: 600;
        color: var(--accent-gold);
    }

    .metric-delta {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .metric-delta.positive {
        color: var(--success-green);
    }

    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: var(--text-secondary);
    }

    .empty-state-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }

    .empty-state-title {
        font-size: 1rem;
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }

    .empty-state-text {
        font-size: 0.85rem;
        color: var(--text-muted);
    }
</style>
""", unsafe_allow_html=True)


def generate_mock_signals(count=15):
    """Generate mock trading signals with confidence levels"""
    patterns = [
        ("Momentum Reversal", "whale_accumulation", "Breakout Detected"),
        ("Liquidity Trap", "order_flow_spike", "Positioning Signal"),
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
        "Tesla announcement triggers market rally?",
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
        return ("Fresh", "badge-fresh")
    elif age_seconds < 1800:
        return ("Recent", "badge-recent")
    else:
        return ("Established", "badge-stale")


def get_strength_class(strength):
    """Get CSS class for strength badge"""
    return {
        "VERY_STRONG": "badge-strength-very-strong",
        "STRONG": "badge-strength-strong",
        "MODERATE": "badge-strength-moderate",
        "WEAK": "badge-strength-weak"
    }.get(strength, "badge-strength-moderate")


def get_confidence_class(confidence):
    """Get confidence bar class"""
    if confidence >= 80:
        return "high"
    elif confidence >= 60:
        return "moderate"
    else:
        return "low"


def render_signal_card(signal):
    """Render a single signal card with professional trading ticket design"""
    freshness_label, freshness_badge = get_freshness_label(signal["freshness_age"])
    strength_class = get_strength_class(signal["strength"])
    confidence_class = get_confidence_class(signal["confidence"])
    bearish = signal["direction"] == "NO"
    bearish_class = "bearish" if bearish else ""
    direction_class = "bearish" if bearish else "bullish"

    html = f"""
    <div class="signal-card {bearish_class}">
        <div class="signal-header">
            <div>
                <span class="signal-direction {direction_class}">{signal['direction']}</span>
                <div class="signal-question">{signal['question']}</div>
            </div>
            <div class="signal-badges">
                <span class="signal-badge {freshness_badge}">{freshness_label}</span>
                <span class="signal-badge {strength_class}">{signal['strength'].replace('_', ' ')}</span>
                <span class="signal-badge badge-pattern">{signal['pattern_type']}</span>
            </div>
        </div>

        <div class="price-grid">
            <div class="price-item">
                <span class="price-label">Current</span>
                <span class="price-value">${signal['current_price']:.2f}</span>
            </div>
            <div class="price-item">
                <span class="price-label">Target</span>
                <span class="price-value success">${signal['target_price']:.2f}</span>
            </div>
            <div class="price-item">
                <span class="price-label">Stop Loss</span>
                <span class="price-value danger">${signal['stop_price']:.2f}</span>
            </div>
            <div class="price-item">
                <span class="price-label">Edge</span>
                <span class="price-value highlight">+{signal['edge_percent']}%</span>
            </div>
        </div>

        <div class="confidence-section">
            <div class="confidence-header">
                <span class="confidence-label">Confidence Level</span>
                <span class="confidence-value">{signal['confidence']}%</span>
            </div>
            <div class="confidence-bar">
                <div class="confidence-fill {confidence_class}" style="width: {signal['confidence']}%"></div>
            </div>
        </div>

        <div class="signal-factors">
            <div class="factor-label">Signal Drivers ({len(signal['factors'])} factors)</div>
            {''.join(f'<div class="factor-item"><span class="factor-check">✓</span> {factor}</div>' for factor in signal['factors'])}
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_kpi_row(signals):
    """Render professional KPI cards"""
    high_conf = sum(1 for s in signals if s["confidence"] >= 80)
    fresh_signals = sum(1 for s in signals if s["freshness_age"] < 300)
    avg_edge = sum(s["edge_percent"] for s in signals) / len(signals)
    strong_patterns = sum(1 for s in signals if s['strength'] in ['STRONG', 'VERY_STRONG'])

    html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">Active Signals</div>
            <div class="kpi-value">{len(signals)}</div>
            <div class="kpi-sub">{high_conf} high confidence</div>
            <div class="kpi-trend positive">
                <span>▲</span>
                <span>+12% this week</span>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Fresh Signals</div>
            <div class="kpi-value">{fresh_signals}</div>
            <div class="kpi-sub">Last 5 minutes</div>
            <div class="kpi-trend positive">
                <span>▲</span>
                <span>Real-time updates</span>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Average Edge</div>
            <div class="kpi-value">{avg_edge:.1f}%</div>
            <div class="kpi-sub">Across all signals</div>
            <div class="kpi-trend positive">
                <span>▲</span>
                <span>+2.3% vs baseline</span>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Strong Patterns</div>
            <div class="kpi-value">{strong_patterns}</div>
            <div class="kpi-sub">Multi-factor confirm</div>
            <div class="kpi-trend positive">
                <span>●</span>
                <span>High reliability</span>
            </div>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def main():
    """Main professional demo application"""

    # Demo banner
    st.markdown("""
    <div class="demo-banner">
        <div class="demo-banner-icon">PM</div>
        <div class="demo-banner-text">
            <strong>PROFESSIONAL EDITION</strong> — Enterprise-grade analytics platform // Mock data for demonstration purposes
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Professional Header
    st.markdown("""
    <div class="professional-header">
        <div class="header-content">
            <div class="header-logo">
                <div class="logo-mark">PM</div>
                <div>
                    <div class="header-title">Polymarket Analytics Platform</div>
                    <div class="header-subtitle">Prediction Market Intelligence System</div>
                </div>
            </div>
            <div class="header-status">
                <div class="status-dot"></div>
                <span>System Operational</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar - Professional styling
    st.sidebar.markdown("""
    <div style="padding: 1rem 0; border-bottom: 1px solid var(--border-card); margin-bottom: 1.5rem;">
        <div style="color: var(--accent-gold); font-weight: 600; letter-spacing: 1px; font-size: 0.75rem; text-transform: uppercase;">
            Signal Filters
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Filters
    min_confidence = st.sidebar.slider(
        "Minimum Confidence",
        min_value=50, max_value=95, value=70, step=5,
        help="Show only signals above this confidence level"
    )

    strength_filter = st.sidebar.multiselect(
        "Pattern Strength",
        options=["Very Strong", "Strong", "Moderate", "Weak"],
        default=["Strong", "Very Strong"]
    )

    # Convert strength filter to match internal format
    strength_map = {
        "Very Strong": "VERY_STRONG",
        "Strong": "STRONG",
        "Moderate": "MODERATE",
        "Weak": "WEAK"
    }
    strength_filter_internal = [strength_map[s] for s in strength_filter]

    direction_filter = st.sidebar.multiselect(
        "Signal Direction",
        options=["YES", "NO"],
        default=["YES", "NO"]
    )

    category_filter = st.sidebar.multiselect(
        "Market Category",
        options=["Crypto", "Politics", "Economics", "Tech"],
        default=["Crypto", "Politics", "Economics", "Tech"]
    )

    st.sidebar.divider()

    st.sidebar.markdown("""
    <div style="color: var(--text-muted); font-size: 0.75rem; line-height: 1.6;">
        <div style="color: var(--accent-gold); font-weight: 500; margin-bottom: 0.5rem;">System Status</div>
        <div>Signal Engine: Active</div>
        <div>Data Source: Mock (Demo)</div>
        <div>Last Update: Just now</div>
        <div>Update Frequency: Real-time</div>
    </div>
    """, unsafe_allow_html=True)

    # Generate signals
    all_signals = generate_mock_signals(15)

    # Apply filters
    filtered_signals = [
        s for s in all_signals
        if s["confidence"] >= min_confidence
        and s["strength"] in strength_filter_internal
        and s["direction"] in direction_filter
        and s["category"] in category_filter
    ]

    # Main content tabs
    tab1, tab2, tab3 = st.tabs([
        "Live Signals",
        "Performance Analytics",
        "System Settings"
    ])

    # Tab 1: Live Signals
    with tab1:
        st.markdown(f"""
        <div class="section-header">
            <h2 class="section-title">Active Trading Signals</h2>
            <span class="section-count">{len(filtered_signals)} signals</span>
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
            <div class="empty-state">
                <div class="empty-state-icon">○</div>
                <div class="empty-state-title">No Signals Match Your Criteria</div>
                <div class="empty-state-text">Adjust your filter parameters to discover more opportunities</div>
            </div>
            """, unsafe_allow_html=True)

    # Tab 2: Performance Analytics
    with tab2:
        st.markdown("""
        <div class="section-header">
            <h2 class="section-title">Signal Performance Analytics</h2>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="analytics-card">
                <div class="analytics-title">Confidence Level Performance</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="analytics-card">
                <div class="performance-metric">
                    <div class="metric-name">80%+ Confidence</div>
                    <div class="metric-values">
                        <div class="metric-value">72%</div>
                        <div class="metric-delta positive">▲ +8% vs baseline</div>
                    </div>
                </div>
                <div class="performance-metric">
                    <div class="metric-name">70-79% Confidence</div>
                    <div class="metric-values">
                        <div class="metric-value">65%</div>
                        <div class="metric-delta positive">▲ +3% vs baseline</div>
                    </div>
                </div>
                <div class="performance-metric">
                    <div class="metric-name">60-69% Confidence</div>
                    <div class="metric-values">
                        <div class="metric-value">58%</div>
                        <div class="metric-delta">▼ -2% vs baseline</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="analytics-card">
                <div class="analytics-title">Pattern Type Performance</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="analytics-card">
                <div class="performance-metric">
                    <div class="metric-name">Momentum Reversal</div>
                    <div class="metric-values">
                        <div class="metric-value">78%</div>
                        <div class="metric-delta positive">Best performer</div>
                    </div>
                </div>
                <div class="performance-metric">
                    <div class="metric-name">Liquidity Trap</div>
                    <div class="metric-values">
                        <div class="metric-value">71%</div>
                        <div class="metric-delta positive">▲ +5% this week</div>
                    </div>
                </div>
                <div class="performance-metric">
                    <div class="metric-name">Cross-Market</div>
                    <div class="metric-values">
                        <div class="metric-value">65%</div>
                        <div class="metric-delta">Stable performance</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Tab 3: Settings
    with tab3:
        st.markdown("""
        <div class="section-header">
            <h2 class="section-title">System Configuration</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="analytics-card">
            <div style="color: var(--accent-gold); margin-bottom: 1rem; font-weight: 500;">
                Demo Mode - Configuration Restricted
            </div>
            <div style="color: var(--text-secondary); font-size: 0.85rem; line-height: 1.6;">
                The professional production edition includes:
                <ul style="margin-top: 0.75rem; margin-left: 1.5rem;">
                    <li>Configurable confidence thresholds</li>
                    <li>Pattern detection sensitivity controls</li>
                    <li>Multi-channel alert notifications</li>
                    <li>Custom pattern overlay configuration</li>
                    <li>API access and webhooks</li>
                    <li>Advanced analytics and reporting</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="app-footer">
        <div class="footer-brand">POLYMARKET ANALYTICS PLATFORM</div>
        <div>Professional Edition // Enterprise Analytics System</div>
        <div style="margin-top: 0.5rem; opacity: 0.7;">Mock data for demonstration purposes</div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
