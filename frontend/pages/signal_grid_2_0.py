"""
Signal Grid 2.0 - Enhanced Signal Display

Shows multi-factor signals with confidence meters, pattern badges, and factor breakdowns.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class SignalGrid2_0:
    """Enhanced signal grid with multi-factor analysis"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.signals_cache = []
        self.last_refresh = None

    def fetch_enhanced_signals(self, min_score: float = 0.6, limit: int = 50) -> List[Dict]:
        """Fetch enhanced signals from the API"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/v1/signals/enhanced",
                params={"min_score": min_score, "limit": limit},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                self.signals_cache = data.get("signals", [])
                self.last_refresh = datetime.now()
                return self.signals_cache
            return []

        except Exception as e:
            st.error(f"Error fetching signals: {e}")
            return []

    def trigger_signal_generation(self, category: Optional[str] = None) -> Dict:
        """Trigger enhanced signal generation"""
        try:
            params = {"limit": 50}
            if category:
                params["category"] = category

            response = requests.post(
                f"{self.api_base_url}/api/v1/signals/enhanced/generate",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            st.error(f"Error triggering generation: {e}")
            return {"success": False, "message": str(e)}

    def display_signal_card(self, signal: Dict[str, Any]) -> None:
        """Display a single enhanced signal card"""
        # Extract signal data
        market_id = signal.get("market_id", "Unknown")
        direction = signal.get("direction", "NEUTRAL")
        composite_score = signal.get("composite_score", 0)
        confidence = signal.get("confidence", 0)
        strength_level = signal.get("strength_level", "WEAK")
        signal_age = signal.get("signal_age_seconds", 0)
        is_active = signal.get("is_active", True)

        # Determine colors based on direction and strength
        if direction == "LONG":
            direction_color = "🟢"
            bg_color = "rgba(34, 197, 94, 0.1)"
        elif direction == "SHORT":
            direction_color = "🔴"
            bg_color = "rgba(239, 68, 68, 0.1)"
        else:
            direction_color = "⚪"
            bg_color = "rgba(255, 255, 255, 0.05)"

        # Freshness indicator
        if signal_age < 300:  # < 5 minutes
            freshness_emoji = "🔥"
            freshness_text = "FRESH"
            freshness_color = "#ef4444"
        elif signal_age < 1800:  # < 30 minutes
            freshness_emoji = "✨"
            freshness_text = "RECENT"
            freshness_color = "#f59e0b"
        elif signal_age < 7200:  # < 2 hours
            freshness_emoji = "📊"
            freshness_text = "AGED"
            freshness_color = "#3b82f6"
        else:
            freshness_emoji = "📉"
            freshness_text = "STALE"
            freshness_color = "#6b7280"

        # Container with styling
        st.markdown(f"""
        <div style="
            background: {bg_color};
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
        ">
        """, unsafe_allow_html=True)

        # Header row
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.markdown(f"**{direction_color} {market_id[:20]}...**")
        with col2:
            st.markdown(f"<small style='color: {freshness_color}'>{freshness_emoji} {freshness_text}</small>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<small>{strength_level}</small>")

        # Confidence meter
        st.markdown("**Confidence:**")
        confidence_pct = int(confidence * 100)

        # Color-coded confidence bar
        if confidence >= 0.8:
            bar_color = "#10b981"  # Green
        elif confidence >= 0.6:
            bar_color = "#3b82f6"  # Blue
        elif confidence >= 0.4:
            bar_color = "#f59e0b"  # Orange
        else:
            bar_color = "#ef4444"  # Red

        st.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            height: 8px;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                background: {bar_color};
                width: {confidence_pct}%;
                height: 100%;
                transition: width 0.3s ease;
            "></div>
        </div>
        <small>{confidence_pct}%</small>
        """, unsafe_allow_html=True)

        # Metrics row
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Composite Score", f"{composite_score:.2f}")
        with m2:
            st.metric("Age", f"{signal_age // 60}m")
        with m3:
            st.metric("Active", "✅" if is_active else "❌")

        # Factor breakdown (expandable)
        factor_attribution = signal.get("factor_attribution", {})
        if factor_attribution and factor_attribution.get("factor_attribution"):
            with st.expander("🔍 Factor Breakdown"):
                factors = factor_attribution["factor_attribution"]
                for factor_name, factor_data in factors.items():
                    contribution = factor_data.get("contribution_percent", 0)
                    raw_score = factor_data.get("raw_score", 0)
                    factor_direction = factor_data.get("direction", "NEUTRAL")

                    factor_color = "#10b981" if factor_direction == "LONG" else "#ef4444"

                    st.markdown(f"""
                    <div style="margin-bottom: 8px;">
                        <small><b>{factor_name.replace('_', ' ').title()}</b></small><br/>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="
                                background: rgba(255,255,255,0.1);
                                border-radius: 4px;
                                height: 6px;
                                flex: 1;
                                overflow: hidden;
                            ">
                                <div style="
                                    background: {factor_color};
                                    width: {contribution}%;
                                    height: 100%;
                                "></div>
                            </div>
                            <small>{contribution:.1f}%</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Action buttons
        st.markdown("<div style='margin-top: 12px;'>", unsafe_allow_html=True)
        b1, b2, b3, b4 = st.columns(4)

        with b1:
            if st.button("🔍 Analyze", key=f"analyze_{market_id}"):
                st.info(f"Detailed analysis for {market_id}")

        with b2:
            if st.button("📊 Position", key=f"position_{market_id}"):
                st.success(f"Position sizing for {market_id}")

        with b3:
            if st.button("⚖️ Scale", key=f"scale_{market_id}"):
                st.info(f"Scaling options for {market_id}")

        with b4:
            if st.button("🔒 Hold", key=f"hold_{market_id}"):
                st.warning(f"Hold strategy for {market_id}")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    def display_signal_stats(self) -> None:
        """Display statistics about current signals"""
        if not self.signals_cache:
            return

        total_signals = len(self.signals_cache)

        # Count by direction
        long_signals = sum(1 for s in self.signals_cache if s.get("direction") == "LONG")
        short_signals = sum(1 for s in self.signals_cache if s.get("direction") == "SHORT")
        neutral_signals = total_signals - long_signals - short_signals

        # Count by freshness
        fresh_signals = sum(1 for s in self.signals_cache if s.get("signal_age_seconds", 9999) < 300)

        # Average metrics
        avg_confidence = sum(s.get("confidence", 0) for s in self.signals_cache) / total_signals if total_signals > 0 else 0
        avg_composite = sum(s.get("composite_score", 0) for s in self.signals_cache) / total_signals if total_signals > 0 else 0

        # Display stats
        st.markdown("### 📊 Signal Statistics")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Signals", total_signals)
        with col2:
            st.metric("🟢 Long", long_signals)
        with col3:
            st.metric("🔴 Short", short_signals)
        with col4:
            st.metric("🔥 Fresh", fresh_signals)

        col5, col6 = st.columns(2)
        with col5:
            st.metric("Avg Confidence", f"{avg_confidence:.2%}")
        with col6:
            st.metric("Avg Composite Score", f"{avg_composite:.2f}")

    def render(self) -> None:
        """Render the complete Signal Grid 2.0"""
        st.title("🎯 Signal Grid 2.0")
        st.markdown("---")

        # Sidebar controls
        with st.sidebar:
            st.header("⚙️ Signal Controls")

            # Signal generation
            st.subheader("Generate Signals")
            category = st.selectbox(
                "Category",
                ["All", "Politics", "Crypto", "Sports", "Culture"],
                index=0
            )

            if st.button("🔄 Generate New Signals", type="primary"):
                with st.spinner("Generating enhanced signals..."):
                    cat_param = None if category == "All" else category
                    result = self.trigger_signal_generation(cat_param)
                    if result.get("success"):
                        st.success(f"✅ {result.get('message', 'Signals generated')}")
                    else:
                        st.error(f"❌ {result.get('message', 'Generation failed')}")

            st.markdown("---")

            # Filters
            st.subheader("🔍 Filters")

            min_score = st.slider(
                "Minimum Composite Score",
                0.0, 1.0, 0.6, 0.05
            )

            direction_filter = st.multiselect(
                "Direction",
                ["LONG", "SHORT", "NEUTRAL"],
                default=["LONG", "SHORT"]
            )

            strength_filter = st.multiselect(
                "Strength Level",
                ["WEAK", "MODERATE", "STRONG", "VERY_STRONG", "EXTREME"],
                default=["STRONG", "VERY_STRONG", "EXTREME"]
            )

            freshness_filter = st.selectbox(
                "Freshness",
                ["All", "FRESH", "RECENT", "AGED", "STALE"],
                index=0
            )

            st.markdown("---")

            # Auto-refresh
            st.subheader("🔄 Auto-Refresh")
            auto_refresh = st.checkbox("Enable Auto-Refresh", value=True)
            refresh_interval = st.selectbox(
                "Interval",
                ["30s", "1m", "5m"],
                index=0
            )

        # Main content area
        if auto_refresh:
            # Fetch signals (will auto-refresh based on Streamlit's rerun)
            if self.last_refresh is None or (datetime.now() - self.last_refresh).total_seconds() > 30:
                with st.spinner("Fetching signals..."):
                    category_param = None if category == "All" else category
                    self.fetch_enhanced_signals(min_score, limit=50)
        else:
            if not self.signals_cache or st.button("🔄 Refresh Signals"):
                with st.spinner("Fetching signals..."):
                    category_param = None if category == "All" else category
                    self.fetch_enhanced_signals(min_score, limit=50)

        # Apply filters
        filtered_signals = self.signals_cache.copy()

        if direction_filter:
            filtered_signals = [s for s in filtered_signals if s.get("direction") in direction_filter]

        if strength_filter:
            filtered_signals = [s for s in filtered_signals if s.get("strength_level") in strength_filter]

        if freshness_filter != "All":
            age_thresholds = {
                "FRESH": 300,
                "RECENT": 1800,
                "AGED": 7200,
                "STALE": 21600
            }
            threshold = age_thresholds.get(freshness_filter, 999999)
            filtered_signals = [s for s in filtered_signals if s.get("signal_age_seconds", 0) < threshold]

        # Display statistics
        if filtered_signals:
            self.display_signal_stats()
            st.markdown("---")

        # Display signals
        st.markdown(f"### 📈 Active Signals ({len(filtered_signals)})")

        if filtered_signals:
            # Sort by composite score descending
            filtered_signals.sort(key=lambda x: x.get("composite_score", 0), reverse=True)

            for signal in filtered_signals:
                self.display_signal_card(signal)
        else:
            st.info("No signals found matching current filters. Try adjusting the filters or generating new signals.")

        # Footer
        st.markdown("---")
        st.markdown(f"<small>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>", unsafe_allow_html=True)


def main():
    """Main entry point for Signal Grid 2.0"""
    st.set_page_config(
        page_title="Signal Grid 2.0",
        page_icon="🎯",
        layout="wide"
    )

    # Custom CSS for dark theme
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #12121a 100%);
    }
    .stMetric {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize and render
    grid = SignalGrid2_0()
    grid.render()


if __name__ == "__main__":
    main()
