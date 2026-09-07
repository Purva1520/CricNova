"""
Unit tests for CricNova unified prediction engine:
Pre-Match Winner, Live Chase Win Probability, and 1st Innings Score Projection.
"""

import pytest
from src.predictor import (
    predict_pre_match,
    predict_live_chase,
    predict_first_innings_score
)


def test_pre_match_prediction():
    res = predict_pre_match(
        team1="Mumbai Indians",
        team2="Chennai Super Kings",
        venue="Wankhede Stadium",
        toss_winner="Mumbai Indians",
        toss_decision="bat"
    )
    assert "favored_team" in res
    assert 0.0 <= res["team1_win_prob"] <= 1.0
    assert 0.0 <= res["team2_win_prob"] <= 1.0
    assert round(res["team1_win_prob"] + res["team2_win_prob"], 2) == 1.0
    assert len(res["explanations"]) >= 1


def test_pre_match_prediction_gt():
    """Verify Gujarat Titans works seamlessly in pre-match prediction."""
    res = predict_pre_match(
        team1="Gujarat Titans",
        team2="Mumbai Indians",
        venue="Wankhede Stadium",
        toss_winner="Gujarat Titans",
        toss_decision="field"
    )
    assert "favored_team" in res
    assert 0.0 <= res["team1_win_prob"] <= 1.0
    assert 0.0 <= res["team2_win_prob"] <= 1.0
    assert len(res["explanations"]) >= 1


def test_live_chase_prediction():
    res = predict_live_chase(
        batting_team="Royal Challengers Bangalore",
        bowling_team="Kolkata Knight Riders",
        target_score=170,
        current_score=110,
        overs_bowled=13.0,
        wickets_fallen=3,
        runs_last_5=40,
        wickets_last_5=1
    )
    assert res["terminal"] is False
    assert 0.0 <= res["batting_win_prob"] <= 1.0
    assert 0.0 <= res["bowling_win_prob"] <= 1.0
    assert round(res["batting_win_prob"] + res["bowling_win_prob"], 2) == 1.0
    assert res["rrr"] > 0
    assert res["crr"] > 0


def test_score_prediction():
    res = predict_first_innings_score(
        batting_team="Delhi Capitals",
        bowling_team="Rajasthan Royals",
        current_score=85,
        overs_bowled=10.0,
        wickets_fallen=2,
        runs_last_5=35
    )
    assert res["terminal"] is False
    assert res["predicted_score"] >= 85
    assert res["lower_bound"] <= res["predicted_score"] <= res["upper_bound"]
    assert len(res["trajectory"]) > 0
