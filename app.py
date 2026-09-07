"""
CricNova — AI/ML Cricket Score & Match Winner Prediction System
Main Entrance, Secure Authentication & Interactive Stadium Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Streamlit Page Config
st.set_page_config(
    page_title="CricNova | AI Cricket Intelligence",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.ui_components import (
    inject_custom_css,
    render_header,
    render_stat_box,
    render_team_badge_html,
    render_provenance_badge,
    get_plotly_dark_layout
)
from src.database import get_database_analytics, get_prediction_history
from src.config import CANONICAL_TEAMS, TEAM_METADATA
from src.auth import (
    is_authenticated,
    render_auth_screen,
    render_sidebar_user_profile,
    get_current_user
)

# Inject Dark Stadium CSS
inject_custom_css()

# Authentication Check
if not is_authenticated():
    render_auth_screen()
    st.stop()

# Sidebar Navigation & Authenticated User Profile
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 12px 0 16px 0;">
            <div style="font-size: 2.4rem; filter: drop-shadow(0 0 10px rgba(0, 242, 254, 0.6));">⚡🏏</div>
            <h2 style="margin: 6px 0 0 0; font-weight: 800; font-size: 1.5rem; letter-spacing: -0.02em; color: #f8fafc;">
                CRIC<span style="color: #00f2fe;">NOVA</span>
            </h2>
            <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">IPL AI Prediction Engine v2.0</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Active User Profile Badge & Logout
    render_sidebar_user_profile()

    st.markdown("---")
    st.markdown("### 🏟️ Quick Jump")
    st.markdown("- [🔮 Predictor](Predict)")
    st.markdown("- [📊 Analytics](Analytics)")
    st.markdown("- [🏏 Team Radar](Teams)")
    st.markdown("- [🏟️ Stadium Intel](Venues)")
    st.markdown("- [📜 Prediction History](History)")
    st.markdown("- [🤖 ML Model Lab](Model_Lab)")
    st.markdown("- [ℹ️ Methodology & Viva](About)")
    st.markdown("---")
    st.caption("Engineered with Scikit-Learn, XGBoost, Streamlit, and SQLite. Zero Data Leakage Architecture.")


# Main Dashboard Header
curr_user = get_current_user()
welcome_msg = f"Welcome back, {curr_user['name'].split()[0]}! " if curr_user else ""
render_header(
    title=f"{welcome_msg}Next-Gen AI Cricket Intelligence Engine",
    subtitle="Precision Match Winner Classification, Live Chase Win Probability & Innings Score Forecasting Powered by Multi-Model Machine Learning.",
    badge="IPL PRODUCTION PREDICTION PLATFORM"
)

# Top KPI Metric Cards
db_stats = get_database_analytics()

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_stat_box("IPL Matches", "752", "2008 – 2019 Official Archive", icon="📅", color="#00f2fe")
with col2:
    render_stat_box("Ball Deliveries", "178,610", "Granular Ball-by-Ball Data", icon="⚾", color="#3b82f6")
with col3:
    render_stat_box("Live Chase ROC-AUC", "0.825", "Logistic Regression / RF Benchmark", icon="🎯", color="#10b981")
with col4:
    render_stat_box("Active Predictions", str(db_stats["total_predictions"]), f"Avg Rating: {db_stats['average_rating']} ⭐", icon="⚡", color="#f59e0b")

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# Interactive Quick Launch Cards (Clean 5-Module Responsive Layout)
st.markdown("### 🚀 Intelligence Modules")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        """
        <div class="stadium-card">
            <div style="font-size: 1.8rem; margin-bottom: 8px;">🔮</div>
            <h3 style="margin: 0 0 6px 0; font-size: 1.25rem; font-weight: 700; color: #f8fafc;">3-Mode Predictor</h3>
            <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.4; margin-bottom: 14px;">
                Pre-match winner probability, live in-game chase dynamics with real-time <b>Sensitivity Analysis</b>, and 1st innings score corridors.
            </p>
            <a href="/Predict" target="_self" style="text-decoration: none; color: #00f2fe; font-weight: 600; font-size: 0.9rem;">
                Launch Predictor →
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        """
        <div class="stadium-card">
            <div style="font-size: 1.8rem; margin-bottom: 8px;">📊</div>
            <h3 style="margin: 0 0 6px 0; font-size: 1.25rem; font-weight: 700; color: #f8fafc;">League Analytics</h3>
            <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.4; margin-bottom: 14px;">
                Deep exploratory data analysis covering season scoring evolutions, Powerplay vs Death run rates, and toss decision advantages.
            </p>
            <a href="/Analytics" target="_self" style="text-decoration: none; color: #f59e0b; font-weight: 600; font-size: 0.9rem;">
                Explore Trends →
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        """
        <div class="stadium-card">
            <div style="font-size: 1.8rem; margin-bottom: 8px;">🤖</div>
            <h3 style="margin: 0 0 6px 0; font-size: 1.25rem; font-weight: 700; color: #f8fafc;">Model Laboratory</h3>
            <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.4; margin-bottom: 14px;">
                Benchmarking Logistic Regression, Random Forest, and XGBoost on ROC-AUC, F1, RMSE, and Explainable AI feature attribution.
            </p>
            <a href="/Model_Lab" target="_self" style="text-decoration: none; color: #10b981; font-weight: 600; font-size: 0.9rem;">
                Inspect Models →
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

