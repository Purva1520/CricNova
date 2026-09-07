"""
Feature Engineering Engine for CricNova.
Constructs time-aware historical metrics (preventing data leakage) and live match dynamic state features.
Vectorized for high performance.
"""

import pandas as pd
import numpy as np
from collections import defaultdict
from src.config import TOP_VENUES, CANONICAL_TEAMS


def _int_defaultdict():
    return defaultdict(int)


class HistoricalStatsTracker:
    """
    Maintains time-aware running statistics across matches to prevent data leakage.
    Every stat for match i is computed strictly using matches < i.
    """

    def __init__(self):
        self.team_matches = defaultdict(int)
        self.team_wins = defaultdict(int)
        self.team_recent_history = defaultdict(list)
        self.h2h_matches = defaultdict(_int_defaultdict)
        self.h2h_wins = defaultdict(_int_defaultdict)
        self.venue_matches = defaultdict(int)
        self.venue_bat_first_wins = defaultdict(int)
        self.venue_chase_wins = defaultdict(int)
        self.venue_first_inns_scores = defaultdict(list)
        self.team_innings_runs = defaultdict(list)
        self.team_innings_wickets_taken = defaultdict(list)

    def get_features_for_match(self, team1: str, team2: str, venue: str, toss_winner: str, toss_decision: str) -> dict:
        """Extract pre-match features using only historical state known prior to this match."""
        t1_total = self.team_matches[team1]
        t1_win_pct = (self.team_wins[team1] / t1_total) if t1_total > 0 else 0.50
        
        t2_total = self.team_matches[team2]
        t2_win_pct = (self.team_wins[team2] / t2_total) if t2_total > 0 else 0.50

        t1_rec5 = self.team_recent_history[team1][-5:]
        t1_form5 = (sum(t1_rec5) / len(t1_rec5)) if len(t1_rec5) > 0 else 0.50

        t2_rec5 = self.team_recent_history[team2][-5:]
        t2_form5 = (sum(t2_rec5) / len(t2_rec5)) if len(t2_rec5) > 0 else 0.50

        h2h_total = self.h2h_matches[team1][team2]
        t1_h2h_wins = self.h2h_wins[team1][team2]
        t1_h2h_win_pct = (t1_h2h_wins / h2h_total) if h2h_total > 0 else 0.50

        v_total = self.venue_matches[venue]
        v_chase_wins = self.venue_chase_wins[venue]
        venue_chase_win_pct = (v_chase_wins / v_total) if v_total > 0 else 0.50
        
        v_scores = self.venue_first_inns_scores[venue]
        venue_avg_1st_inns = float(np.mean(v_scores)) if len(v_scores) > 0 else 165.0

        t1_runs = self.team_innings_runs[team1]
        t1_bat_avg = float(np.mean(t1_runs[-15:])) if len(t1_runs) > 0 else 160.0

        t2_runs = self.team_innings_runs[team2]
        t2_bat_avg = float(np.mean(t2_runs[-15:])) if len(t2_runs) > 0 else 160.0

        t1_w = self.team_innings_wickets_taken[team1]
        t1_bowl_w = float(np.mean(t1_w[-15:])) if len(t1_w) > 0 else 5.5

        t2_w = self.team_innings_wickets_taken[team2]
        t2_bowl_w = float(np.mean(t2_w[-15:])) if len(t2_w) > 0 else 5.5

        toss_won_by_t1 = 1 if toss_winner == team1 else 0
        toss_is_bat = 1 if str(toss_decision).lower() == "bat" else 0

        return {
            "t1_win_pct": round(t1_win_pct, 4),
            "t2_win_pct": round(t2_win_pct, 4),
            "t1_form5": round(t1_form5, 4),
            "t2_form5": round(t2_form5, 4),
            "t1_h2h_win_pct": round(t1_h2h_win_pct, 4),
            "venue_chase_win_pct": round(venue_chase_win_pct, 4),
            "venue_avg_1st_inns": round(venue_avg_1st_inns, 2),
            "t1_bat_avg": round(t1_bat_avg, 2),
            "t2_bat_avg": round(t2_bat_avg, 2),
            "t1_bowl_w": round(t1_bowl_w, 2),
            "t2_bowl_w": round(t2_bowl_w, 2),
            "toss_won_by_t1": toss_won_by_t1,
            "toss_is_bat": toss_is_bat,
        }

    def update_with_match(self, team1: str, team2: str, venue: str, winner: str, 
                          first_inns_team: str, first_inns_score: int, 
                          t1_wickets_taken: int = 6, t2_wickets_taken: int = 6):
        """Update tracker state with the completed match result."""
        self.team_matches[team1] += 1
        self.team_matches[team2] += 1
        
        t1_won = (winner == team1)
        if t1_won:
            self.team_wins[team1] += 1
            self.team_recent_history[team1].append(1)
            self.team_recent_history[team2].append(0)
            self.h2h_wins[team1][team2] += 1
        else:
            self.team_wins[team2] += 1
            self.team_recent_history[team2].append(1)
            self.team_recent_history[team1].append(0)
            self.h2h_wins[team2][team1] += 1

        self.h2h_matches[team1][team2] += 1
        self.h2h_matches[team2][team1] += 1

        self.venue_matches[venue] += 1
        chasing_team = team2 if first_inns_team == team1 else team1
        if winner == chasing_team:
            self.venue_chase_wins[venue] += 1
        else:
            self.venue_bat_first_wins[venue] += 1

        if first_inns_score > 0:
            self.venue_first_inns_scores[venue].append(first_inns_score)
            self.team_innings_runs[first_inns_team].append(first_inns_score)

        self.team_innings_wickets_taken[team1].append(t1_wickets_taken)
        self.team_innings_wickets_taken[team2].append(t2_wickets_taken)


