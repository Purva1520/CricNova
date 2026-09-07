"""
Domain validation for cricket match scenarios and user inputs.
Guards against invalid cricket states, edge cases, and illegal parameters.
"""

from typing import Tuple, List, Optional
from src.config import CANONICAL_TEAMS


class MatchStateValidationError(ValueError):
    """Raised when match state parameters are logically or physically invalid."""
    pass


def validate_match_teams(batting_team: str, bowling_team: str) -> None:
    """Validates that teams are distinct and non-empty."""
    if not batting_team or not bowling_team:
        raise MatchStateValidationError("Both batting team and bowling team must be specified.")
    if batting_team.strip().lower() == bowling_team.strip().lower():
        raise MatchStateValidationError(
            f"Batting team and bowling team cannot be the same ({batting_team})."
        )


def validate_overs(overs: float) -> Tuple[int, int, int]:
    """
    Validates overs bowled in a standard 20-over T20 match.
    Returns:
        (completed_overs, balls_in_over, total_balls_bowled)
    """
    if overs < 0.0 or overs > 20.0:
        raise MatchStateValidationError(f"Overs bowled must be between 0.0 and 20.0. Received: {overs}")
    
    # Check over representation (e.g. 5.4 is 5 overs, 4 balls. 5.6 or 5.9 is invalid cricket notation)
    completed_overs = int(overs)
    decimal_part = round((overs - completed_overs) * 10)
    
    if decimal_part > 5:
        raise MatchStateValidationError(
            f"Invalid cricket overs notation: {overs}. The balls portion must be between .0 and .5."
        )
    
    if completed_overs == 20 and decimal_part > 0:
        raise MatchStateValidationError("Maximum overs in T20 is 20.0.")
        
    total_balls = completed_overs * 6 + decimal_part
    return completed_overs, decimal_part, total_balls


def validate_live_chase_state(
    batting_team: str,
    bowling_team: str,
    target_score: int,
    current_score: int,
    overs_bowled: float,
    wickets_fallen: int,
    runs_last_5: Optional[int] = None,
    wickets_last_5: Optional[int] = None
) -> dict:
    """
    Validates all parameters for 2nd innings live chase win probability calculation.
    Returns cleaned and normalized parameters with derived quantities.
    """
    validate_match_teams(batting_team, bowling_team)
    
    if target_score <= 0:
        raise MatchStateValidationError(f"Target score must be a positive integer. Received: {target_score}")
    if current_score < 0:
        raise MatchStateValidationError(f"Current score cannot be negative. Received: {current_score}")
    if wickets_fallen < 0 or wickets_fallen > 10:
        raise MatchStateValidationError(
            f"Wickets fallen must be between 0 and 10. Received: {wickets_fallen}"
        )
        
    completed_overs, balls_in_over, balls_bowled = validate_overs(overs_bowled)
    balls_remaining = 120 - balls_bowled
    runs_required = target_score - current_score
    wickets_in_hand = 10 - wickets_fallen
    
    # Check boundary terminal states
    if current_score >= target_score:
        return {
            "terminal": True,
            "winner": batting_team,
            "win_probability": 1.0,
            "reason": f"{batting_team} has already reached the target score of {target_score}."
        }
        
    if wickets_fallen == 10:
        return {
            "terminal": True,
            "winner": bowling_team,
            "win_probability": 0.0,
            "reason": f"{batting_team} is all out (10 wickets fallen) without reaching target."
        }
        
    if balls_remaining <= 0:
        return {
            "terminal": True,
            "winner": bowling_team if current_score < target_score - 1 else "Tie",
            "win_probability": 0.0,
            "reason": "All 20 overs (120 balls) have been bowled without reaching the target."
        }
        
    # Validate rolling 5 overs
    if runs_last_5 is not None:
        if runs_last_5 < 0:
            raise MatchStateValidationError("Runs in last 5 overs cannot be negative.")
        if runs_last_5 > current_score and balls_bowled >= 30:
            # If less than 30 balls bowled, runs_last_5 is simply all runs so far
            runs_last_5 = current_score
            
    if wickets_last_5 is not None:
        if wickets_last_5 < 0 or wickets_last_5 > 10:
            raise MatchStateValidationError("Wickets in last 5 overs must be between 0 and 10.")
        if wickets_last_5 > wickets_fallen:
            wickets_last_5 = wickets_fallen

    return {
        "terminal": False,
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "target_score": target_score,
        "current_score": current_score,
        "overs_bowled": overs_bowled,
        "balls_bowled": balls_bowled,
        "balls_remaining": balls_remaining,
        "wickets_fallen": wickets_fallen,
        "wickets_in_hand": wickets_in_hand,
        "runs_required": runs_required,
        "runs_last_5": runs_last_5 if runs_last_5 is not None else min(current_score, int(current_score / max(1, balls_bowled) * 30)),
        "wickets_last_5": wickets_last_5 if wickets_last_5 is not None else min(wickets_fallen, 2)
    }


def validate_score_prediction_state(
    batting_team: str,
    bowling_team: str,
    current_score: int,
    overs_bowled: float,
    wickets_fallen: int,
    runs_last_5: Optional[int] = None,
    wickets_last_5: Optional[int] = None
) -> dict:
    """
    Validates state for 1st innings score prediction.
    """
    validate_match_teams(batting_team, bowling_team)
    
    if current_score < 0:
        raise MatchStateValidationError(f"Current score cannot be negative. Received: {current_score}")
    if wickets_fallen < 0 or wickets_fallen > 10:
        raise MatchStateValidationError(
            f"Wickets fallen must be between 0 and 10. Received: {wickets_fallen}"
        )
        
    completed_overs, balls_in_over, balls_bowled = validate_overs(overs_bowled)
    balls_remaining = 120 - balls_bowled
    
    if wickets_fallen == 10:
        return {
            "terminal": True,
            "final_score": current_score,
            "reason": f"{batting_team} is all out at {current_score}."
        }
        
    if balls_remaining <= 0:
        return {
            "terminal": True,
            "final_score": current_score,
            "reason": f"Innings completed: 20 overs finished at {current_score} runs."
        }
        
    return {
        "terminal": False,
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "current_score": current_score,
        "overs_bowled": overs_bowled,
        "balls_bowled": balls_bowled,
        "balls_remaining": balls_remaining,
        "wickets_fallen": wickets_fallen,
        "wickets_in_hand": 10 - wickets_fallen,
        "runs_last_5": runs_last_5 if runs_last_5 is not None else min(current_score, int(current_score / max(1, balls_bowled) * 30)),
        "wickets_last_5": wickets_last_5 if wickets_last_5 is not None else min(wickets_fallen, 2)
    }
