"""
CricNova — League Visual Analytics & Historical Match Intelligence
Exploratory Data Analysis covering 752 matches and 178k deliveries.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Analytics | CricNova", page_icon="📊", layout="wide")

from src.ui_components import (
    inject_custom_css,
    render_header,
    render_stat_box,
    render_provenance_badge,
    get_plotly_dark_layout
)
from src.data_loader import load_raw_data
from src.preprocessing import get_cleaned_data

inject_custom_css()

render_header(
    title="League Visual Analytics & Scoring Trends",
    subtitle="Interactive Exploratory Data Analysis covering 12 seasons of IPL ball-by-ball dynamics.",
    badge="IPL BIG DATA INTELLIGENCE"
)
render_provenance_badge("HISTORICAL")


@st.cache_data
def get_analytics_data():
    m_raw, d_raw = load_raw_data()
    m_clean, d_clean = get_cleaned_data(m_raw, d_raw)
    return m_clean, d_clean


m_df, d_df = get_analytics_data()

# Top KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_stat_box("Total Matches", f"{len(m_df)}", "2008 to 2019", icon="🏟️", color="#00f2fe")
with col2:
    total_runs = int(d_df["total_runs"].sum())
    render_stat_box("Total Runs Scored", f"{total_runs:,}", "All seasons", icon="🏏", color="#3b82f6")
with col3:
    total_wkts = int(d_df["is_wicket"].sum())
    render_stat_box("Total Wickets", f"{total_wkts:,}", "Dismissals logged", icon="🎯", color="#10b981")
with col4:
    sixes = int((d_df["batsman_runs"] == 6).sum())
    render_stat_box("Sixes Cleared", f"{sixes:,}", f"{(sixes/len(m_df)):.1f} per match", icon="🚀", color="#f59e0b")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# Row 1: Season-by-Season Scoring Evolution & Phase Run Rates
c1, c2 = st.columns(2)

with c1:
    # 1st Innings Average by Season
    inns1 = d_df[d_df["inning"] == 1].groupby(["match_id"])["total_runs"].sum().reset_index()
    inns1 = inns1.merge(m_df[["id", "season"]], left_on="match_id", right_on="id")
    season_avg = inns1.groupby("season")["total_runs"].agg(["mean", "max"]).reset_index()
    season_avg.rename(columns={"mean": "Avg 1st Innings", "max": "Highest Total"}, inplace=True)

    fig_season = go.Figure()
    fig_season.add_trace(go.Bar(
        x=season_avg["season"],
        y=season_avg["Avg 1st Innings"],
        name="Avg 1st Innings Score",
        marker_color="#00f2fe"
    ))
    fig_season.add_trace(go.Scatter(
        x=season_avg["season"],
        y=season_avg["Highest Total"],
        mode="lines+markers",
        name="Season Highest Total",
        line=dict(color="#f43f5e", width=3)
    ))
    fig_season.update_layout(get_plotly_dark_layout("Season-by-Season Scoring Trend (1st Innings)", height=360))
    fig_season.update_yaxes(range=[140, 260])
    st.plotly_chart(fig_season, use_container_width=True)

with c2:
    # Run Rate across Match Phases (Powerplay 1-6, Middle 7-15, Death 16-20)
    d_df["phase"] = pd.cut(
        d_df["over"],
        bins=[0, 6, 15, 20],
        labels=["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]
    )
    phase_stats = d_df.groupby("phase", observed=False).agg(
        total_runs=("total_runs", "sum"),
        balls=("ball", "count"),
        wickets=("is_wicket", "sum")
    ).reset_index()
    phase_stats["run_rate"] = np.round((phase_stats["total_runs"] / phase_stats["balls"]) * 6.0, 2)
    phase_stats["balls_per_wicket"] = np.round(phase_stats["balls"] / phase_stats["wickets"], 1)

    fig_phase = go.Figure()
    fig_phase.add_trace(go.Bar(
        x=phase_stats["phase"],
        y=phase_stats["run_rate"],
        text=[f"{r:.2f} RPO" for r in phase_stats["run_rate"]],
        textposition="auto",
        marker_color=["#3b82f6", "#00f2fe", "#10b981"]
    ))
    fig_phase.update_layout(get_plotly_dark_layout("Average Run Rate by Match Phase", height=360))
    fig_phase.update_yaxes(title="Run Rate (RPO)", range=[0, 12])
    st.plotly_chart(fig_phase, use_container_width=True)

# Row 2: Toss Decision Advantage & Boundary Distribution
c3, c4 = st.columns(2)

with c3:
    # Toss Winner Advantage
    toss_win_match_win = (m_df["toss_winner"] == m_df["winner"]).mean() * 100
    toss_field_win = (
        (m_df["toss_decision"] == "field") & (m_df["toss_winner"] == m_df["winner"])
    ).sum() / (m_df["toss_decision"] == "field").sum() * 100
    toss_bat_win = (
        (m_df["toss_decision"] == "bat") & (m_df["toss_winner"] == m_df["winner"])
    ).sum() / (m_df["toss_decision"] == "bat").sum() * 100

    toss_df = pd.DataFrame({
        "Decision": ["Elected to Field", "Elected to Bat", "Overall Toss Winner"],
        "Win %": [round(toss_field_win, 1), round(toss_bat_win, 1), round(toss_win_match_win, 1)]
    })

    fig_toss = px.bar(
        toss_df,
        x="Decision",
        y="Win %",
        color="Decision",
        color_discrete_sequence=["#10b981", "#f59e0b", "#00f2fe"],
        text="Win %"
    )
    fig_toss.update_layout(get_plotly_dark_layout("Toss Advantage: Fielding vs Batting First", height=360))
    fig_toss.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_toss.update_yaxes(range=[0, 70])
    st.plotly_chart(fig_toss, use_container_width=True)

with c4:
    # Boundaries (4s vs 6s) evolution over seasons
    boundary_df = d_df[d_df["batsman_runs"].isin([4, 6])].merge(
        m_df[["id", "season"]], left_on="match_id", right_on="id"
    )
    b_agg = boundary_df.groupby(["season", "batsman_runs"]).size().unstack(fill_value=0).reset_index()
    b_agg.rename(columns={4: "Fours", 6: "Sixes"}, inplace=True)

    fig_bounds = go.Figure()
    fig_bounds.add_trace(go.Bar(
        x=b_agg["season"], y=b_agg["Fours"], name="Fours (4s)", marker_color="#3b82f6"
    ))
    fig_bounds.add_trace(go.Bar(
        x=b_agg["season"], y=b_agg["Sixes"], name="Sixes (6s)", marker_color="#f59e0b"
    ))
    fig_bounds.update_layout(
        get_plotly_dark_layout("Boundary Volume by Season (4s vs 6s)", height=360),
        barmode="stack"
    )
    st.plotly_chart(fig_bounds, use_container_width=True)
