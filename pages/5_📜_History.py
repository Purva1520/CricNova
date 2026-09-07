"""
CricNova — Prediction History Log & User Feedback Dashboard
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px

st.set_page_config(page_title="History | CricNova", page_icon="📜", layout="wide")

from src.ui_components import (
    inject_custom_css,
    render_header,
    render_stat_box,
    render_provenance_badge,
    get_plotly_dark_layout
)
from src.database import get_prediction_history, get_database_analytics

inject_custom_css()

render_header(
    title="Prediction Audit Log & User Feedback",
    subtitle="Inspect model inference logs, verify predictions against match realities, and review community accuracy ratings.",
    badge="SQLITE REPOSITORY"
)
render_provenance_badge("ANALYSIS")

db_stats = get_database_analytics()

# Top KPIs
h1, h2, h3, h4 = st.columns(4)
with h1:
    render_stat_box("Total Predictions", f"{db_stats['total_predictions']}", "Logged in SQLite", icon="📜", color="#00f2fe")
with h2:
    render_stat_box("Average Rating", f"{db_stats['average_rating']} / 5.0", f"{db_stats['feedback_count']} reviews", icon="⭐", color="#f59e0b")
with h3:
    render_stat_box("Avg Predicted Score", f"{db_stats['avg_predicted_score']:.0f}", "1st innings models", icon="🎯", color="#3b82f6")
with h4:
    render_stat_box("Top Predicted Team", f"{db_stats['most_predicted_team']}", "Most favored side", icon="🏆", color="#10b981")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# Fetch History Records
records = get_prediction_history(limit=100)

if not records:
    st.info("No predictions recorded in the database yet. Launch the Predictor to log your first match scenario!")
else:
    # Filter Controls
    f_col1, f_col2 = st.columns([1, 2])
    with f_col1:
        modes = ["All Modes"] + list(set(r["mode"] for r in records if r.get("mode")))
        selected_mode = st.selectbox("Filter by Prediction Mode", modes, index=0)
    with f_col2:
        search_query = st.text_input("Search by Franchise or Venue", placeholder="e.g. Mumbai, Chennai, Wankhede")

    filtered = records
    if selected_mode != "All Modes":
        filtered = [r for r in filtered if r.get("mode") == selected_mode]
    if search_query:
        q = search_query.lower()
        filtered = [
            r for r in filtered
            if q in r.get("team1", "").lower()
            or q in r.get("team2", "").lower()
            or q in r.get("venue", "").lower()
            or q in r.get("prediction", "").lower()
        ]

    st.markdown(f"#### 📋 Logged Records ({len(filtered)} Found)")

    table_data = []
    for r in filtered:
        rating_disp = f"{r['rating']} ⭐" if r.get("rating") else "Unrated"
        table_data.append({
            "ID": r["id"],
            "Timestamp": r["timestamp"],
            "Mode": r["mode"],
            "Match": f"{r['team1']} vs {r['team2']}",
            "Venue": r["venue"],
            "Prediction Verdict": r["prediction"],
            "Confidence": r["confidence"] or "—",
            "User Rating": rating_disp
        })

    df_table = pd.DataFrame(table_data)
    st.dataframe(df_table, use_container_width=True, hide_index=True)

    # Detailed Record Inspector
    st.markdown("---")
    st.markdown("### 🔍 Record Inspector")
    rec_ids = [r["id"] for r in filtered]
    if rec_ids:
        selected_id = st.selectbox("Select Record ID to Inspect Detailed Explanation", rec_ids, index=0)
        selected_rec = next((r for r in filtered if r["id"] == selected_id), None)

        if selected_rec:
            st.markdown(
                f"""
                <div class="stadium-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span class="metric-pill" style="color: #00f2fe; border-color: #00f2fe;">RECORD #{selected_rec['id']}</span>
                        <span style="color: #64748b; font-size: 0.85rem;">{selected_rec['timestamp']}</span>
                    </div>
                    <h3 style="margin: 8px 0; color: #f8fafc;">
                        {selected_rec['team1']} vs {selected_rec['team2']} @ {selected_rec['venue']}
                    </h3>
                    <div style="color: #38bdf8; font-weight: 700; font-size: 1.1rem; margin-bottom: 8px;">
                        Prediction: {selected_rec['prediction']} (Confidence: {selected_rec['confidence']})
                    </div>
                    <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.5;">
                        <b>Summary Narrative:</b> {selected_rec.get('explanation', 'None recorded.')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Factors list if available
            raw_factors = selected_rec.get("factors_json")
            if raw_factors:
                try:
                    factors_list = json.loads(raw_factors)
                    if factors_list:
                        st.markdown("##### Detailed Factor Attribution")
                        for f in factors_list:
                            st.markdown(
                                f"""
                                <div class="xai-callout">
                                    <b>{f.get('category', 'Factor')}</b> ({f.get('impact', 'Info')}): {f.get('narrative', '')}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                except Exception:
                    pass
