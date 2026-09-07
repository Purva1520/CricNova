"""
Unit tests for SQLite database operations, predictions logging, and user feedback.
"""

from src.database import (
    init_db,
    save_prediction,
    save_feedback,
    get_prediction_history,
    get_database_analytics
)


def test_database_crud():
    init_db()
    pid = save_prediction(
        mode="Pre-Match Winner",
        team1="Chennai Super Kings",
        team2="Mumbai Indians",
        venue="MA Chidambaram Stadium, Chepauk",
        prediction="Chennai Super Kings",
        team1_prob=0.55,
        team2_prob=0.45,
        confidence="High",
        explanation="Home turf spin advantage."
    )
    assert pid > 0

    fid = save_feedback(
        prediction_id=pid,
        rating=5,
        reaction_tag="Spot on",
        feedback_text="Chepauk spin was decisive."
    )
    assert fid > 0

    history = get_prediction_history(limit=10)
    assert len(history) > 0
    assert any(h["id"] == pid for h in history)

    analytics = get_database_analytics()
    assert analytics["total_predictions"] >= 1
    assert analytics["average_rating"] > 0
