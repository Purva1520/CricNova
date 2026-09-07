"""
SQLite Database Layer for CricNova.
Manages relational storage for teams, venues, matches, predictions, and user feedback.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
from src.config import DB_PATH, CANONICAL_TEAMS, TEAM_METADATA, TOP_VENUES


def get_db_connection():
    """Returns a SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        short_name TEXT NOT NULL,
        primary_color TEXT,
        secondary_color TEXT
    );

    CREATE TABLE IF NOT EXISTS venues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        city TEXT,
        country TEXT DEFAULT 'India',
        avg_score REAL,
        chase_win_pct REAL
    );

    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY,
        date TEXT,
        season INTEGER,
        team1 TEXT,
        team2 TEXT,
        venue TEXT,
        toss_winner TEXT,
        toss_decision TEXT,
        winner TEXT
    );

    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        mode TEXT NOT NULL,
        team1 TEXT NOT NULL,
        team2 TEXT NOT NULL,
        venue TEXT NOT NULL,
        prediction TEXT NOT NULL,
        team1_probability REAL,
        team2_probability REAL,
        predicted_score INTEGER,
        score_min INTEGER,
        score_max INTEGER,
        confidence TEXT,
        explanation TEXT,
        factors_json TEXT
    );

    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction_id INTEGER,
        rating INTEGER NOT NULL,
        reaction_tag TEXT,
        feedback_text TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (prediction_id) REFERENCES predictions(id)
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT DEFAULT 'analyst',
        created_at TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()


def seed_reference_data(matches_clean: pd.DataFrame = None):
    """Populates teams, venues, and historical matches if empty."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Seed teams
    for team, meta in TEAM_METADATA.items():
        cursor.execute("""
            INSERT OR IGNORE INTO teams (name, short_name, primary_color, secondary_color)
            VALUES (?, ?, ?, ?)
        """, (team, meta["short"], meta["primary_color"], meta["secondary_color"]))

    # 2. Seed venues & matches if provided
    if matches_clean is not None and not matches_clean.empty:
        # Venues
        venue_stats = matches_clean.groupby("venue").agg(
            city=("city", "first"),
            match_count=("id", "count")
        ).reset_index()

        for _, v in venue_stats.iterrows():
            cursor.execute("""
                INSERT OR IGNORE INTO venues (name, city, country)
                VALUES (?, ?, 'India')
            """, (v["venue"], v["city"] if pd.notnull(v["city"]) else "India"))

        # Matches
        for _, m in matches_clean.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO matches (id, date, season, team1, team2, venue, toss_winner, toss_decision, winner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(m["id"]),
                str(m["date"])[:10],
                int(m["season"]),
                str(m["team1"]),
                str(m["team2"]),
                str(m["venue"]),
                str(m["toss_winner"]),
                str(m["toss_decision"]),
                str(m["winner"])
            ))

    conn.commit()
    conn.close()


def save_prediction(mode: str, team1: str, team2: str, venue: str, prediction: str,
                    team1_prob: float = None, team2_prob: float = None,
                    predicted_score: int = None, score_min: int = None, score_max: int = None,
                    confidence: str = "Medium", explanation: str = "", factors: list = None) -> int:
    """Inserts a new prediction log and returns its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    factors_json = json.dumps(factors or [])

    cursor.execute("""
        INSERT INTO predictions (
            timestamp, mode, team1, team2, venue, prediction,
            team1_probability, team2_probability, predicted_score,
            score_min, score_max, confidence, explanation, factors_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, mode, team1, team2, venue, prediction,
        team1_prob, team2_prob, predicted_score,
        score_min, score_max, confidence, explanation, factors_json
    ))

    pred_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pred_id


def save_feedback(prediction_id: int, rating: int, reaction_tag: str, feedback_text: str = "") -> int:
    """Saves user rating and feedback for a prediction."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO feedback (prediction_id, rating, reaction_tag, feedback_text, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (prediction_id, rating, reaction_tag, feedback_text, timestamp))

    fb_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return fb_id


def get_prediction_history(limit: int = 50) -> list[dict]:
    """Fetches recent prediction records with optional feedback info."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*, f.rating, f.reaction_tag, f.feedback_text
        FROM predictions p
        LEFT JOIN feedback f ON p.id = f.prediction_id
        ORDER BY p.id DESC
        LIMIT ?
    """, (limit,))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_database_analytics() -> dict:
    """Calculates summary KPIs from predictions and user feedback."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total predictions
    cursor.execute("SELECT COUNT(*) FROM predictions")
    total_preds = cursor.fetchone()[0]

    # Average score
    cursor.execute("SELECT AVG(predicted_score) FROM predictions WHERE predicted_score IS NOT NULL")
    avg_score_row = cursor.fetchone()[0]
    avg_score = round(avg_score_row, 1) if avg_score_row else 168.0

    # Most predicted team
    cursor.execute("""
        SELECT prediction, COUNT(*) as cnt
        FROM predictions
        WHERE mode IN ('Pre-Match Winner', 'Live Win Probability')
        GROUP BY prediction
        ORDER BY cnt DESC
        LIMIT 1
    """)
    top_team_row = cursor.fetchone()
    top_team = top_team_row[0] if top_team_row else "Mumbai Indians"

    # Feedback stats
    cursor.execute("SELECT COUNT(*), AVG(rating) FROM feedback")
    fb_count, avg_rating = cursor.fetchone()
    avg_rating = round(avg_rating, 2) if avg_rating else 4.5

    # Feedback reaction distribution
    cursor.execute("""
        SELECT reaction_tag, COUNT(*) as count
        FROM feedback
        WHERE reaction_tag IS NOT NULL
        GROUP BY reaction_tag
    """)
    reactions = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()
    return {
        "total_predictions": total_preds,
        "avg_predicted_score": avg_score,
        "most_predicted_team": top_team,
        "feedback_count": fb_count or 0,
        "average_rating": avg_rating,
        "reaction_distribution": reactions
    }


def create_user(name: str, email: str, password_hash: str, salt: str, role: str = "analyst") -> int:
    """Inserts a new user record into the users table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, salt, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name.strip(), email.strip().lower(), password_hash, salt, role, created_at))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email: str) -> dict | None:
    """Retrieves a user by email address (case-insensitive)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    """Retrieves a user by user ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


if __name__ == "__main__":
    init_db()
    print("Initialized database at", DB_PATH)
    pid = save_prediction("Pre-Match Winner", "Mumbai Indians", "Chennai Super Kings", "Wankhede Stadium", "Mumbai Indians", 0.62, 0.38, confidence="High", explanation="Strong venue record and form.")
    print("Saved test prediction ID:", pid)
    save_feedback(pid, 5, "Very accurate", "Spot on prediction for Wankhede!")
    print("Analytics:", get_database_analytics())