c4, c5 = st.columns(2)
with c4:
    st.markdown(
        """
        <div class="stadium-card">
            <div style="font-size: 1.8rem; margin-bottom: 8px;">🏏</div>
            <h3 style="margin: 0 0 6px 0; font-size: 1.25rem; font-weight: 700; color: #f8fafc;">Team Command Center</h3>
            <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.4; margin-bottom: 14px;">
                Head-to-head match matrices, franchise win percentages, batting depth ratings, and historical bowling efficiency across all 10 teams.
            </p>
            <a href="/Teams" target="_self" style="text-decoration: none; color: #f43f5e; font-weight: 600; font-size: 0.9rem;">
                View Franchises →
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

with c5:
    st.markdown(
        """
        <div class="stadium-card">
            <div style="font-size: 1.8rem; margin-bottom: 8px;">🏟️</div>
            <h3 style="margin: 0 0 6px 0; font-size: 1.25rem; font-weight: 700; color: #f8fafc;">Stadium Intelligence</h3>
            <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.4; margin-bottom: 14px;">
                Ground dimensions, par 1st innings scores, chasing vs defending win ratios, and venue pitch characteristics.
            </p>
            <a href="/Venues" target="_self" style="text-decoration: none; color: #a855f7; font-weight: 600; font-size: 0.9rem;">
                Inspect Venues →
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# Recent Activity & Recent Predictions Feed
st.markdown("### 📜 Recent Predictions Activity")
recent_history = get_prediction_history(limit=5)

if recent_history:
    hist_records = []
    for h in recent_history:
        hist_records.append({
            "Time": h["timestamp"],
            "Mode": h["mode"],
            "Teams": f"{h['team1']} vs {h['team2']}",
            "Venue": h["venue"],
            "Prediction": h["prediction"],
            "Confidence": h["confidence"] or "Medium",
            "User Rating": f"{h['rating']} ⭐" if h.get("rating") else "—"
        })
    df_hist = pd.DataFrame(hist_records)
    st.dataframe(df_hist, use_container_width=True, hide_index=True)
else:
    st.info("No predictions recorded in database yet. Head to the **Predict** page to generate your first match forecast!")

# Platform Footer
st.markdown("---")
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; color: #64748b; font-size: 0.85rem; padding: 10px 0;">
        <div><b>CricNova</b> © 2026 • AI Cricket Analytics Platform</div>
        <div>Built for Academic Rigor & Industrial ML Benchmarking</div>
    </div>
    """,
    unsafe_allow_html=True
)
