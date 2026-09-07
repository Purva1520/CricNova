"""
Unified Prediction Engine for CricNova.
Loads serialized models and provides inference pipelines for:
1. Pre-Match Winner Prediction
2. Live Chase Win Probability
3. First Innings Final Score Estimation
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import joblib
import numpy as np
import pandas as pd

from src.config import MODELS_DIR, TOP_VENUES
from src.validation import (
    validate_match_teams,
    validate_overs,
    validate_live_chase_state,
    validate_score_prediction_state,
    MatchStateValidationError
)
from src.explainability import (
    explain_pre_match_prediction,
    explain_live_chase_prediction,
    explain_score_prediction
)
from src.models.winner_classifier import PRE_MATCH_FEATURE_COLS, LIVE_CHASE_FEATURE_COLS
from src.models.score_regressor import SCORE_FEATURE_COLS


_CACHED_MODELS = {}


def load_artifacts():
    """Loads and caches models, stats tracker, and evaluation metrics."""
    global _CACHED_MODELS
    if "winner_pm" in _CACHED_MODELS:
        return _CACHED_MODELS

    pm_path = MODELS_DIR / "winner_pre_match.pkl"
    chase_path = MODELS_DIR / "winner_live_chase.pkl"
    score_path = MODELS_DIR / "score_model.pkl"
    tracker_path = MODELS_DIR / "stats_tracker.pkl"
    metrics_path = MODELS_DIR / "evaluation_metrics.json"

    if not pm_path.exists() or not chase_path.exists() or not score_path.exists():
        raise FileNotFoundError(
            "Trained model artifacts not found in models/. Please run train_models.py first."
        )

    _CACHED_MODELS["winner_pm"] = joblib.load(pm_path)
    _CACHED_MODELS["winner_chase"] = joblib.load(chase_path)
    _CACHED_MODELS["score_model"] = joblib.load(score_path)
    _CACHED_MODELS["stats_tracker"] = joblib.load(tracker_path) if tracker_path.exists() else None

    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as f:
            _CACHED_MODELS["metrics"] = json.load(f)
    else:
        _CACHED_MODELS["metrics"] = {}

    return _CACHED_MODELS


def predict_pre_match(
    team1: str,
    team2: str,
    venue: str,
    toss_winner: str,
    toss_decision: str
) -> Dict[str, Any]:
    """
    Computes pre-match victory probabilities for both teams before a ball is bowled.
    """
    validate_match_teams(team1, team2)
    artifacts = load_artifacts()
    model = artifacts["winner_pm"]
    tracker = artifacts["stats_tracker"]

    if tracker is not None:
        raw_feats = tracker.get_features_for_match(team1, team2, venue, toss_winner, toss_decision)
    else:
        # Fallback default features if tracker not loaded
        raw_feats = {
            "t1_win_pct": 0.50, "t2_win_pct": 0.50,
            "t1_form5": 0.50, "t2_form5": 0.50,
            "t1_h2h_win_pct": 0.50, "venue_chase_win_pct": 0.50,
            "venue_avg_1st_inns": 165.0, "t1_bat_avg": 160.0, "t2_bat_avg": 160.0,
            "t1_bowl_w": 5.5, "t2_bowl_w": 5.5,
            "toss_won_by_t1": 1 if toss_winner == team1 else 0,
            "toss_is_bat": 1 if str(toss_decision).lower() == "bat" else 0
        }

    feat_vector = pd.DataFrame([[raw_feats[c] for c in PRE_MATCH_FEATURE_COLS]], columns=PRE_MATCH_FEATURE_COLS)
    
    probs = model.predict_proba(feat_vector)[0]
    # Class 1 is team1 victory, Class 0 is team2 victory
    p_team1 = float(probs[1])
    p_team2 = float(probs[0])

    # Normalization check
    total = p_team1 + p_team2
    p_team1 /= total
    p_team2 /= total

    favored = team1 if p_team1 >= 0.5 else team2
    confidence_margin = abs(p_team1 - p_team2)
    # Confidence rating from 50% to 99%
    confidence_score = round(min(50.0 + confidence_margin * 50.0, 95.0), 1)

    explanations = explain_pre_match_prediction(
        team1=team1,
        team2=team2,
        venue=venue,
        toss_winner=toss_winner,
        toss_decision=toss_decision,
        win_prob_team1=p_team1,
        metrics=raw_feats
    )

    return {
        "team1": team1,
        "team2": team2,
        "team1_win_prob": round(p_team1, 4),
        "team2_win_prob": round(p_team2, 4),
        "favored_team": favored,
        "confidence_score": confidence_score,
        "features": raw_feats,
        "explanations": explanations
    }


def predict_live_chase(
    batting_team: str,
    bowling_team: str,
    target_score: int,
    current_score: int,
    overs_bowled: float,
    wickets_fallen: int,
    runs_last_5: Optional[int] = None,
    wickets_last_5: Optional[int] = None
) -> Dict[str, Any]:
    """
    Computes real-time win probability during the 2nd innings run chase.
    """
    validated = validate_live_chase_state(
        batting_team=batting_team,
        bowling_team=bowling_team,
        target_score=target_score,
        current_score=current_score,
        overs_bowled=overs_bowled,
        wickets_fallen=wickets_fallen,
        runs_last_5=runs_last_5,
        wickets_last_5=wickets_last_5
    )

    if validated.get("terminal"):
        p_batting = validated["win_probability"]
        p_bowling = 1.0 - p_batting
        return {
            "terminal": True,
            "batting_team": batting_team,
            "bowling_team": bowling_team,
            "batting_win_prob": p_batting,
            "bowling_win_prob": p_bowling,
            "crr": round(current_score / max(overs_bowled, 0.1), 2),
            "rrr": 0.0,
            "pressure_index": 0.0,
            "reason": validated["reason"],
            "explanations": [{
                "category": "Match Status",
                "impact": "Terminal State",
                "icon": "🏁",
                "narrative": validated["reason"]
            }]
        }

    artifacts = load_artifacts()
    model = artifacts["winner_chase"]

    balls_bowled = validated["balls_bowled"]
    balls_remaining = validated["balls_remaining"]
    wickets_in_hand = validated["wickets_in_hand"]
    runs_required = validated["runs_required"]
    r_last5 = validated["runs_last_5"]
    w_last5 = validated["wickets_last_5"]

    crr = round(current_score / max(overs_bowled, 0.1), 2)
    rrr = round((runs_required * 6.0) / max(balls_remaining, 1), 2)
    rr_diff = round(crr - rrr, 2)
    pressure_factor = round(rrr / (wickets_in_hand + 0.5), 2)
    momentum_score = round((r_last5 / 30.0) / max(rrr / 6.0, 0.5), 2)
    is_powerplay = 1 if overs_bowled <= 6.0 else 0
    is_death = 1 if overs_bowled >= 16.0 else 0

    input_data = {
        "overs": overs_bowled,
        "current_score": current_score,
        "wickets": wickets_fallen,
        "wickets_remaining": wickets_in_hand,
        "runs_required": runs_required,
        "balls_remaining": balls_remaining,
        "target": target_score,
        "crr": crr,
        "rrr": rrr,
        "run_rate_diff": rr_diff,
        "last_5_overs_runs": r_last5,
        "pressure_factor": pressure_factor,
        "momentum_score": momentum_score,
        "is_powerplay": is_powerplay,
        "is_death": is_death
    }

    feat_vector = pd.DataFrame([[input_data[c] for c in LIVE_CHASE_FEATURE_COLS]], columns=LIVE_CHASE_FEATURE_COLS)
    probs = model.predict_proba(feat_vector)[0]
    p_batting = float(probs[1])
    p_bowling = float(probs[0])

    explanations = explain_live_chase_prediction(
        batting_team=batting_team,
        bowling_team=bowling_team,
        target=target_score,
        current_score=current_score,
        balls_remaining=balls_remaining,
        wickets_in_hand=wickets_in_hand,
        crr=crr,
        rrr=rrr,
        win_prob_batting=p_batting,
        runs_last_5=r_last5,
        wickets_last_5=w_last5
    )

    return {
        "terminal": False,
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "batting_win_prob": round(p_batting, 4),
        "bowling_win_prob": round(p_bowling, 4),
        "crr": crr,
        "rrr": rrr,
        "run_rate_diff": rr_diff,
        "pressure_index": pressure_factor,
        "runs_required": runs_required,
        "balls_remaining": balls_remaining,
        "wickets_in_hand": wickets_in_hand,
        "features": input_data,
        "explanations": explanations
    }


def predict_first_innings_score(
    batting_team: str,
    bowling_team: str,
    current_score: int,
    overs_bowled: float,
    wickets_fallen: int,
    runs_last_5: Optional[int] = None,
    venue: str = "Wankhede Stadium"
) -> Dict[str, Any]:
    """
    Predicts 1st innings total score and uncertainty confidence intervals.
    """
    validated = validate_score_prediction_state(
        batting_team=batting_team,
        bowling_team=bowling_team,
        current_score=current_score,
        overs_bowled=overs_bowled,
        wickets_fallen=wickets_fallen,
        runs_last_5=runs_last_5
    )

    if validated.get("terminal"):
        final_val = validated["final_score"]
        return {
            "terminal": True,
            "batting_team": batting_team,
            "predicted_score": final_val,
            "lower_bound": final_val,
            "upper_bound": final_val,
            "crr": round(current_score / max(overs_bowled, 0.1), 2),
            "reason": validated["reason"],
            "trajectory": [{"over": overs_bowled, "score": final_val}],
            "explanations": [{
                "category": "Innings State",
                "impact": "Final Score",
                "icon": "🏁",
                "narrative": validated["reason"]
            }]
        }

    artifacts = load_artifacts()
    model = artifacts["score_model"]
    metrics = artifacts.get("metrics", {}).get("best_score", {})
    residual_std = metrics.get("residual_std", 18.0)

    balls_bowled = validated["balls_bowled"]
    balls_remaining = validated["balls_remaining"]
    r_last5 = validated["runs_last_5"]
    crr = round(current_score / max(overs_bowled, 0.1), 2)
    is_powerplay = 1 if overs_bowled <= 6.0 else 0
    is_middle = 1 if (6.0 < overs_bowled <= 15.0) else 0
    is_death = 1 if overs_bowled > 15.0 else 0

    input_data = {
        "overs": overs_bowled,
        "current_score": current_score,
        "wickets": wickets_fallen,
        "crr": crr,
        "balls_remaining": balls_remaining,
        "last_5_overs_runs": r_last5,
        "is_powerplay": is_powerplay,
        "is_middle": is_middle,
        "is_death": is_death
    }

    feat_vector = pd.DataFrame([[input_data[c] for c in SCORE_FEATURE_COLS]], columns=SCORE_FEATURE_COLS)
    raw_pred = float(model.predict(feat_vector)[0])
    
    # Must be at least current_score
    predicted_score = max(int(round(raw_pred)), current_score)

    # 80% confidence corridor: +/- 1.28 standard deviations
    lower_bound = max(int(round(predicted_score - 1.28 * residual_std)), current_score)
    upper_bound = int(round(predicted_score + 1.28 * residual_std))

    # Generate trajectory points from current over to over 20
    remaining_overs = 20.0 - overs_bowled
    trajectory = []
    current_int_over = int(overs_bowled)
    for ov in range(current_int_over, 21):
        if ov < overs_bowled:
            continue
        fraction = (ov - overs_bowled) / max(remaining_overs, 0.1)
        interp_score = int(round(current_score + fraction * (predicted_score - current_score)))
        trajectory.append({"over": ov, "score": interp_score})

    explanations = explain_score_prediction(
        predicted_score=predicted_score,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        current_score=current_score,
        overs_bowled=overs_bowled,
        wickets_fallen=wickets_fallen,
        crr=crr,
        venue_avg=165.0
    )

    return {
        "terminal": False,
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "predicted_score": predicted_score,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "crr": crr,
        "current_score": current_score,
        "overs_bowled": overs_bowled,
        "wickets_fallen": wickets_fallen,
        "trajectory": trajectory,
        "explanations": explanations
    }
