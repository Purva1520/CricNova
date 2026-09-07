"""
CricNova — Academic Methodology, System Architecture & Viva Guide
"""

import streamlit as st

st.set_page_config(page_title="Methodology | CricNova", page_icon="ℹ️", layout="wide")

from src.ui_components import (
    inject_custom_css,
    render_header
)

inject_custom_css()

render_header(
    title="Academic Methodology & Technical Handbook",
    subtitle="Zero Data Leakage Proof, System Architecture, Mathematical Formulations, and Viva Voce Defense Guide.",
    badge="ACADEMIC DOCUMENTATION"
)

# Section 1: Core Problem Statement
st.markdown("### 🎯 Problem Statement & Mission")
st.markdown(
    """
    <div class="stadium-card">
        <p style="color: #cbd5e1; font-size: 1rem; line-height: 1.6; margin: 0;">
            Cricket is inherently a non-linear, stochastic game characterized by sudden momentum shifts, phase transitions, and asymmetric pitch deterioration. Traditional statistical approaches rely on static batting or bowling averages that fail to capture in-game leverage and time-series evolution. 
            <b>CricNova</b> was engineered to bridge this gap by uniting <b>time-aware feature engineering</b> (strictly eliminating lookahead bias), <b>multi-model ML benchmarking</b> (Logistic Regression, Random Forest, Gradient Boosting, XGBoost), <b>domain-constrained physics guards</b>, and <b>Explainable AI attribution</b> into an integrated, industrial-grade intelligence suite.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Section 2: End-to-End Architecture
st.markdown("### 🏗️ End-to-End System Architecture")
st.markdown(
    """
    ```
    +-----------------------------------------------------------------------------------+
    |                             DATA INGESTION & PIPELINE                             |
    |  • Kaggle Ball-by-Ball IPL Dataset (752 Matches, 178k Deliveries, 2008-2019)       |
    |  • Entity Normalization (Canonical Franchises: CSK, DC, GT, KKR, LSG, MI, etc.)   |
    +-----------------------------------------------------------------------------------+
                                            │
                                            ▼
    +-----------------------------------------------------------------------------------+
    |                         ZERO DATA LEAKAGE FEATURE ENGINE                          |
    |  • HistoricalStatsTracker: State for Match i strictly computed from Matches < i   |
    |  • Rolling Form (Last 5 matches), Head-to-Head win %, Venue Par Innings Score     |
    |  • Live Chase Dynamics: CRR, RRR, Pressure Index, Momentum (Last 5 overs)          |
    +-----------------------------------------------------------------------------------+
                                            │
                                            ▼
    +-----------------------------------------------------------------------------------+
    |                        MULTI-MODEL BENCHMARKING & INFERENCE                       |
    |  • Pre-Match Winner Classifier: Logistic Regression vs Random Forest vs XGBoost   |
    |  • Live Chase Win Probability: Calibrated Logit & Forest Classifiers (ROC > 0.82) |
    |  • 1st Innings Score Regressor: Gradient Boosting with 80% Uncertainty Corridor   |
    |  • Domain Constrained Physics Guards: Terminal States & Run-Floor Invariants      |
    +-----------------------------------------------------------------------------------+
                                            │
                                            ▼
    +-----------------------------------------------------------------------------------+
    |                      EXPLAINABLE AI & PERSISTENCE LAYER                           |
    |  • Human-Readable Factor Attribution (Run Rate, Wicket Capital, Momentum, Pitch)  |
    |  • SQLite Storage: Predictions, In-Play Inputs, User Star Ratings & Feedback Loop |
    |  • Dark Stadium Responsive UI: Streamlit, Plotly Visualizations, Model Lab        |
    +-----------------------------------------------------------------------------------+
    ```
    """
)

# Section 3: Data Leakage Prevention Proof
st.markdown("### 🛡️ Proof of Zero Data Leakage (Lookahead Bias Prevention)")
st.markdown(
    """
    <div class="xai-callout">
        <b style="color: #00f2fe; font-size: 1.05rem;">Critical Academic Invariant</b>
        <p style="color: #cbd5e1; font-size: 0.92rem; margin-top: 6px; line-height: 1.5;">
            In sports predictive modeling, a fatal flaw in amateur pipelines is calculating team win rates or venue scores over the <i>entire dataset</i>. If a team's 2019 championship run is used to calculate their strength rating in a 2012 match, the model commits severe <b>lookahead data leakage</b>.
        </p>
        <p style="color: #cbd5e1; font-size: 0.92rem; margin: 0; line-height: 1.5;">
            In <b>CricNova</b>, matches are sorted strictly in chronological order. We implement the <code>HistoricalStatsTracker</code> class: before match <i>i</i> is processed, feature vectors are queried strictly from prior games <i>k &lt; i</i>. Only after the match prediction vector is logged is the tracker state updated with the match result.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Section 4: Comprehensive Viva Voce / Presentation Defense Guide
st.markdown("---")
st.markdown("### 🎓 Comprehensive Viva Voce / Presentation Defense Guide")

with st.expander("Q1: Why did Logistic Regression achieve the highest ROC-AUC on Live Chase Win Probability?"):
    st.markdown(
        """
        **Answer:** In cricket run chases, the probability of winning is primarily governed by the log-odds of two linear ratios:
        1. **Run Rate Gap:** `CRR - RRR`
        2. **Resource Cushion:** `Wickets Remaining / Overs Remaining`
        
        Because the underlying physics of a cricket chase map naturally to a logistic curve (as RRR approaches infinity, win probability approaches 0 asymptotically; when RRR is low and wickets are high, it approaches 1 asymptotically), a well-regularized Logistic Regression model produces exceptionally well-calibrated probabilities without overfitting the variance of individual matches, whereas uncalibrated deep decision trees can suffer from step-function probability jumps.
        """
    )

with st.expander("Q2: How are AI/ML predictions strictly distinguished from historical statistics in CricNova?"):
    st.markdown(
        """
        **Answer:** 
        - **Actual Historical Data:** Displayed on League Analytics and Team Radar pages, directly derived and aggregated from the 752 official IPL matches and 178,610 ball delivery records (2008–2019). No synthetic or fake match results are fabricated.
        - **AI/ML Model Inferences:** Displayed with prominent `AI/ML PREDICTION` and `AI INSIGHT` badges, representing probabilistic expectations derived from machine learning models trained on time-aware historical features. Missing historical overlaps (such as GT vs CSK during CSK's suspension era) are explicitly documented as era-boundary limits rather than synthesized numbers.
        """
    )

with st.expander("Q3: How does CricNova handle physical and logical boundary conditions?"):
    st.markdown(
        """
        **Answer:** We implemented a dedicated domain validation module (`src/validation.py`) guarding against:
        - **Terminal State 1:** Target already reached (`current_score >= target_score` -> 100% win probability for batting side).
        - **Terminal State 2:** All-out (`wickets == 10` -> 0% win probability for batting side).
        - **Terminal State 3:** Overs exhausted (`overs == 20.0`).
        - **Format Invariants:** Cricket overs notation validation (`.0` to `.5` balls only).
        - **Boundary Floor:** Predicted final score cannot physically drop below the runs currently on the board.
        """
    )

with st.expander("Q4: What is the significance of the 'Pressure Index' and 'Momentum Score' features?"):
    st.markdown(
        """
        **Answer:**
        - **Pressure Index:** Defined mathematically as $\\text{Pressure} = \\frac{\\text{RRR}}{\\text{Wickets in Hand} + 0.5}$. When wickets fall, the denominator shrinks rapidly, multiplying the pressure on incoming batsmen.
        - **Momentum Score:** Defined as the ratio of scoring rate in the last 5 overs relative to par required rate. A team scoring 50 runs in overs 10-15 has psychological and tactical momentum compared to a team that scored 20 runs in the same phase.
        """
    )

# Tech Stack Pills
st.markdown("---")
st.markdown("### 💻 Core Technology Stack")
st.markdown(
    """
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px;">
        <span class="metric-pill">Python 3.13</span>
        <span class="metric-pill">Scikit-Learn 1.9</span>
        <span class="metric-pill">XGBoost 3.4.1</span>
        <span class="metric-pill">Streamlit 1.63</span>
        <span class="metric-pill">Plotly 7.0</span>
        <span class="metric-pill">SQLite 3</span>
        <span class="metric-pill">Pandas & NumPy</span>
        <span class="metric-pill">Joblib</span>
    </div>
    """,
    unsafe_allow_html=True
)
