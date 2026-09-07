"""
Data loader module for CricNova.
Handles downloading and local caching of raw IPL datasets.
"""

import os
from pathlib import Path
import pandas as pd
import requests
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, MATCHES_URL, DELIVERIES_URL


def ensure_data_dirs():
    """Ensure data/raw and data/processed directories exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest_path: Path, chunk_size: int = 1024 * 1024):
    """Download a file with streaming chunks and verify completion."""
    print(f"Downloading {url} to {dest_path}...")
    headers = {"User-Agent": "Mozilla/5.0 (CricNova AIML Project)"}
    resp = requests.get(url, headers=headers, stream=True, timeout=30)
    resp.raise_for_status()

    temp_path = dest_path.with_suffix(".tmp")
    with open(temp_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)

    if temp_path.exists():
        temp_path.replace(dest_path)
    print(f"Successfully downloaded {dest_path.name} ({dest_path.stat().st_size / (1024*1024):.2f} MB)")


def load_raw_data(force_download: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads matches.csv and deliveries.csv from data/raw.
    Downloads them if missing or if force_download=True.
    
    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (matches_df, deliveries_df)
    """
    ensure_data_dirs()

    matches_path = RAW_DATA_DIR / "matches.csv"
    deliveries_path = RAW_DATA_DIR / "deliveries.csv"

    if force_download or not matches_path.exists() or matches_path.stat().st_size == 0:
        download_file(MATCHES_URL, matches_path)

    if force_download or not deliveries_path.exists() or deliveries_path.stat().st_size == 0:
        download_file(DELIVERIES_URL, deliveries_path)

    matches_df = pd.read_csv(matches_path)
    deliveries_df = pd.read_csv(deliveries_path)

    return matches_df, deliveries_df


if __name__ == "__main__":
    m, d = load_raw_data()
    print(f"Matches loaded: {m.shape}")
    print(f"Deliveries loaded: {d.shape}")
