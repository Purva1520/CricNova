"""
CricNova — Franchise Profiles, Team Radar & Head-to-Head Analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Teams | CricNova", page_icon="🏏", layout="wide")

from src.ui_components import (
    inject_custom_css,
    render_header,
    render_stat_box,
    render_team_badge_html,
    render_provenance_badge,
    get_plotly_dark_layout
)
from src.config import CANONICAL_TEAMS, TEAM_METADATA
from src.data_loader import load_raw_data
from src.preprocessing import get_cleaned_data

inject_custom_css()

render_header(
    title="Franchise Command Center & Head-to-Head Radar",
    subtitle="In-depth analytics, team strength ratings, and historical matchup matrix across all IPL franchises.",
    badge="TEAM INTELLIGENCE"
)
render_provenance_badge("HISTORICAL")


@st.cache_data
def get_team_data():
    m_raw, d_raw = load_raw_data()
    m_clean, d_clean = get_cleaned_data(m_raw, d_raw)
    return m_clean, d_clean


m_df, d_df = get_team_data()

# Team Selector
selected_team = st.selectbox("Select Franchise to Inspect", CANONICAL_TEAMS, index=2)
meta = TEAM_METADATA.get(selected_team, {"short": selected_team[:3].upper(), "primary_color": "#00f2fe", "secondary_color": "#3b82f6"})
color = meta["primary_color"]

# Team Stats calculation
team_matches = m_df[(m_df["team1"] == selected_team) | (m_df["team2"] == selected_team)]
total_played = len(team_matches)
total_won = len(team_matches[team_matches["winner"] == selected_team])
win_rate = (total_won / max(total_played, 1)) * 100

# Chasing vs Defending
chasing_matches = team_matches[
    ((team_matches["team2"] == selected_team) & (team_matches["toss_decision"] == "bat")) |
    ((team_matches["team1"] == selected_team) & (team_matches["toss_decision"] == "field"))
]
chase_wins = len(chasing_matches[chasing_matches["winner"] == selected_team])
chase_rate = (chase_wins / max(len(chasing_matches), 1)) * 100

defend_matches = team_matches[~team_matches.index.isin(chasing_matches.index)]
defend_wins = len(defend_matches[defend_matches["winner"] == selected_team])
defend_rate = (defend_wins / max(len(defend_matches), 1)) * 100

# Top KPIs
t_c1, t_c2, t_c3, t_c4 = st.columns(4)
with t_c1:
    render_stat_box("Total Matches", f"{total_played}", f"{meta['short']} in IPL Record", icon="🏟️", color=color)
with t_c2:
    render_stat_box("Total Victories", f"{total_won}", f"{win_rate:.1f}% Win Rate", icon="🏆", color="#10b981")
with t_c3:
    render_stat_box("Chasing Win %", f"{chase_rate:.1f}%", f"{chase_wins} / {len(chasing_matches)} chases", icon="⚡", color="#00f2fe")
with t_c4:
    render_stat_box("Defending Win %", f"{defend_rate:.1f}%", f"{defend_wins} / {len(defend_matches)} defended", icon="🛡️", color="#f59e0b")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# Head to Head Comparison Matrix
st.markdown(f"### ⚔️ {selected_team} vs Opposition H2H Records")

opp_rows = []
for opp in CANONICAL_TEAMS:
    if opp == selected_team:
        continue
    h2h = team_matches[(team_matches["team1"] == opp) | (team_matches["team2"] == opp)]
    played = len(h2h)
    if played > 0:
        wins = len(h2h[h2h["winner"] == selected_team])
        losses = played - wins
        pct = round((wins / played) * 100, 1)
        status = "Played"
    else:
        wins = 0
        losses = 0
        pct = 0.0
        status = "Era Overlap"
    opp_rows.append({
        "Opponent": opp,
        "Matches": played,
        "Won": wins,
        "Lost": losses,
        "Win %": pct,
        "Status": status
    })

df_h2h = pd.DataFrame(opp_rows).sort_values("Matches", ascending=False)
df_chart = df_h2h[df_h2h["Matches"] > 0]

c_tab, c_chart = st.columns([1, 1])
with c_tab:
    st.dataframe(
        df_h2h.style.background_gradient(subset=["Win %"], cmap="Blues"),
        use_container_width=True,
        hide_index=True
    )

with c_chart:
    if len(df_chart) > 0:
        fig_h2h = px.bar(
            df_chart,
            x="Opponent",
            y=["Won", "Lost"],
            barmode="stack",
            color_discrete_sequence=[color, "#334155"]
        )
        fig_h2h.update_layout(get_plotly_dark_layout(f"{meta['short']} vs Franchises (Wins & Losses)", height=380))
        fig_h2h.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_h2h, use_container_width=True)
    else:
        st.info("No recorded matches for this franchise in the dataset era.")

# Direct Head to Head Clashes
st.markdown("---")
st.markdown("### 🔍 Direct Franchise Clash Lookup")
clash_col1, clash_col2 = st.columns(2)
with clash_col1:
    team_a = st.selectbox("Franchise A", CANONICAL_TEAMS, index=2, key="clash_a")
with clash_col2:
    team_b_opts = [t for t in CANONICAL_TEAMS if t != team_a]
    team_b = st.selectbox("Franchise B", team_b_opts, index=0, key="clash_b")

clash_matches = m_df[
    ((m_df["team1"] == team_a) & (m_df["team2"] == team_b)) |
    ((m_df["team1"] == team_b) & (m_df["team2"] == team_a))
]

if len(clash_matches) > 0:
    wins_a = len(clash_matches[clash_matches["winner"] == team_a])
    wins_b = len(clash_matches[clash_matches["winner"] == team_b])
    
    color_a = TEAM_METADATA.get(team_a, {}).get("primary_color", "#00f2fe")
    color_b = TEAM_METADATA.get(team_b, {}).get("primary_color", "#f59e0b")

    st.markdown(
        f"""
        <div class="stadium-card">
            <div style="text-align: center; margin-bottom: 12px;">
                <span style="font-size: 1.1rem; color: #94a3b8; font-weight: 600;">ALL-TIME CLASH SUMMARY ({len(clash_matches)} Matches in 2008–2019 Dataset)</span>
            </div>
            <div style="display: flex; justify-content: space-around; align-items: center;">
                <div style="text-align: center;">
                    <h2 style="margin: 0; color: {color_a}; font-size: 2.4rem; font-family: 'JetBrains Mono', monospace;">{wins_a}</h2>
                    <b style="color: #f8fafc; font-size: 1.05rem;">{team_a}</b>
                </div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #64748b;">VS</div>
                <div style="text-align: center;">
                    <h2 style="margin: 0; color: {color_b}; font-size: 2.4rem; font-family: 'JetBrains Mono', monospace;">{wins_b}</h2>
                    <b style="color: #f8fafc; font-size: 1.05rem;">{team_b}</b>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Recent meetings table
    st.markdown("##### Recent Meetings")
    recent_clashes = clash_matches.sort_values("season", ascending=False).head(5)[
        ["season", "date", "venue", "toss_winner", "toss_decision", "winner"]
    ]
    st.dataframe(recent_clashes, use_container_width=True, hide_index=True)
else:
    st.markdown(
        f"""
        <div class="stadium-card" style="border-left: 4px solid #f59e0b;">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 1.3rem; margin-right: 10px;">ℹ️</span>
                <b style="color: #f8fafc; font-size: 1.05rem;">Dataset Era Availability Note</b>
            </div>
            <p style="color: #cbd5e1; font-size: 0.93rem; line-height: 1.5; margin: 0 0 12px 0;">
                No direct head-to-head fixtures occurred between <b>{team_a}</b> and <b>{team_b}</b> during the 2008–2019 IPL dataset archive (era active overlap limitation).
            </p>
            <a href="/Predict" target="_self" style="text-decoration: none; display: inline-block; background: rgba(0, 242, 254, 0.15); border: 1px solid #00f2fe; color: #00f2fe; padding: 7px 16px; border-radius: 8px; font-weight: 600; font-size: 0.88rem;">
                🔮 Evaluate Match Winner Prediction for {team_a} vs {team_b} →
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
