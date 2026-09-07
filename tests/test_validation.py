"""
Automated unit tests for domain validation and cricket physics guards.
"""

import pytest
from src.validation import (
    validate_match_teams,
    validate_overs,
    validate_live_chase_state,
    validate_score_prediction_state,
    MatchStateValidationError
)


def test_validate_match_teams_success():
    # Different teams should pass without error
    validate_match_teams("Mumbai Indians", "Chennai Super Kings")


def test_validate_match_teams_identical():
    # Identical teams should raise MatchStateValidationError
    with pytest.raises(MatchStateValidationError):
        validate_match_teams("Mumbai Indians", "mumbai indians")


def test_validate_overs_valid():
    completed, balls, total = validate_overs(5.4)
    assert completed == 5
    assert balls == 4
    assert total == 34


def test_validate_overs_invalid_ball_notation():
    # 5.6 is invalid in cricket notation (max is 5.5)
    with pytest.raises(MatchStateValidationError):
        validate_overs(5.6)


def test_validate_overs_out_of_bounds():
    with pytest.raises(MatchStateValidationError):
        validate_overs(21.0)
    with pytest.raises(MatchStateValidationError):
        validate_overs(-1.0)


def test_validate_live_chase_terminal_target_reached():
    res = validate_live_chase_state(
        batting_team="Mumbai Indians",
        bowling_team="Chennai Super Kings",
        target_score=150,
        current_score=152,
        overs_bowled=18.2,
        wickets_fallen=4
    )
    assert res["terminal"] is True
    assert res["win_probability"] == 1.0


def test_validate_live_chase_terminal_all_out():
    res = validate_live_chase_state(
        batting_team="Mumbai Indians",
        bowling_team="Chennai Super Kings",
        target_score=180,
        current_score=140,
        overs_bowled=17.0,
        wickets_fallen=10
    )
    assert res["terminal"] is True
    assert res["win_probability"] == 0.0


def test_validate_score_terminal_all_out():
    res = validate_score_prediction_state(
        batting_team="Mumbai Indians",
        bowling_team="Chennai Super Kings",
        current_score=110,
        overs_bowled=14.0,
        wickets_fallen=10
    )
    assert res["terminal"] is True
    assert res["final_score"] == 110
