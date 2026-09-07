"""
Automated, Reproducible Model Training Pipeline for CricNova.
Executes end-to-end data ingestion, time-aware feature engineering,
multi-model benchmarking, and model artifact serialization.
"""

import json
import sys
from pathlib import Path

# Configure utf-8 output for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import joblib
from src.config import MODELS_DIR
from src.data_loader import load_raw_data
from src.preprocessing import get_cleaned_data
from src.database import init_db, seed_reference_data
from src.auth import ensure_demo_user
from src.feature_engineering import (
    build_pre_match_features_dataset,
    build_live_chase_dataset,
    build_first_innings_score_dataset
)
from src.models.winner_classifier import (
    train_and_benchmark_pre_match,
    train_and_benchmark_live_chase,
    extract_feature_importances,
    PRE_MATCH_FEATURE_COLS,
    LIVE_CHASE_FEATURE_COLS
)
from src.models.score_regressor import (
    train_and_benchmark_score_model,
    extract_score_feature_importances,
    SCORE_FEATURE_COLS
)


def train_all_models():
    """Runs full pipeline and serializes best models and evaluation metrics."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    ensure_demo_user()

    print("\n=======================================================")
    print("[CRICNOVA] STARTING END-TO-END MODEL TRAINING PIPELINE")
    print("=======================================================\n")

    # Step 1: Load Data
    print("Step 1: Loading raw IPL dataset...")
    m_raw, d_raw = load_raw_data()
    print(f" -> Raw: {len(m_raw)} matches, {len(d_raw)} deliveries.")

    # Step 2: Clean & Preprocess
    print("\nStep 2: Cleaning data and standardizing entities...")
    m_clean, d_clean = get_cleaned_data(m_raw, d_raw)
    print(f" -> Clean: {len(m_clean)} matches, {len(d_clean)} deliveries.")

    # Step 3: Seed Reference Database
    print("\nStep 3: Seeding SQLite database with reference matches & venues...")
    seed_reference_data(m_clean)

    # Step 4: Feature Engineering (No Data Leakage)
    print("\nStep 4: Engineering time-aware features...")
    pm_df, tracker = build_pre_match_features_dataset(m_clean, d_clean)
    chase_df = build_live_chase_dataset(m_clean, d_clean)
    score_df = build_first_innings_score_dataset(m_clean, d_clean)
    print(f" -> Pre-match samples: {len(pm_df)}")
    print(f" -> Live chase samples: {len(chase_df)}")
    print(f" -> Score regression samples: {len(score_df)}")

    # Step 5: Train & Benchmark Pre-Match Winner Model
    print("\nStep 5: Benchmarking Pre-Match Winner Classifiers (LR vs RF vs XGB)...")
    best_pm, pm_benchmarks = train_and_benchmark_pre_match(pm_df)
    for b in pm_benchmarks:
        print(f"   [{b['model_name']}] Acc: {b['accuracy']:.4f} | ROC-AUC: {b['roc_auc']:.4f} | F1: {b['f1']:.4f}")
    print(f" -> Selected Best Pre-Match Model: {best_pm['model_name']}")

    # Step 6: Train & Benchmark Live Chase Model
    print("\nStep 6: Benchmarking Live Chase Win Probability Classifiers...")
    best_chase, chase_benchmarks = train_and_benchmark_live_chase(chase_df)
    for b in chase_benchmarks:
        print(f"   [{b['model_name']}] Acc: {b['accuracy']:.4f} | ROC-AUC: {b['roc_auc']:.4f} | F1: {b['f1']:.4f}")
    print(f" -> Selected Best Live Chase Model: {best_chase['model_name']}")

    # Step 7: Train & Benchmark Final Score Regressor
    print("\nStep 7: Benchmarking Final Score Regressors (RF vs GB vs XGB)...")
    best_score, score_benchmarks = train_and_benchmark_score_model(score_df)
    for b in score_benchmarks:
        print(f"   [{b['model_name']}] RMSE: {b['rmse']:.2f} | MAE: {b['mae']:.2f} | R2: {b['r2']:.4f}")
    print(f" -> Selected Best Score Regressor: {best_score['model_name']}")

    # Step 8: Save Model Artifacts
    print("\nStep 8: Serializing trained models and preprocessors to models/...")
    joblib.dump(best_pm["model_obj"], MODELS_DIR / "winner_pre_match.pkl")
    joblib.dump(best_chase["model_obj"], MODELS_DIR / "winner_live_chase.pkl")
    joblib.dump(best_score["model_obj"], MODELS_DIR / "score_model.pkl")
    joblib.dump(tracker, MODELS_DIR / "stats_tracker.pkl")

    # Step 9: Extract and Save Metrics and Feature Importance
    print("\nStep 9: Generating explainability and evaluation metrics...")
    pm_feat_imp = extract_feature_importances(best_pm["model_obj"], PRE_MATCH_FEATURE_COLS)
    chase_feat_imp = extract_feature_importances(best_chase["model_obj"], LIVE_CHASE_FEATURE_COLS)
    score_feat_imp = extract_score_feature_importances(best_score["model_obj"], SCORE_FEATURE_COLS)

    def sanitize_benchmarks(b_list):
        clean = []
        for item in b_list:
            d = dict(item)
            d.pop("model_obj", None)
            clean.append(d)
        return clean

    evaluation_report = {
        "dataset_summary": {
            "total_matches": len(m_clean),
            "total_deliveries": len(d_clean),
            "pre_match_samples": len(pm_df),
            "live_chase_samples": len(chase_df),
            "score_samples": len(score_df),
            "seasons": sorted([int(s) for s in m_clean["season"].unique()])
        },
        "pre_match_benchmarks": sanitize_benchmarks(pm_benchmarks),
        "best_pre_match": {
            "name": best_pm["model_name"],
            "accuracy": best_pm["accuracy"],
            "roc_auc": best_pm["roc_auc"],
            "confusion_matrix": best_pm["confusion_matrix"],
            "feature_importances": pm_feat_imp
        },
        "live_chase_benchmarks": sanitize_benchmarks(chase_benchmarks),
        "best_live_chase": {
            "name": best_chase["model_name"],
            "accuracy": best_chase["accuracy"],
            "roc_auc": best_chase["roc_auc"],
            "confusion_matrix": best_chase["confusion_matrix"],
            "feature_importances": chase_feat_imp
        },
        "score_benchmarks": sanitize_benchmarks(score_benchmarks),
        "best_score": {
            "name": best_score["model_name"],
            "rmse": best_score["rmse"],
            "mae": best_score["mae"],
            "r2": best_score["r2"],
            "residual_std": best_score["residual_std"],
            "feature_importances": score_feat_imp
        }
    }

    with open(MODELS_DIR / "evaluation_metrics.json", "w") as f:
        json.dump(evaluation_report, f, indent=2)

    print(f" -> Metrics and artifacts saved to {MODELS_DIR}")
    print("\n[SUCCESS] ALL MODELS TRAINED AND VALIDATED SUCCESSFULLY!")
    print("=======================================================\n")
    return evaluation_report


if __name__ == "__main__":
    train_all_models()
