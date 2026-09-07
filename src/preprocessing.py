"""
Data Preprocessing Pipeline for CricNova.
Standardizes team names, venues, dates, and computes basic cumulative match states.
"""

import pandas as pd
import numpy as np
from src.config import TEAM_ALIASES, CANONICAL_TEAMS


def clean_team_name(name: str) -> str:
    """Normalize team name using alias mapping (handles exact match and case-insensitivity)."""
    if not isinstance(name, str):
        return name
    name = name.strip()
    if name in TEAM_ALIASES:
        return TEAM_ALIASES[name]
    
    # Case-insensitive fallback
    name_lower = name.lower()
    for alias, canonical in TEAM_ALIASES.items():
        if alias.lower() == name_lower:
            return canonical
    return name


def clean_venue_name(venue: str) -> str:
    """Standardize venue naming variations."""
    if not isinstance(venue, str):
        return venue
    venue = venue.strip()
    if "Chinnaswamy" in venue:
        return "M Chinnaswamy Stadium"
    if "Wankhede" in venue:
        return "Wankhede Stadium"
    if "Eden Gardens" in venue:
        return "Eden Gardens"
    if "Feroz Shah Kotla" in venue or "Arun Jaitley" in venue:
        return "Feroz Shah Kotla"
    if "MA Chidambaram" in venue or "Chepauk" in venue:
        return "MA Chidambaram Stadium, Chepauk"
    if "Rajiv Gandhi" in venue:
        return "Rajiv Gandhi International Stadium, Uppal"
    if "Punjab Cricket Association" in venue or "Mohali" in venue:
        return "Punjab Cricket Association Stadium, Mohali"
    if "Sawai Mansingh" in venue:
        return "Sawai Mansingh Stadium"
    if "Dubai" in venue:
        return "Dubai International Cricket Stadium"
    if "Sharjah" in venue:
        return "Sharjah Cricket Stadium"
    if "Sheikh Zayed" in venue or "Abu Dhabi" in venue:
        return "Sheikh Zayed Stadium"
    if "Narendra Modi" in venue or "Motera" in venue or "Sardar Patel" in venue:
        return "Narendra Modi Stadium, Ahmedabad"
    return venue


def preprocess_matches(matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans matches dataset:
    - Normalizes team1, team2, toss_winner, winner
    - Standardizes venue and city
    - Parses dates and sorts chronologically
    - Filters out matches without winners (abandoned/no result)
    """
    df = matches_df.copy()
    
    # Standardize teams
    for col in ["team1", "team2", "toss_winner", "winner"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_team_name)

    # Standardize venues
    df["venue"] = df["venue"].apply(clean_venue_name)
    
    # Fill missing cities using venue heuristic
    venue_city_map = {
        "M Chinnaswamy Stadium": "Bengaluru",
        "Wankhede Stadium": "Mumbai",
        "Eden Gardens": "Kolkata",
        "Feroz Shah Kotla": "Delhi",
        "MA Chidambaram Stadium, Chepauk": "Chennai",
        "Rajiv Gandhi International Stadium, Uppal": "Hyderabad",
        "Punjab Cricket Association Stadium, Mohali": "Chandigarh",
        "Sawai Mansingh Stadium": "Jaipur",
        "Dubai International Cricket Stadium": "Dubai",
        "Sharjah Cricket Stadium": "Sharjah",
        "Sheikh Zayed Stadium": "Abu Dhabi"
    }
    for v, c in venue_city_map.items():
        mask = df["venue"] == v
        df.loc[mask & df["city"].isnull(), "city"] = c

    # Filter matches with a defined winner
    df = df[df["winner"].notnull()].copy()

    # Parse and sort chronologically
    df["date"] = pd.to_datetime(df["date"], format="mixed")
    df = df.sort_values(by=["date", "id"]).reset_index(drop=True)
    
    return df


def preprocess_deliveries(deliveries_df: pd.DataFrame, matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans deliveries dataset and merges match-level metadata:
    - Standardizes batting_team and bowling_team
    - Calculates total runs per ball (batsman + extra)
    - Flags wickets (dismissals that credit a wicket to bowler or run-outs)
    - Keeps innings 1 and 2
    """
    df = deliveries_df.copy()

    # Filter to innings 1 and 2
    df = df[df["inning"].isin([1, 2])].copy()

    # Clean team names
    df["batting_team"] = df["batting_team"].apply(clean_team_name)
    df["bowling_team"] = df["bowling_team"].apply(clean_team_name)

    # Ensure integer runs
    df["total_runs"] = df["total_runs"].fillna(0).astype(int)
    
    # Dismissal indicator
    df["is_wicket"] = df["player_dismissed"].notnull().astype(int)

    # Compute ball counter within over and legal delivery tracking
    # Extra runs like wides and noballs don't advance the legal ball count
    df["is_legal_ball"] = (~df["wide_runs"].fillna(0).astype(bool) & ~df["noball_runs"].fillna(0).astype(bool)).astype(int)

    return df


def get_cleaned_data(matches_raw: pd.DataFrame, deliveries_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convenience pipeline returning cleaned matches and deliveries."""
    matches_clean = preprocess_matches(matches_raw)
    valid_match_ids = set(matches_clean["id"])
    
    deliveries_filtered = deliveries_raw[deliveries_raw["match_id"].isin(valid_match_ids)].copy()
    deliveries_clean = preprocess_deliveries(deliveries_filtered, matches_clean)
    
    return matches_clean, deliveries_clean


if __name__ == "__main__":
    from src.data_loader import load_raw_data
    m_raw, d_raw = load_raw_data()
    m_clean, d_clean = get_cleaned_data(m_raw, d_raw)
    print(f"Preprocessed matches: {m_clean.shape}, seasons: {sorted(m_clean['season'].unique())}")
    print(f"Preprocessed deliveries: {d_clean.shape}, unique matches: {d_clean['match_id'].nunique()}")
