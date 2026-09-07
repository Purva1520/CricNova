"""
Winner Classifier Training and Model Benchmarking.
Evaluates Logistic Regression, Random Forest, and XGBoost for both Pre-Match and Live Chase Win Probability.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
import joblib
from pathlib import Path


PRE_MATCH_FEATURE_COLS = [
    "t1_win_pct", "t2_win_pct", "t1_form5", "t2_form5",
    "t1_h2h_win_pct", "venue_chase_win_pct", "venue_avg_1st_inns",
    "t1_bat_avg", "t2_bat_avg", "t1_bowl_w", "t2_bowl_w",
    "toss_won_by_t1", "toss_is_bat"
]

LIVE_CHASE_FEATURE_COLS = [
    "overs", "current_score", "wickets", "wickets_remaining",
    "runs_required", "balls_remaining", "target", "crr", "rrr",
    "run_rate_diff", "last_5_overs_runs", "pressure_factor",
    "momentum_score", "is_powerplay", "is_death"
]


def evaluate_classifier(model, X_train, y_train, X_test, y_test, model_name: str) -> dict:
    """Trains and computes full classification metrics on hold-out test set."""
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()

    return {
        "model_name": model_name,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": cm,
        "model_obj": model
    }


def train_and_benchmark_pre_match(pre_match_df: pd.DataFrame) -> tuple[dict, list[dict]]:
    """
    Chronological train/test split on pre_match_df (seasons <= 2017 for train, 2018-2019 for test).
    Benchmarks Logistic Regression, Random Forest, and XGBoost.
    Returns:
        tuple[dict, list[dict]]: (best_model_result, all_benchmarks)
    """
    df = pre_match_df.copy()
    
    # Chronological Split (prevents data leakage)
    split_mask = df["season"] <= 2017
    train_df = df[split_mask]
    test_df = df[~split_mask]

    X_train = train_df[PRE_MATCH_FEATURE_COLS]
    y_train = train_df["target"]
    X_test = test_df[PRE_MATCH_FEATURE_COLS]
    y_test = test_df["target"]

    candidates = [
        ("Logistic Regression", Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=0.5, max_iter=1000, random_state=42))
        ])),
        ("Random Forest", RandomForestClassifier(
            n_estimators=150, max_depth=6, min_samples_split=5, random_state=42
        )),
        ("XGBoost", xgb.XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.05,
            eval_metric="logloss", random_state=42
        ))
    ]

    benchmarks = []
    for name, clf in candidates:
        res = evaluate_classifier(clf, X_train, y_train, X_test, y_test, name)
        benchmarks.append(res)

    # Select best model by ROC-AUC
    best = max(benchmarks, key=lambda b: (b["roc_auc"], b["accuracy"]))
    return best, benchmarks


def train_and_benchmark_live_chase(chase_df: pd.DataFrame) -> tuple[dict, list[dict]]:
    """
    Chronological train/test split on live chase dataset (80% train, 20% test chronologically).
    Benchmarks Logistic Regression, Random Forest, and XGBoost.
    """
    df = chase_df.copy()
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    X_train = train_df[LIVE_CHASE_FEATURE_COLS]
    y_train = train_df["won_by_bat"]
    X_test = test_df[LIVE_CHASE_FEATURE_COLS]
    y_test = test_df["won_by_bat"]

    candidates = [
        ("Logistic Regression", Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=42))
        ])),
        ("Random Forest", RandomForestClassifier(
            n_estimators=150, max_depth=8, min_samples_leaf=4, random_state=42
        )),
        ("XGBoost", xgb.XGBClassifier(
            n_estimators=120, max_depth=5, learning_rate=0.08,
            eval_metric="logloss", random_state=42
        ))
    ]

    benchmarks = []
    for name, clf in candidates:
        res = evaluate_classifier(clf, X_train, y_train, X_test, y_test, name)
        benchmarks.append(res)

    best = max(benchmarks, key=lambda b: (b["roc_auc"], b["accuracy"]))
    return best, benchmarks


def extract_feature_importances(model_obj, feature_cols: list[str]) -> list[dict]:
    """Extracts normalized feature importance weights from trained model."""
    importances = None
    
    # Check if pipeline with LogisticRegression
    if hasattr(model_obj, "named_steps") and "clf" in model_obj.named_steps:
        clf = model_obj.named_steps["clf"]
        if hasattr(clf, "coef_"):
            importances = np.abs(clf.coef_[0])
    elif hasattr(model_obj, "feature_importances_"):
        importances = model_obj.feature_importances_

    if importances is None:
        importances = np.ones(len(feature_cols)) / len(feature_cols)
    else:
        # Normalize to sum to 100%
        importances = importances / np.sum(importances) * 100.0

    feat_list = []
    for col, imp in zip(feature_cols, importances):
        feat_list.append({
            "feature": col,
            "importance": round(float(imp), 2)
        })

    feat_list.sort(key=lambda x: x["importance"], reverse=True)
    return feat_list
