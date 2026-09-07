"""
Final Score Regressor Training and Model Benchmarking.
Evaluates Random Forest, Gradient Boosting, and XGBoost Regressor.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
import joblib


SCORE_FEATURE_COLS = [
    "overs", "current_score", "wickets", "crr", "balls_remaining",
    "last_5_overs_runs", "is_powerplay", "is_middle", "is_death"
]


def evaluate_regressor(model, X_train, y_train, X_test, y_test, model_name: str) -> dict:
    """Trains and computes regression metrics on hold-out test set."""
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(root_mean_squared_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))
    residuals = y_test - y_pred
    residual_std = float(np.std(residuals))

    return {
        "model_name": model_name,
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
        "residual_std": round(residual_std, 2),
        "model_obj": model
    }


def train_and_benchmark_score_model(score_df: pd.DataFrame) -> tuple[dict, list[dict]]:
    """
    Chronological 80/20 train/test split on 1st innings states.
    Benchmarks Random Forest Regressor, Gradient Boosting Regressor, and XGBoost Regressor.
    """
    df = score_df.copy()
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    X_train = train_df[SCORE_FEATURE_COLS]
    y_train = train_df["final_score"]
    X_test = test_df[SCORE_FEATURE_COLS]
    y_test = test_df["final_score"]

    candidates = [
        ("Random Forest Regressor", RandomForestRegressor(
            n_estimators=150, max_depth=8, min_samples_leaf=3, random_state=42
        )),
        ("Gradient Boosting Regressor", GradientBoostingRegressor(
            n_estimators=120, max_depth=4, learning_rate=0.08, random_state=42
        )),
        ("XGBoost Regressor", xgb.XGBRegressor(
            n_estimators=120, max_depth=5, learning_rate=0.08, random_state=42
        ))
    ]

    benchmarks = []
    for name, reg in candidates:
        res = evaluate_regressor(reg, X_train, y_train, X_test, y_test, name)
        benchmarks.append(res)

    # Select best model by lowest RMSE and highest R2
    best = min(benchmarks, key=lambda b: (b["rmse"], -b["r2"]))
    return best, benchmarks


def extract_score_feature_importances(model_obj, feature_cols: list[str]) -> list[dict]:
    """Extracts normalized feature importance weights from score regressor."""
    if hasattr(model_obj, "feature_importances_"):
        importances = model_obj.feature_importances_
    else:
        importances = np.ones(len(feature_cols)) / len(feature_cols)

    importances = importances / np.sum(importances) * 100.0
    feat_list = [
        {"feature": col, "importance": round(float(imp), 2)}
        for col, imp in zip(feature_cols, importances)
    ]
    feat_list.sort(key=lambda x: x["importance"], reverse=True)
    return feat_list