def build_pre_match_features_dataset(matches_clean: pd.DataFrame, deliveries_clean: pd.DataFrame) -> tuple[pd.DataFrame, HistoricalStatsTracker]:
    """Generates a chronological, time-aware pre-match dataset for winner classification."""
    tracker = HistoricalStatsTracker()
    rows = []

    # Vectorized fast summary of innings 1 scores
    inns1 = deliveries_clean[deliveries_clean["inning"] == 1]
    inns1_score_map = inns1.groupby("match_id")["total_runs"].sum().to_dict()
    inns1_team_map = inns1.groupby("match_id")["batting_team"].first().to_dict()

    # Fast wickets per bowling team
    wickets_series = deliveries_clean.groupby(["match_id", "bowling_team"])["is_wicket"].sum()
    wickets_dict = wickets_series.to_dict()

    for _, match in matches_clean.iterrows():
        m_id = match["id"]
        t1 = match["team1"]
        t2 = match["team2"]
        venue = match["venue"]
        toss_winner = match["toss_winner"]
        toss_decision = match["toss_decision"]
        winner = match["winner"]

        if winner not in [t1, t2]:
            continue

        feats = tracker.get_features_for_match(t1, t2, venue, toss_winner, toss_decision)
        feats["match_id"] = m_id
        feats["season"] = match["season"]
        feats["team1"] = t1
        feats["team2"] = t2
        feats["venue"] = venue
        feats["target"] = 1 if winner == t1 else 0
        rows.append(feats)

        first_inns_team = inns1_team_map.get(m_id, t1)
        first_inns_score = inns1_score_map.get(m_id, 160)
        t1_w = wickets_dict.get((m_id, t1), 5)
        t2_w = wickets_dict.get((m_id, t2), 5)
        tracker.update_with_match(t1, t2, venue, winner, first_inns_team, first_inns_score, t1_w, t2_w)

    features_df = pd.DataFrame(rows)
    return features_df, tracker


