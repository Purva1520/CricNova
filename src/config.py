"""
CricNova Central Configuration
Defines paths, team mappings, venue standardizations, and UI tokens.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
DB_PATH = BASE_DIR / "cricket_nova.db"

# Remote Dataset URLs (Official Verified Kaggle IPL Dataset Mirrors)
MATCHES_URL = "https://raw.githubusercontent.com/krish-italiya/IPL-Data-Analysis/main/matches.csv"
DELIVERIES_URL = "https://raw.githubusercontent.com/krish-italiya/IPL-Data-Analysis/main/deliveries.csv"

# Active & Canonical IPL Teams
CANONICAL_TEAMS = [
    "Chennai Super Kings",
    "Delhi Capitals",
    "Gujarat Titans",
    "Kolkata Knight Riders",
    "Lucknow Super Giants",
    "Mumbai Indians",
    "Punjab Kings",
    "Rajasthan Royals",
    "Royal Challengers Bangalore",
    "Sunrisers Hyderabad"
]

# Team Aliases Mapping (Historical names -> Canonical names)
TEAM_ALIASES = {
    "Delhi Daredevils": "Delhi Capitals",
    "Delhi Capitals": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Punjab Kings": "Punjab Kings",
    "Rising Pune Supergiant": "Rising Pune Supergiants",
    "Rising Pune Supergiants": "Rising Pune Supergiants",
    "Deccan Chargers": "Sunrisers Hyderabad",
    "Sunrisers Hyderabad": "Sunrisers Hyderabad",
    "Royal Challengers Bangalore": "Royal Challengers Bangalore",
    "Royal Challengers Bengaluru": "Royal Challengers Bangalore",
    "Mumbai Indians": "Mumbai Indians",
    "Chennai Super Kings": "Chennai Super Kings",
    "Kolkata Knight Riders": "Kolkata Knight Riders",
    "Rajasthan Royals": "Rajasthan Royals",
    "Gujarat Lions": "Gujarat Titans",
    "Gujarat Titans": "Gujarat Titans",
    "GL": "Gujarat Titans",
    "GT": "Gujarat Titans",
    "CSK": "Chennai Super Kings",
    "MI": "Mumbai Indians",
    "RCB": "Royal Challengers Bangalore",
    "KKR": "Kolkata Knight Riders",
    "DC": "Delhi Capitals",
    "PBKS": "Punjab Kings",
    "KXIP": "Punjab Kings",
    "RR": "Rajasthan Royals",
    "SRH": "Sunrisers Hyderabad",
    "LSG": "Lucknow Super Giants",
    "Lucknow Super Giants": "Lucknow Super Giants",
    "Pune Warriors": "Pune Warriors",
    "Kochi Tuskers Kerala": "Kochi Tuskers Kerala"
}

# Team Short Names & Colors
TEAM_METADATA = {
    "Chennai Super Kings": {"short": "CSK", "primary_color": "#F9CD05", "secondary_color": "#0081E9"},
    "Delhi Capitals": {"short": "DC", "primary_color": "#004C93", "secondary_color": "#D71920"},
    "Gujarat Titans": {"short": "GT", "primary_color": "#1B2133", "secondary_color": "#C59B27"},
    "Kolkata Knight Riders": {"short": "KKR", "primary_color": "#3A225D", "secondary_color": "#D1AB3E"},
    "Lucknow Super Giants": {"short": "LSG", "primary_color": "#A7D5F2", "secondary_color": "#E32636"},
    "Mumbai Indians": {"short": "MI", "primary_color": "#004BA0", "secondary_color": "#D1AB3E"},
    "Punjab Kings": {"short": "PBKS", "primary_color": "#DD1F2D", "secondary_color": "#DCDDDF"},
    "Rajasthan Royals": {"short": "RR", "primary_color": "#EA1A85", "secondary_color": "#254AA5"},
    "Royal Challengers Bangalore": {"short": "RCB", "primary_color": "#EC1C24", "secondary_color": "#2B2A29"},
    "Sunrisers Hyderabad": {"short": "SRH", "primary_color": "#F26522", "secondary_color": "#000000"}
}

# Top Venues
TOP_VENUES = [
    "Wankhede Stadium",
    "M Chinnaswamy Stadium",
    "Eden Gardens",
    "Feroz Shah Kotla",
    "MA Chidambaram Stadium, Chepauk",
    "Rajiv Gandhi International Stadium, Uppal",
    "Punjab Cricket Association Stadium, Mohali",
    "Sawai Mansingh Stadium",
    "Dubai International Cricket Stadium",
    "Sharjah Cricket Stadium",
    "Sheikh Zayed Stadium",
    "Narendra Modi Stadium, Ahmedabad"
]

# Dark Stadium UI Color Palette Tokens
UI_THEME = {
    "bg_main": "#0b0f19",
    "bg_card": "#131b2e",
    "bg_card_hover": "#1a253e",
    "border": "#212e4d",
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",
    "accent_cyan": "#00f2fe",
    "accent_blue": "#3b82f6",
    "accent_green": "#10b981",
    "accent_amber": "#f59e0b",
    "accent_rose": "#f43f5e",
    "gradient_hero": "linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0284c7 100%)",
}
