"""
Dark Stadium UI Components & Design System for CricNova.
Injects custom CSS, glassmorphic cards, team-branded badges, and Plotly dark theme templates.
"""

import streamlit as st
import plotly.graph_objects as go
from src.config import TEAM_METADATA, UI_THEME


def inject_custom_css():
    """Injects high-end dark stadium aesthetics, Google Fonts, and animations."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Main background & subtle stadium floodlight gradient */
        .stApp {
            background-color: #0b0f19;
            background-image: 
                radial-gradient(at 0% 0%, rgba(0, 242, 254, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.08) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(15, 23, 42, 0.5) 0px, transparent 100%);
            background-attachment: fixed;
            color: #f8fafc;
        }

        /* Top Header & Navbar styling */
        header[data-testid="stHeader"] {
            background: rgba(11, 15, 25, 0.8) !important;
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(33, 46, 77, 0.6);
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0d1322 !important;
            border-right: 1px solid #1e293b !important;
        }

        section[data-testid="stSidebar"] .stMarkdown h1, 
        section[data-testid="stSidebar"] .stMarkdown h2,
        section[data-testid="stSidebar"] .stMarkdown h3 {
            color: #f8fafc !important;
        }

        /* Glassmorphic Stadium Cards */
        .stadium-card {
            background: linear-gradient(135deg, rgba(19, 27, 46, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
            border: 1px solid #212e4d;
            border-radius: 14px;
            padding: 22px 26px;
            margin-bottom: 20px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(8px);
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .stadium-card:hover {
            border-color: #38bdf8;
            box-shadow: 0 14px 30px -4px rgba(0, 242, 254, 0.15);
            transform: translateY(-2px);
        }

        /* Neon Accent Highlights */
        .neon-cyan {
            color: #00f2fe;
            text-shadow: 0 0 12px rgba(0, 242, 254, 0.4);
        }
        .neon-green {
            color: #10b981;
            text-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
        }
        .neon-amber {
            color: #f59e0b;
            text-shadow: 0 0 12px rgba(245, 158, 11, 0.4);
        }

        /* Metric Pill Box */
        .metric-pill {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 600;
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.2);
            color: #38bdf8;
            margin-right: 8px;
            margin-bottom: 6px;
        }

        /* Custom Streamlit Buttons */
        div.stButton > button {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            border: 1px solid #38bdf8 !important;
            border-radius: 10px !important;
            padding: 10px 24px !important;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4) !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            letter-spacing: 0.02em;
        }
        div.stButton > button:hover {
            background: linear-gradient(135deg, #00f2fe 0%, #0284c7 100%) !important;
            color: #0b0f19 !important;
            box-shadow: 0 6px 20px rgba(0, 242, 254, 0.6) !important;
            transform: translateY(-2px) !important;
        }

        /* Form Inputs & Selectboxes */
        div[data-baseweb="select"] > div {
            background-color: #131b2e !important;
            border: 1px solid #212e4d !important;
            border-radius: 10px !important;
            color: #f8fafc !important;
        }
        div[data-baseweb="select"] > div:hover {
            border-color: #38bdf8 !important;
        }
        div[data-baseweb="input"] > div {
            background-color: #131b2e !important;
            border: 1px solid #212e4d !important;
            border-radius: 10px !important;
            color: #f8fafc !important;
        }
        div[data-baseweb="input"] > div:focus-within {
            border-color: #00f2fe !important;
            box-shadow: 0 0 0 1px #00f2fe !important;
        }

        /* Tab Active States */
        div[data-baseweb="tab-list"] {
            background: rgba(15, 23, 42, 0.6) !important;
            border-radius: 12px !important;
            padding: 4px !important;
            border: 1px solid #1e293b !important;
        }
        button[data-baseweb="tab"] {
            border-radius: 8px !important;
            color: #94a3b8 !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(2, 132, 199, 0.8) 0%, rgba(3, 105, 161, 0.9) 100%) !important;
            color: #ffffff !important;
            border: 1px solid #38bdf8 !important;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
        }

        /* Explanatory Callout Box */
        .xai-callout {
            background: rgba(15, 23, 42, 0.85);
            border-left: 4px solid #00f2fe;
            border-radius: 0 10px 10px 0;
            padding: 16px 20px;
            margin: 12px 0;
            border-top: 1px solid rgba(33, 46, 77, 0.4);
            border-right: 1px solid rgba(33, 46, 77, 0.4);
            border-bottom: 1px solid rgba(33, 46, 77, 0.4);
        }

        /* Code & Monospace numbers */
        .mono-stat {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
        }
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_header(title: str, subtitle: str = "", badge: str = "IPL AI INTELLIGENCE"):
    """Renders a premier dark stadium hero header with glowing typography."""
    st.markdown(
        f"""
        <div style="margin-bottom: 24px; padding-top: 10px;">
            <div class="metric-pill" style="border-color: #00f2fe; color: #00f2fe; background: rgba(0, 242, 254, 0.1);">
                ⚡ {badge}
            </div>
            <h1 style="font-size: 2.6rem; font-weight: 800; margin: 8px 0 6px 0; letter-spacing: -0.03em;
                       background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #38bdf8 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {title}
            </h1>
            <p style="color: #94a3b8; font-size: 1.05rem; margin: 0; line-height: 1.5;">
                {subtitle}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_stat_box(title: str, value: str, sub: str = "", icon: str = "🏏", color: str = "#00f2fe"):
    """Renders a standalone glowing KPI stat box."""
    st.markdown(
        f"""
        <div class="stadium-card" style="border-top: 3px solid {color}; padding: 18px 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: #94a3b8; font-size: 0.88rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                    {title}
                </span>
                <span style="font-size: 1.3rem;">{icon}</span>
            </div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #f8fafc; font-family: 'JetBrains Mono', monospace; line-height: 1.1;">
                {value}
            </div>
            {f'<div style="color: #64748b; font-size: 0.82rem; margin-top: 6px;">{sub}</div>' if sub else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_team_badge_html(team_name: str) -> str:
    """Returns HTML chip for a team with its official brand color."""
    meta = TEAM_METADATA.get(team_name, {"short": team_name[:3].upper(), "primary_color": "#38bdf8"})
    color = meta["primary_color"]
    short = meta["short"]
    return f"""
    <span style="display: inline-flex; align-items: center; background: rgba(30, 41, 59, 0.9);
                 border: 1px solid {color}; border-radius: 8px; padding: 3px 10px; font-weight: 700; font-size: 0.88rem; color: #f8fafc;">
        <span style="width: 10px; height: 10px; border-radius: 50%; background-color: {color}; margin-right: 8px; box-shadow: 0 0 6px {color};"></span>
        {team_name} <span style="color: {color}; margin-left: 6px; font-size: 0.78rem;">({short})</span>
    </span>
    """


def render_provenance_badge(kind: str = "HISTORICAL"):
    """
    Renders clear, bold, high-contrast provenance badges distinguishing
    actual historical statistics from AI/ML predictions.
    """
    kind_upper = kind.upper()
    if "HIST" in kind_upper:
        st.markdown(
            """
            <div style="display: inline-flex; align-items: center; background: rgba(16, 185, 129, 0.12); border: 1px solid #10b981; border-radius: 9999px; padding: 4px 14px; font-size: 0.8rem; font-weight: 700; color: #34d399; margin-bottom: 12px; letter-spacing: 0.04em;">
                <span style="margin-right: 6px;">🏛️</span> ACTUAL HISTORICAL DATA (OFFICIAL IPL ARCHIVE 2008–2019)
            </div>
            """,
            unsafe_allow_html=True
        )
    elif "PRED" in kind_upper:
        st.markdown(
            """
            <div style="display: inline-flex; align-items: center; background: rgba(168, 85, 247, 0.12); border: 1px solid #a855f7; border-radius: 9999px; padding: 4px 14px; font-size: 0.8rem; font-weight: 700; color: #c084fc; margin-bottom: 12px; letter-spacing: 0.04em;">
                <span style="margin-right: 6px;">🔮</span> AI/ML PREDICTION & INFERENCE (PROBABILISTIC MODEL)
            </div>
            """,
            unsafe_allow_html=True
        )
    elif "XAI" in kind_upper or "FACTOR" in kind_upper:
        st.markdown(
            """
            <div style="display: inline-flex; align-items: center; background: rgba(0, 242, 254, 0.12); border: 1px solid #00f2fe; border-radius: 9999px; padding: 4px 14px; font-size: 0.8rem; font-weight: 700; color: #38bdf8; margin-bottom: 12px; letter-spacing: 0.04em;">
                <span style="margin-right: 6px;">🧠</span> EXPLAINABLE AI FACTOR ATTRIBUTION (ML FEATURE IMPACT)
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="display: inline-flex; align-items: center; background: rgba(59, 130, 246, 0.12); border: 1px solid #3b82f6; border-radius: 9999px; padding: 4px 14px; font-size: 0.8rem; font-weight: 700; color: #60a5fa; margin-bottom: 12px; letter-spacing: 0.04em;">
                <span style="margin-right: 6px;">📊</span> DERIVED STATISTICAL AGGREGATION
            </div>
            """,
            unsafe_allow_html=True
        )


def get_plotly_dark_layout(title: str = "", height: int = 380) -> dict:
    """Standardizes Plotly chart themes for seamless dark stadium integration."""
    return dict(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(family="Outfit, sans-serif", size=16, color="#f8fafc"),
            x=0.02,
            y=0.96
        ),
        paper_bgcolor="rgba(19, 27, 46, 0.0)",
        plot_bgcolor="rgba(15, 23, 42, 0.4)",
        font=dict(family="Outfit, sans-serif", color="#94a3b8"),
        height=height,
        margin=dict(l=40, r=30, t=50, b=40),
        xaxis=dict(
            gridcolor="#1e293b",
            zerolinecolor="#334155",
            tickfont=dict(color="#94a3b8", size=11)
        ),
        yaxis=dict(
            gridcolor="#1e293b",
            zerolinecolor="#334155",
            tickfont=dict(color="#94a3b8", size=11)
        ),
        legend=dict(
            bgcolor="rgba(19, 27, 46, 0.6)",
            bordercolor="#212e4d",
            borderwidth=1,
            font=dict(color="#f8fafc", size=11)
        )
    )
