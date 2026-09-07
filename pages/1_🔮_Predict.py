"""
CricNova — Conversational 3-Mode Cricket Prediction Wizard & What-If Simulator
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Predictor | CricNova", page_icon="🔮", layout="wide")

from src.ui_components import (
    inject_custom_css,
    render_header,
    render_stat_box,
    render_team_badge_html,
    render_provenance_badge,
    get_plotly_dark_layout
)
from src.config import CANONICAL_TEAMS, TOP_VENUES, TEAM_METADATA
from src.predictor import (
    predict_pre_match,
    predict_live_chase,
    predict_first_innings_score
)
from src.database import save_prediction, save_feedback
from src.validation import MatchStateValidationError

inject_custom_css()

render_header(
    title="Cricket Prediction Wizard & Sensitivity Lab",
    subtitle="Evaluate Pre-Match Winner Probabilities, Live In-Game Chase Dynamics, and 1st Innings Projected Totals.",
    badge="AI INFERENCE ENGINE"
)
render_provenance_badge("PREDICTION")

# Tabs for the 3 Prediction Modes
tab1, tab2, tab3 = st.tabs([
    "🔮 Mode 1: Pre-Match Winner AI",
    "⚡ Mode 2: Live Win Probability & Sensitivity",
    "🎯 Mode 3: 1st Innings Score Projection"
])


# ==============================================================================
# TAB 1: PRE-MATCH WINNER
# ==============================================================================
with tab1:
    st.markdown("#### ⚔️ Pre-Match Head-to-Head Setup")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        team1 = st.selectbox("Team 1 (Home / First Selected)", CANONICAL_TEAMS, index=0, key="pm_team1")
    with col_t2:
        # Default team 2 to different team
        t2_options = [t for t in CANONICAL_TEAMS if t != team1]
        team2 = st.selectbox("Team 2 (Challenger)", t2_options, index=min(1, len(t2_options)-1), key="pm_team2")

    col_v, col_tw, col_td = st.columns(3)
    with col_v:
        venue = st.selectbox("Match Venue", TOP_VENUES, index=0, key="pm_venue")
    with col_tw:
        toss_winner = st.selectbox("Toss Winner", [team1, team2], index=0, key="pm_toss_winner")
    with col_td:
        toss_decision = st.selectbox("Toss Decision", ["field", "bat"], index=0, key="pm_toss_decision")

    if st.button("🚀 Compute Pre-Match Prediction", key="btn_pre_match"):
        try:
            with st.spinner("Analyzing historical matchups, venue par scores, and recent form..."):
                res = predict_pre_match(team1, team2, venue, toss_winner, toss_decision)
                
                # Save to database
                pred_id = save_prediction(
                    mode="Pre-Match Winner",
                    team1=team1,
                    team2=team2,
                    venue=venue,
                    prediction=res["favored_team"],
                    team1_prob=res["team1_win_prob"],
                    team2_prob=res["team2_win_prob"],
                    confidence=f"{res['confidence_score']}%",
                    explanation=f"Favored {res['favored_team']} with {res['confidence_score']}% confidence.",
                    factors=res["explanations"]
                )
                st.session_state["last_pm_pred_id"] = pred_id
                st.session_state["last_pm_res"] = res

        except Exception as e:
            st.error(f"Prediction Error: {str(e)}")

    if "last_pm_res" in st.session_state:
        res = st.session_state["last_pm_res"]
        p1 = res["team1_win_prob"] * 100
        p2 = res["team2_win_prob"] * 100
        favored = res["favored_team"]
        conf = res["confidence_score"]

        color_t1 = TEAM_METADATA.get(team1, {}).get("primary_color", "#00f2fe")
        color_t2 = TEAM_METADATA.get(team2, {}).get("primary_color", "#f59e0b")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # Hero Prediction Result Card
        st.markdown(
            f"""
            <div class="stadium-card" style="border-left: 6px solid {color_t1 if favored == team1 else color_t2};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div class="metric-pill" style="color: #10b981; border-color: #10b981; background: rgba(16, 185, 129, 0.1);">
                            🎯 MODEL VERDICT
                        </div>
                        <h2 style="margin: 6px 0; font-size: 2.2rem; font-weight: 800; color: #f8fafc;">
                            {favored} To Win
                        </h2>
                        <p style="color: #94a3b8; margin: 0; font-size: 1rem;">
                            Model Confidence Rating: <b style="color: #00f2fe;">{conf}%</b>
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 2.8rem; font-family: 'JetBrains Mono', monospace; font-weight: 800; color: #f8fafc;">
                            {max(p1, p2):.1f}%
                        </span>
                        <div style="color: #64748b; font-size: 0.82rem;">WIN PROBABILITY</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Comparative Win Probability Bar
        st.markdown(
            f"""
            <div style="margin: 20px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-weight: 700; font-size: 0.95rem;">
                    <span style="color: {color_t1};">{team1}: {p1:.1f}%</span>
                    <span style="color: {color_t2};">{team2}: {p2:.1f}%</span>
                </div>
                <div style="height: 18px; border-radius: 9999px; background: rgba(30, 41, 59, 0.8); overflow: hidden; display: flex;">
                    <div style="width: {p1}%; background-color: {color_t1}; transition: width 0.5s ease;"></div>
                    <div style="width: {p2}%; background-color: {color_t2}; transition: width 0.5s ease;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Explainable AI Factor Attribution
        st.markdown("#### 🧠 Explainable AI: Tactical Factor Attribution")
        for exp in res["explanations"]:
            st.markdown(
                f"""
                <div class="xai-callout">
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="margin-right: 8px; font-size: 1.1rem;">{exp['icon']}</span>
                        <b style="color: #f8fafc; font-size: 0.95rem;">{exp['category']}</b>
                        <span class="metric-pill" style="margin-left: 10px; font-size: 0.75rem;">{exp['impact']}</span>
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.4;">
                        {exp['narrative']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # User Feedback Rating Block
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("##### 💬 Rate this Prediction")
        fb_c1, fb_c2, fb_c3 = st.columns([2, 3, 2])
        with fb_c1:
            rating = st.slider("Rating (1-5 Stars)", 1, 5, 5, key="pm_star_rating")
        with fb_c2:
            feedback_text = st.text_input("Qualitative Feedback (Optional)", placeholder="e.g., Matches my pitch analysis", key="pm_fb_text")
        with fb_c3:
            if st.button("Submit Feedback", key="pm_btn_feedback"):
                pid = st.session_state.get("last_pm_pred_id")
                if pid:
                    save_feedback(pid, rating, "Pre-Match User", feedback_text)
                    st.success("Thank you! Feedback saved to database.")


# ==============================================================================
# TAB 2: LIVE WIN PROBABILITY & WHAT-IF SIMULATOR
# ==============================================================================
with tab2:
    st.markdown("#### ⚡ 2nd Innings Live Chase Match Situation")
    
    live_c1, live_c2 = st.columns(2)
    with live_c1:
        bat_team = st.selectbox("Chasing Team (Batting 2nd)", CANONICAL_TEAMS, index=5, key="live_bat_team")
    with live_c2:
        bowl_options = [t for t in CANONICAL_TEAMS if t != bat_team]
        bowl_team = st.selectbox("Defending Team (Bowling 2nd)", bowl_options, index=0, key="live_bowl_team")

    l_col1, l_col2, l_col3, l_col4 = st.columns(4)
    with l_col1:
        target_score = st.number_input("Target Score", min_value=50, max_value=300, value=178, step=1, key="live_target")
    with l_col2:
        current_score = st.number_input("Current Score", min_value=0, max_value=300, value=122, step=1, key="live_score")
    with l_col3:
        overs_bowled = st.number_input("Overs Bowled (e.g. 14.2)", min_value=0.1, max_value=19.5, value=14.2, step=0.1, key="live_overs")
    with l_col4:
        wickets_fallen = st.number_input("Wickets Fallen", min_value=0, max_value=9, value=3, step=1, key="live_wickets")

    l_sub1, l_sub2 = st.columns(2)
    with l_sub1:
        runs_last5 = st.number_input("Runs in Last 5 Overs", min_value=0, max_value=120, value=42, step=1, key="live_r5")
    with l_sub2:
        wickets_last5 = st.number_input("Wickets in Last 5 Overs", min_value=0, max_value=5, value=1, step=1, key="live_w5")

    # Run Prediction
    try:
        live_res = predict_live_chase(
            batting_team=bat_team,
            bowling_team=bowl_team,
            target_score=target_score,
            current_score=current_score,
            overs_bowled=overs_bowled,
            wickets_fallen=wickets_fallen,
            runs_last_5=runs_last5,
            wickets_last_5=wickets_last5
        )

        p_bat = live_res["batting_win_prob"] * 100
        p_bowl = live_res["bowling_win_prob"] * 100

        color_bat = TEAM_METADATA.get(bat_team, {}).get("primary_color", "#00f2fe")
        color_bowl = TEAM_METADATA.get(bowl_team, {}).get("primary_color", "#f43f5e")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Dynamic Key Equation Cards
        eq1, eq2, eq3, eq4 = st.columns(4)
        with eq1:
            render_stat_box("Current Run Rate", f"{live_res['crr']:.2f}", "Runs Per Over", icon="📊", color="#00f2fe")
        with eq2:
            render_stat_box("Required Run Rate", f"{live_res['rrr']:.2f}", "Needed to Win", icon="📈", color="#f59e0b" if live_res['rrr'] > live_res['crr'] else "#10b981")
        with eq3:
            render_stat_box("Equation", f"{live_res.get('runs_required', 0)} off {live_res.get('balls_remaining', 0)}b", f"{live_res.get('wickets_in_hand', 0)} Wkts in hand", icon="🎯", color="#3b82f6")
        with eq4:
            render_stat_box("Pressure Index", f"{live_res.get('pressure_index', 0):.2f}", "RRR / (Wickets+0.5)", icon="🚨", color="#f43f5e" if live_res.get('pressure_index', 0) > 1.3 else "#10b981")

        # Win Probability Display
        st.markdown(
            f"""
            <div class="stadium-card" style="margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="metric-pill" style="color: #00f2fe; border-color: #00f2fe;">⚡ LIVE WIN PROBABILITY</span>
                        <h2 style="margin: 6px 0; font-size: 2.2rem; font-weight: 800; color: #f8fafc;">
                            {bat_team if p_bat >= 50 else bowl_team} Advantage
                        </h2>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 2.8rem; font-family: 'JetBrains Mono', monospace; font-weight: 800; color: {color_bat if p_bat >= 50 else color_bowl};">
                            {max(p_bat, p_bowl):.1f}%
                        </span>
                        <div style="color: #64748b; font-size: 0.82rem;">PREDICTED WIN SHARE</div>
                    </div>
                </div>
                <div style="margin-top: 14px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-weight: 700;">
                        <span style="color: {color_bat};">{bat_team}: {p_bat:.1f}%</span>
                        <span style="color: {color_bowl};">{bowl_team}: {p_bowl:.1f}%</span>
                    </div>
                    <div style="height: 18px; border-radius: 9999px; background: rgba(30, 41, 59, 0.8); overflow: hidden; display: flex;">
                        <div style="width: {p_bat}%; background-color: {color_bat}; transition: width 0.4s ease;"></div>
                        <div style="width: {p_bowl}%; background-color: {color_bowl}; transition: width 0.4s ease;"></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ======================================================================
        # DYNAMIC SENSITIVITY ANALYZER
        # ======================================================================
        st.markdown("---")
        st.markdown("### 🎛️ Dynamic Over-by-Over Sensitivity Analyzer")
        st.caption("Evaluate how real-time run rate fluctuations and wickets swing the ML Win Probability!")

        wi_col1, wi_col2 = st.columns(2)
        with wi_col1:
            delta_runs = st.slider("Hypothetical Next Over Runs", min_value=0, max_value=36, value=10, key="wi_runs")
        with wi_col2:
            delta_wickets = st.slider("Hypothetical Next Over Wickets", min_value=0, max_value=3, value=0, key="wi_wickets")

        # Compute hypothetical state
        hypo_score = current_score + delta_runs
        hypo_wickets = min(wickets_fallen + delta_wickets, 10)
        hypo_overs = min(int(overs_bowled) + 1.0, 20.0)

        hypo_res = predict_live_chase(
            batting_team=bat_team,
            bowling_team=bowl_team,
            target_score=target_score,
            current_score=hypo_score,
            overs_bowled=hypo_overs,
            wickets_fallen=hypo_wickets,
            runs_last_5=runs_last5 + delta_runs - 8,
            wickets_last_5=delta_wickets
        )

        hypo_p_bat = hypo_res["batting_win_prob"] * 100
        swing = hypo_p_bat - p_bat
        swing_color = "#10b981" if swing >= 0 else "#f43f5e"

        st.markdown(
            f"""
            <div class="stadium-card" style="border: 1px dashed #38bdf8; background: rgba(19, 27, 46, 0.6);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="metric-pill" style="color: #38bdf8; border-color: #38bdf8;">MODEL SENSITIVITY PROJECTION</span>
                        <div style="font-size: 1.1rem; color: #f8fafc; margin-top: 4px;">
                            If {bat_team} scores <b>{delta_runs} runs</b> and loses <b>{delta_wickets} wicket(s)</b> next over:
                        </div>
                        <div style="color: #94a3b8; font-size: 0.88rem; margin-top: 4px;">
                            Projected State: {hypo_score}/{hypo_wickets} after {hypo_overs:.0f} overs (Needs {max(target_score - hypo_score, 0)} off {max(120 - int(hypo_overs*6), 0)}b)
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 2.2rem; font-family: 'JetBrains Mono', monospace; font-weight: 800; color: #f8fafc;">
                            {hypo_p_bat:.1f}%
                        </span>
                        <div style="color: {swing_color}; font-weight: 700; font-size: 0.95rem;">
                            {f'+{swing:.1f}%' if swing >= 0 else f'{swing:.1f}%'} Shift
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Tactical Explanations
        st.markdown("#### 🧠 Real-Time Chase Factors")
        for exp in live_res.get("explanations", []):
            st.markdown(
                f"""
                <div class="xai-callout">
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="margin-right: 8px; font-size: 1.1rem;">{exp.get('icon', '⚡')}</span>
                        <b style="color: #f8fafc; font-size: 0.95rem;">{exp.get('category', 'Factor')}</b>
                        <span class="metric-pill" style="margin-left: 10px; font-size: 0.75rem;">{exp.get('impact', 'Info')}</span>
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.4;">
                        {exp.get('narrative', '')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    except MatchStateValidationError as ve:
        st.warning(f"Cricket Logic Alert: {str(ve)}")
    except Exception as e:
        st.error(f"Computation Error: {str(e)}")


# ==============================================================================
# TAB 3: 1ST INNINGS SCORE PROJECTION
# ==============================================================================
with tab3:
    st.markdown("#### 🎯 1st Innings Score Projection & Uncertainty Corridor")
    
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        s_bat_team = st.selectbox("Batting Team (1st Innings)", CANONICAL_TEAMS, index=0, key="s_bat")
    with s_col2:
        s_bowl_opts = [t for t in CANONICAL_TEAMS if t != s_bat_team]
        s_bowl_team = st.selectbox("Bowling Team", s_bowl_opts, index=0, key="s_bowl")

    s_i1, s_i2, s_i3, s_i4 = st.columns(4)
    with s_i1:
        s_score = st.number_input("Runs on Board", min_value=0, max_value=280, value=96, step=1, key="s_score")
    with s_i2:
        s_overs = st.number_input("Overs Bowled", min_value=1.0, max_value=19.5, value=11.4, step=0.1, key="s_overs")
    with s_i3:
        s_wickets = st.number_input("Wickets Down", min_value=0, max_value=9, value=2, step=1, key="s_wkts")
    with s_i4:
        s_r5 = st.number_input("Runs in Last 5 Overs", min_value=0, max_value=100, value=38, step=1, key="s_r5")

    try:
        score_res = predict_first_innings_score(
            batting_team=s_bat_team,
            bowling_team=s_bowl_team,
            current_score=s_score,
            overs_bowled=s_overs,
            wickets_fallen=s_wickets,
            runs_last_5=s_r5
        )

        pred_total = score_res["predicted_score"]
        lb = score_res["lower_bound"]
        ub = score_res["upper_bound"]

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            render_stat_box("Conservative Floor (10th %ile)", f"{lb}", "Rapid wickets scenario", icon="🛡️", color="#3b82f6")
        with sc2:
            render_stat_box("Projected Total", f"{pred_total}", f"CRR: {score_res['crr']:.2f} RPO", icon="🎯", color="#00f2fe")
        with sc3:
            render_stat_box("Aggressive Ceiling (90th %ile)", f"{ub}", "Unbroken death hitting", icon="🚀", color="#10b981")

        # Projected Innings Trajectory Line Chart
        traj = score_res.get("trajectory", [])
        if traj and len(traj) > 1:
            df_traj = pd.DataFrame(traj)
            
            fig = go.Figure()
            # Historical / Current pace
            fig.add_trace(go.Scatter(
                x=[0, s_overs],
                y=[0, s_score],
                mode="lines+markers",
                name="Actual Innings Run",
                line=dict(color="#00f2fe", width=3)
            ))
            # Projected trajectory
            fig.add_trace(go.Scatter(
                x=df_traj["over"],
                y=df_traj["score"],
                mode="lines",
                name="Expected AI Trajectory",
                line=dict(color="#38bdf8", width=3, dash="dash")
            ))
            # Upper bound fan
            fig.add_trace(go.Scatter(
                x=[s_overs, 20],
                y=[s_score, ub],
                mode="lines",
                name="Aggressive Finish (90%)",
                line=dict(color="#10b981", width=2, dash="dot")
            ))
            # Lower bound fan
            fig.add_trace(go.Scatter(
                x=[s_overs, 20],
                y=[s_score, lb],
                mode="lines",
                name="Conservative Finish (10%)",
                line=dict(color="#f59e0b", width=2, dash="dot")
            ))

            fig.update_layout(get_plotly_dark_layout("Projected Innings Trajectory Corridor to 20 Overs", height=380))
            fig.update_xaxes(title="Overs", range=[0, 20.5])
            fig.update_yaxes(title="Total Runs", range=[0, ub + 20])
            st.plotly_chart(fig, use_container_width=True)

        # Factor Attribution
        st.markdown("#### 🧠 Innings Dynamics & Boundary Assumptions")
        for exp in score_res.get("explanations", []):
            st.markdown(
                f"""
                <div class="xai-callout">
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="margin-right: 8px; font-size: 1.1rem;">{exp.get('icon', '⚡')}</span>
                        <b style="color: #f8fafc; font-size: 0.95rem;">{exp.get('category', 'Factor')}</b>
                        <span class="metric-pill" style="margin-left: 10px; font-size: 0.75rem;">{exp.get('impact', 'Info')}</span>
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.4;">
                        {exp.get('narrative', '')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    except MatchStateValidationError as ve:
        st.warning(f"Input Validation: {str(ve)}")
    except Exception as e:
        st.error(f"Score Model Error: {str(e)}")
