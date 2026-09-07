"""
CricNova — Academic Model Laboratory & ML Evaluation Center
Benchmarking Logistic Regression, Random Forest, Gradient Boosting, and XGBoost.
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Model Lab | CricNova", page_icon="🤖", layout="wide")

from src.ui_components import (
    inject_custom_css,
    render_header,
    render_stat_box,
    render_provenance_badge,
    get_plotly_dark_layout
)
from src.config import MODELS_DIR

inject_custom_css()

render_header(
    title="Machine Learning Laboratory & Model Benchmarks",
    subtitle="Rigorous multi-model evaluation across Scikit-Learn and XGBoost with Explainable AI attribution.",
    badge="ML EVALUATION SUITE"
)
render_provenance_badge("ANALYSIS")

# Load metrics json
metrics_file = MODELS_DIR / "evaluation_metrics.json"
if not metrics_file.exists():
    st.warning("Model metrics not found. Please run `python train_models.py` first.")
    st.stop()

with open(metrics_file, "r", encoding="utf-8") as f:
    metrics = json.load(f)

ds = metrics.get("dataset_summary", {})

# Dataset Summary KPIs
m1, m2, m3, m4 = st.columns(4)
with m1:
    render_stat_box("Total Matches", f"{ds.get('total_matches', 752)}", "Seasons 2008-2019", icon="📅", color="#00f2fe")
with m2:
    render_stat_box("Deliveries Cleaned", f"{ds.get('total_deliveries', 178610):,}", "Granular ball events", icon="⚾", color="#3b82f6")
with m3:
    render_stat_box("Live Chase States", f"{ds.get('live_chase_samples', 13331):,}", "In-game situation rows", icon="⚡", color="#10b981")
with m4:
    render_stat_box("Score States", f"{ds.get('score_samples', 11130):,}", "1st innings over rows", icon="🎯", color="#f59e0b")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# Tabs: Benchmark Sections
lab_tab1, lab_tab2, lab_tab3 = st.tabs([
    "🏆 Pre-Match Winner Classifiers",
    "⚡ Live Chase Win Probability",
    "🎯 1st Innings Score Regressors"
])

# TAB 1: Pre-match
with lab_tab1:
    st.markdown("### 📊 Pre-Match Winner Classification Benchmarks")
    st.caption("Chronological Hold-Out Validation: Seasons ≤ 2017 for Training, 2018–2019 for Hold-Out Testing.")

    pm_bench = metrics.get("pre_match_benchmarks", [])
    if pm_bench:
        df_pm = pd.DataFrame(pm_bench)
        st.dataframe(
            df_pm[["model_name", "accuracy", "roc_auc", "precision", "recall", "f1"]]
            .rename(columns={"model_name": "Model", "accuracy": "Accuracy", "roc_auc": "ROC-AUC", "precision": "Precision", "recall": "Recall", "f1": "F1-Score"})
            .style.highlight_max(subset=["Accuracy", "ROC-AUC"], color="#0369a1"),
            use_container_width=True,
            hide_index=True
        )

    # Feature Importance for Pre-Match
    st.markdown("#### 🔍 Pre-Match Feature Importance Weights")
    pm_feats = metrics.get("best_pre_match", {}).get("feature_importances", [])
    if pm_feats:
        df_pfeat = pd.DataFrame(pm_feats)
        fig_pfeat = px.bar(
            df_pfeat,
            x="importance",
            y="feature",
            orientation="h",
            color="importance",
            color_continuous_scale="Viridis"
        )
        fig_pfeat.update_layout(get_plotly_dark_layout("Feature Attribution (% Weight)", height=340))
        fig_pfeat.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_pfeat, use_container_width=True)

# TAB 2: Live Chase
with lab_tab2:
    st.markdown("### 📊 Live Chase Win Probability Classifiers")
    st.caption("Hold-Out Evaluation on 20% Chronological split across 13,331 in-game over states.")

    chase_bench = metrics.get("live_chase_benchmarks", [])
    if chase_bench:
        df_chase = pd.DataFrame(chase_bench)
        st.dataframe(
            df_chase[["model_name", "accuracy", "roc_auc", "precision", "recall", "f1"]]
            .rename(columns={"model_name": "Model", "accuracy": "Accuracy", "roc_auc": "ROC-AUC", "precision": "Precision", "recall": "Recall", "f1": "F1-Score"})
            .style.highlight_max(subset=["Accuracy", "ROC-AUC"], color="#0369a1"),
            use_container_width=True,
            hide_index=True
        )

    # Confusion Matrix for Best Live Chase Model
    c_cm, c_imp = st.columns(2)
    with c_cm:
        st.markdown("#### 🎯 Confusion Matrix (Best Classifier)")
        cm_data = metrics.get("best_live_chase", {}).get("confusion_matrix", [[0, 0], [0, 0]])
        fig_cm = px.imshow(
            cm_data,
            labels=dict(x="Predicted Class", y="Actual Class", color="Count"),
            x=["Loss", "Win"],
            y=["Loss", "Win"],
            color_continuous_scale="Blues",
            text_auto=True
        )
        fig_cm.update_layout(get_plotly_dark_layout("Hold-Out Test Confusion Matrix", height=340))
        st.plotly_chart(fig_cm, use_container_width=True)

    with c_imp:
        st.markdown("#### 🔍 Live Dynamic Feature Importances")
        chase_feats = metrics.get("best_live_chase", {}).get("feature_importances", [])
        if chase_feats:
            df_cfeats = pd.DataFrame(chase_feats)
            fig_cfeat = px.bar(
                df_cfeats,
                x="importance",
                y="feature",
                orientation="h",
                color="importance",
                color_continuous_scale="Teal"
            )
            fig_cfeat.update_layout(get_plotly_dark_layout("Live Chase Feature Attribution", height=340))
            fig_cfeat.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_cfeat, use_container_width=True)

# TAB 3: Score Regressors
with lab_tab3:
    st.markdown("### 📊 1st Innings Score Regressor Benchmarks")
    st.caption("Benchmarking Random Forest Regressor, Gradient Boosting, and XGBoost Regressor.")

    score_bench = metrics.get("score_benchmarks", [])
    if score_bench:
        df_score = pd.DataFrame(score_bench)
        st.dataframe(
            df_score[["model_name", "rmse", "mae", "r2", "residual_std"]]
            .rename(columns={"model_name": "Model", "rmse": "RMSE (Runs)", "mae": "MAE (Runs)", "r2": "R² Score", "residual_std": "Residual Std"})
            .style.highlight_min(subset=["RMSE (Runs)", "MAE (Runs)"], color="#0369a1"),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("#### 🔍 Score Regressor Feature Attribution")
    score_feats = metrics.get("best_score", {}).get("feature_importances", [])
    if score_feats:
        df_sfeat = pd.DataFrame(score_feats)
        fig_sfeat = px.bar(
            df_sfeat,
            x="importance",
            y="feature",
            orientation="h",
            color="importance",
            color_continuous_scale="Plasma"
        )
        fig_sfeat.update_layout(get_plotly_dark_layout("Score Regression Feature Attribution", height=340))
        fig_sfeat.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_sfeat, use_container_width=True)