def build_live_chase_dataset(matches_clean: pd.DataFrame, deliveries_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorized construction of 2nd innings live chase states per over.
    Runs in sub-second time.
    """
    # 1. First innings total runs + 1 = Target for 2nd innings
    inns1_scores = deliveries_clean[deliveries_clean["inning"] == 1].groupby("match_id")["total_runs"].sum().reset_index()
    inns1_scores.rename(columns={"total_runs": "first_inns_total"}, inplace=True)
    inns1_scores["target"] = inns1_scores["first_inns_total"] + 1

    # Inning 2 deliveries aggregated by match_id and over
    inns2 = deliveries_clean[deliveries_clean["inning"] == 2]
    
    over_agg = inns2.groupby(["match_id", "over"]).agg(
        over_runs=("total_runs", "sum"),
        over_wickets=("is_wicket", "sum"),
        batting_team=("batting_team", "first"),
        bowling_team=("bowling_team", "first")
    ).reset_index()

    # Cumulative calculations within each match
    over_agg["current_score"] = over_agg.groupby("match_id")["over_runs"].cumsum()
    over_agg["wickets"] = over_agg.groupby("match_id")["over_wickets"].cumsum()
    
    # Rolling last 5 overs runs (min_periods=1)
    over_agg["last_5_overs_runs"] = over_agg.groupby("match_id")["over_runs"].transform(
        lambda s: s.rolling(5, min_periods=1).sum()
    )

    # Merge target and match details
    merged = over_agg.merge(inns1_scores[["match_id", "target"]], on="match_id")
    merged = merged.merge(matches_clean[["id", "winner", "venue"]], left_on="match_id", right_on="id")

    # Derived features
    merged["overs"] = merged["over"]
    merged["balls_bowled"] = merged["overs"] * 6
    merged["balls_remaining"] = np.maximum(120 - merged["balls_bowled"], 0)
    merged["wickets_remaining"] = np.maximum(10 - merged["wickets"], 0)
    merged["runs_required"] = np.maximum(merged["target"] - merged["current_score"], 0)

    # Filter out completed innings / edge cases
    valid_mask = (
        (merged["overs"] <= 19) &
        (merged["runs_required"] > 0) &
        (merged["wickets_remaining"] > 0) &
        (merged["target"] >= 60)
    )
    df = merged[valid_mask].copy()

    df["crr"] = np.round(df["current_score"] / df["overs"], 2)
    df["rrr"] = np.round((df["runs_required"] * 6.0) / np.maximum(df["balls_remaining"], 1), 2)
    df["run_rate_diff"] = np.round(df["crr"] - df["rrr"], 2)

    df["pressure_factor"] = np.round(df["rrr"] / (df["wickets_remaining"] + 0.5), 2)
    df["momentum_score"] = np.round(
        (df["last_5_overs_runs"] / 30.0) / np.maximum(df["rrr"] / 6.0, 0.5), 2
    )

    df["is_powerplay"] = (df["overs"] <= 6).astype(int)
    df["is_death"] = (df["overs"] >= 16).astype(int)
    df["won_by_bat"] = (df["winner"] == df["batting_team"]).astype(int)

    feature_cols = [
        "match_id", "batting_team", "bowling_team", "venue", "overs",
        "current_score", "wickets", "wickets_remaining", "runs_required",
        "balls_remaining", "target", "crr", "rrr", "run_rate_diff",
        "last_5_overs_runs", "pressure_factor", "momentum_score",
        "is_powerplay", "is_death", "won_by_bat"
    ]
    return df[feature_cols].reset_index(drop=True)


def build_first_innings_score_dataset(matches_clean: pd.DataFrame, deliveries_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorized construction of 1st innings state per over for Final Score Regression.
    Runs in sub-second time.
    """
    inns1 = deliveries_clean[deliveries_clean["inning"] == 1]
    
    # Match total 1st innings scores
    total_scores = inns1.groupby("match_id")["total_runs"].sum().reset_index()
    total_scores.rename(columns={"total_runs": "final_score"}, inplace=True)

    # Over aggregates
    over_agg = inns1.groupby(["match_id", "over"]).agg(
        over_runs=("total_runs", "sum"),
        over_wickets=("is_wicket", "sum"),
        batting_team=("batting_team", "first"),
        bowling_team=("bowling_team", "first")
    ).reset_index()

    over_agg["current_score"] = over_agg.groupby("match_id")["over_runs"].cumsum()
    over_agg["wickets"] = over_agg.groupby("match_id")["over_wickets"].cumsum()
    over_agg["last_5_overs_runs"] = over_agg.groupby("match_id")["over_runs"].transform(
        lambda s: s.rolling(5, min_periods=1).sum()
    )

    merged = over_agg.merge(total_scores, on="match_id")
    merged = merged.merge(matches_clean[["id", "venue"]], left_on="match_id", right_on="id")

    merged["overs"] = merged["over"]
    merged["crr"] = np.round(merged["current_score"] / merged["overs"], 2)
    merged["balls_remaining"] = 120 - (merged["overs"] * 6)
    merged["is_powerplay"] = (merged["overs"] <= 6).astype(int)
    merged["is_middle"] = ((merged["overs"] > 6) & (merged["overs"] <= 15)).astype(int)
    merged["is_death"] = (merged["overs"] > 15).astype(int)

    # Keep realistic in-play state from over 4 to 18 where innings didn't collapse early
    valid_mask = (
        (merged["overs"] >= 4) &
        (merged["overs"] <= 18) &
        (merged["wickets"] < 10) &
        (merged["final_score"] >= 80)
    )
    df = merged[valid_mask].copy()

    feature_cols = [
        "match_id", "batting_team", "bowling_team", "venue", "overs",
        "current_score", "wickets", "crr", "balls_remaining",
        "last_5_overs_runs", "is_powerplay", "is_middle", "is_death", "final_score"
    ]
    return df[feature_cols].reset_index(drop=True)


if __name__ == "__main__":
    from src.data_loader import load_raw_data
    from src.preprocessing import get_cleaned_data
    
    m_raw, d_raw = load_raw_data()
    m_clean, d_clean = get_cleaned_data(m_raw, d_raw)
    
    pm_df, tracker = build_pre_match_features_dataset(m_clean, d_clean)
    print("Pre-match dataset:", pm_df.shape)
    
    chase_df = build_live_chase_dataset(m_clean, d_clean)
    print("Live chase dataset:", chase_df.shape)
    
    score_df = build_first_innings_score_dataset(m_clean, d_clean)
    print("Score regressor dataset:", score_df.shape)
