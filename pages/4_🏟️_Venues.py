"""
CricNova — Stadium Intelligence & Ground Conditions Analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Venues | CricNova", page_icon="🏟️", layout="wide")

from src.ui_components import (
    inject_custom_css,
    render_header,
    render_stat_box,
    render_provenance_badge,
    get_plotly_dark_layout
)
from src.config import TOP_VENUES
from src.data_loader import load_raw_data
from src.preprocessing import get_cleaned_data

inject_custom_css()

render_header(
    title="Stadium Intelligence & Ground Conditions",
    subtitle="Ground par scores, dew impact, chasing vs defending biases, and venue pitch dynamics across India.",
    badge="VENUE ANALYTICS"
)
render_provenance_badge("HISTORICAL")


@st.cache_data
def get_venue_data():
    m_raw, d_raw = load_raw_data()
    m_clean, d_clean = get_cleaned_data(m_raw, d_raw)
    return m_clean, d_clean


m_df, d_df = get_venue_data()

# Selected Venue
selected_venue = st.selectbox("Select Ground to Inspect", TOP_VENUES, index=0)

v_matches = m_df[m_df["venue"] == selected_venue]
total_matches = len(v_matches)

# 1st and 2nd innings scores at this venue
v_d = d_df[d_df["match_id"].isin(v_matches["id"])]
inns1_scores = v_d[v_d["inning"] == 1].groupby("match_id")["total_runs"].sum()
inns2_scores = v_d[v_d["inning"] == 2].groupby("match_id")["total_runs"].sum()

avg_1st = float(inns1_scores.mean()) if len(inns1_scores) > 0 else 165.0
avg_2nd = float(inns2_scores.mean()) if len(inns2_scores) > 0 else 150.0

# Chasing vs Defending wins
toss_field_wins = (
    (v_matches["toss_decision"] == "field") & (v_matches["toss_winner"] == v_matches["winner"])
).sum()
toss_bat_wins = (
    (v_matches["toss_decision"] == "bat") & (v_matches["toss_winner"] == v_matches["winner"])
).sum()

# Identify chasing teams: team batting in inning 2
chase_wins_count = 0
for _, m in v_matches.iterrows():
    # If toss winner fielded, toss winner chased
    if m["toss_decision"] == "field" and m["winner"] == m["toss_winner"]:
        chase_wins_count += 1
    elif m["toss_decision"] == "bat" and m["winner"] != m["toss_winner"]:
        chase_wins_count += 1

chase_pct = (chase_wins_count / max(total_matches, 1)) * 100
defend_pct = 100.0 - chase_pct

# Top KPIs
v_c1, v_c2, v_c3, v_c4 = st.columns(4)
with v_c1:
    render_stat_box("Matches Hosted", f"{total_matches}", f"{selected_venue[:20]}...", icon="🏟️", color="#00f2fe")
with v_c2:
    render_stat_box("Par 1st Innings", f"{avg_1st:.0f}", "Historical Average Total", icon="🎯", color="#3b82f6")
with v_c3:
    render_stat_box("Chasing Win %", f"{chase_pct:.1f}%", f"{chase_wins_count} chases succeeded", icon="⚡", color="#10b981")
with v_c4:
    render_stat_box("Defending Win %", f"{defend_pct:.1f}%", f"{total_matches - chase_wins_count} totals defended", icon="🛡️", color="#f59e0b")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# Row 1: Score Distribution Histogram & Chasing Bias Pie
r1_col1, r1_col2 = st.columns([3, 2])

with r1_col1:
    fig_hist = px.histogram(
        inns1_scores,
        nbins=16,
        title=f"1st Innings Total Score Distribution at {selected_venue}",
        color_discrete_sequence=["#00f2fe"]
    )
    fig_hist.update_layout(get_plotly_dark_layout("1st Innings Score Distribution", height=360))
    fig_hist.update_xaxes(title="Innings Total (Runs)")
    fig_hist.update_yaxes(title="Match Frequency")
    st.plotly_chart(fig_hist, use_container_width=True)

with r1_col2:
    fig_pie = go.Figure(data=[go.Pie(
        labels=["Chasing Side Won", "Defending Side Won"],
        values=[chase_wins_count, total_matches - chase_wins_count],
        hole=0.55,
        marker=dict(colors=["#10b981", "#f59e0b"])
    )])
    fig_pie.update_layout(get_plotly_dark_layout("Chasing vs Defending Victory Share", height=360))
    st.plotly_chart(fig_pie, use_container_width=True)

# Cross Stadium Comparison Table
st.markdown("---")
st.markdown("### 🌐 Cross-Venue Benchmark Comparison")
st.caption("Compare par scores and chasing advantages across all premier IPL grounds.")

venue_benchmarks = []
for v in TOP_VENUES:
    m_sub = m_df[m_df["venue"] == v]
    if len(m_sub) < 5:
        continue
    d_sub = d_df[d_df["match_id"].isin(m_sub["id"])]
    inns1_sub = d_sub[d_sub["inning"] == 1].groupby("match_id")["total_runs"].sum()
    
    c_count = 0
    for _, row_m in m_sub.iterrows():
        if row_m["toss_decision"] == "field" and row_m["winner"] == row_m["toss_winner"]:
            c_count += 1
        elif row_m["toss_decision"] == "bat" and row_m["winner"] != row_m["toss_winner"]:
            c_count += 1

    c_win_rate = (c_count / len(m_sub)) * 100
    avg_score = float(inns1_sub.mean()) if len(inns1_sub) > 0 else 160.0

    venue_benchmarks.append({
        "Stadium": v,
        "Matches": len(m_sub),
        "Avg 1st Innings": round(avg_score, 1),
        "Chasing Win %": round(c_win_rate, 1),
        "Ground Nature": "High Scoring / Flat" if avg_score >= 170 else ("Bowling Paradise" if avg_score < 155 else "Balanced Surface")
    })

df_venues = pd.DataFrame(venue_benchmarks).sort_values("Avg 1st Innings", ascending=False)
st.dataframe(
    df_venues.style.background_gradient(subset=["Avg 1st Innings"], cmap="YlOrRd"),
    use_container_width=True,
    hide_index=True
)
