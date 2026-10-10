"""EV Charging Analytics | Research Archive & Engineering Intelligence.

An editorial, research-grade presentation layer for empirical EV charging behavior,
hourly time-series demand forecasting, and unsupervised anomaly detection.

Design Reference: Editorial Research-Publication Architecture (Beyond AUROC).
Project Timeline: 2024–2026 Horizon.
Dataset Observation Period: January 2020 – September 2021 (Caltech ACN-Data Garage Site 0002, Cluster 0039).
Canonical Dataset Properties: Exactly 5,000 sessions, 14,422 continuous hours, 53,668.78 kWh total energy.
Timezone: America/Los_Angeles (PST/PDT).
"""

from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# -----------------------------------------------------------------------------
# APPLICATION CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="EV Charging Analytics — Research Archive",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# EDITORIAL DARK RESEARCH DESIGN SYSTEM (CSS)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');

    :root {
        --canvas-bg: #0b0f19;
        --surface-base: #111827;
        --surface-elevated: #162032;
        --surface-muted: #1a263c;
        --line-subtle: #1e293b;
        --line-light: #283953;
        --blue-primary: #3b82f6;
        --blue-muted: #2563eb;
        --teal-accent: #14b8a6;
        --teal-muted: #0d9488;
        --amber-accent: #d97706;
        --text-headline: #f1f5f9;
        --text-body: #94a3b8;
        --text-muted: #64748b;
    }

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: var(--text-body);
        background-color: var(--canvas-bg);
        line-height: 1.6;
    }

    .stApp {
        background-color: var(--canvas-bg);
    }

    /* Reset Header & Footer */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    footer {
        visibility: hidden;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3.5rem;
        max-width: 1450px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0c101a !important;
        border-right: 1px solid var(--line-subtle);
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
        padding-left: 1.25rem;
        padding-right: 1.25rem;
    }

    /* Sidebar Typography */
    .sb-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 1.2rem;
        border-bottom: 1px solid var(--line-subtle);
        margin-bottom: 1.5rem;
    }
    .sb-brand-icon {
        width: 38px;
        height: 38px;
        border: 1px solid var(--blue-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Libre Baskerville', Georgia, serif;
        font-size: 19px;
        font-weight: 700;
        color: var(--blue-primary);
        background: #111a2e;
    }
    .sb-brand-text {
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 1.5px;
        line-height: 1.2;
        color: var(--text-headline);
        text-transform: uppercase;
    }
    .sb-brand-text small {
        display: block;
        font-weight: 500;
        font-size: 9px;
        letter-spacing: 2px;
        color: var(--text-muted);
        margin-top: 4px;
    }

    .sb-section-hdr {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.4px;
        color: var(--text-muted);
        text-transform: uppercase;
        margin: 1.4rem 0 0.5rem 0;
    }

    /* Selectbox Overrides for Dark UI */
    .stSelectbox label {
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: 0.8px !important;
        color: var(--text-muted) !important;
        text-transform: uppercase !important;
    }
    .stSelectbox div[data-baseweb="select"] {
        background-color: var(--surface-base) !important;
        border-color: var(--line-subtle) !important;
        border-radius: 2px !important;
        color: var(--text-headline) !important;
    }
    .stSelectbox div[data-baseweb="select"] * {
        color: var(--text-headline) !important;
    }

    /* Sidebar Dataset Metadata Card */
    .sb-dataset-card {
        background-color: var(--surface-base);
        border: 1px solid var(--line-subtle);
        border-top: 2px solid var(--blue-primary);
        padding: 16px 14px;
        margin-top: 1.8rem;
    }
    .sb-dataset-card .tag {
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1.2px;
        color: var(--blue-primary);
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .sb-dataset-card .title {
        font-family: 'Libre Baskerville', Georgia, serif;
        font-size: 15px;
        color: var(--text-headline);
        margin-bottom: 8px;
    }
    .sb-dataset-card dl {
        margin: 0;
        font-size: 11px;
    }
    .sb-dataset-card dt {
        color: var(--text-muted);
        margin-top: 6px;
    }
    .sb-dataset-card dd {
        margin-left: 0;
        font-weight: 600;
        color: var(--text-headline);
        font-variant-numeric: tabular-nums;
    }

    /* Editorial Site Header */
    .site-header {
        border-bottom: 1px solid var(--line-subtle);
        padding-bottom: 18px;
        margin-bottom: 22px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .site-brand {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .site-brand-icon {
        width: 42px;
        height: 42px;
        border: 1px solid var(--blue-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Libre Baskerville', Georgia, serif;
        font-size: 20px;
        font-weight: 700;
        color: var(--blue-primary);
        background: #111a2e;
    }
    .site-brand-title {
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1.8px;
        line-height: 1.2;
        color: var(--text-headline);
    }
    .site-brand-title small {
        display: block;
        font-size: 10px;
        font-weight: 500;
        letter-spacing: 2.2px;
        color: var(--text-muted);
        margin-top: 4px;
    }
    .site-header-meta {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .site-meta-pill {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        color: var(--blue-primary);
        background: #132038;
        border: 1px solid #1f365d;
        padding: 6px 12px;
        text-transform: uppercase;
    }
    .site-meta-date {
        font-size: 12px;
        color: var(--text-muted);
        font-variant-numeric: tabular-nums;
    }

    /* Horizontal Research Navigation Styling */
    div[data-testid="stRadio"] {
        background-color: transparent;
        margin-bottom: 28px;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 18px;
        align-items: center;
        border-bottom: 1px solid var(--line-subtle);
        padding-bottom: 12px;
    }
    div[data-testid="stRadio"] label {
        background: transparent !important;
        border: none !important;
        padding: 6px 12px !important;
        cursor: pointer !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        color: var(--text-body) !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        transition: color 0.15s, border-color 0.15s !important;
    }
    div[data-testid="stRadio"] label:hover {
        color: var(--text-headline) !important;
    }
    div[data-testid="stRadio"] label > div:first-child {
        display: none !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"],
    div[data-testid="stRadio"] label:has(input:checked) {
        color: var(--blue-primary) !important;
        border-bottom: 2px solid var(--blue-primary) !important;
        font-weight: 700 !important;
    }

    /* Editorial Paper Hero (Overview) */
    .paper-hero {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 380px;
        gap: 48px;
        padding: 36px 0 42px 0;
        border-bottom: 1px solid var(--line-subtle);
        margin-bottom: 38px;
    }
    .eyebrow {
        font-size: 11px;
        letter-spacing: 1.4px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 16px;
        color: var(--text-muted);
        text-transform: uppercase;
    }
    .category-tag {
        color: var(--blue-primary);
        background: #132038;
        padding: 5px 9px;
        font-size: 10px;
        letter-spacing: 1.1px;
        border: 1px solid #1f365d;
    }
    h1.hero-title {
        font-family: 'Libre Baskerville', Georgia, serif;
        font-size: 42px;
        line-height: 1.18;
        letter-spacing: -1.2px;
        font-weight: 400;
        margin: 20px 0 14px;
        color: var(--blue-primary);
    }
    h1.hero-title span {
        display: block;
        font-size: 26px;
        line-height: 1.35;
        letter-spacing: -0.5px;
        color: var(--text-headline);
        margin-top: 10px;
    }
    .hero-subtitle {
        font-family: Georgia, serif;
        font-style: italic;
        font-size: 17px;
        color: var(--text-body);
        margin: 0 0 22px;
        line-height: 1.5;
    }
    .authors-block {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 20px;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-headline);
        margin-bottom: 24px;
    }
    .authors-block span {
        border-bottom: 1px solid var(--line-light);
        padding-bottom: 2px;
    }
    .paper-meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 18px;
    }
    .paper-meta-row strong {
        color: var(--text-headline);
        font-variant-numeric: tabular-nums;
    }

    /* Hero Aside Box */
    .hero-aside {
        background: var(--surface-base);
        border: 1px solid var(--line-subtle);
        border-top: 3px solid var(--blue-primary);
        padding: 24px 24px 20px;
    }
    .aside-top {
        display: flex;
        justify-content: space-between;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.3px;
        color: var(--blue-primary);
        text-transform: uppercase;
    }
    .aside-top .index {
        color: var(--text-muted);
    }
    .hero-aside h2 {
        font-family: 'Libre Baskerville', Georgia, serif;
        font-size: 22px;
        font-weight: 400;
        line-height: 1.3;
        margin: 18px 0 10px;
        color: var(--text-headline);
    }
    .hero-aside p {
        font-size: 13px;
        color: var(--text-body);
        line-height: 1.6;
    }
    .aside-foot {
        font-size: 11px;
        line-height: 1.6;
        border-top: 1px solid var(--line-subtle);
        padding-top: 14px;
        margin-top: 18px;
        color: var(--text-muted);
    }

    /* Status Banner */
    .status-banner {
        background: #141b2a;
        border-left: 3px solid var(--amber-accent);
        border: 1px solid var(--line-subtle);
        border-left-width: 3px;
        border-left-color: var(--amber-accent);
        padding: 14px 20px;
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 34px;
    }
    .status-label {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.2px;
        white-space: nowrap;
        color: #f59e0b;
        text-transform: uppercase;
    }
    .status-banner p {
        font-size: 13px;
        line-height: 1.5;
        margin: 0;
        color: var(--text-body);
    }

    /* Section Number & Header */
    .section-head {
        display: flex;
        align-items: center;
        gap: 14px;
        margin: 38px 0 18px 0;
    }
    .section-number {
        font-size: 12px;
        color: var(--blue-primary);
        font-weight: 700;
        border: 1px solid var(--line-subtle);
        background: #111a2e;
        width: 32px;
        height: 32px;
        display: grid;
        place-items: center;
        flex-shrink: 0;
        font-variant-numeric: tabular-nums;
    }
    .section-head h2 {
        font-family: 'Libre Baskerville', Georgia, serif;
        font-weight: 400;
        font-size: 26px;
        line-height: 1.25;
        margin: 0;
        color: var(--text-headline);
        flex: 1;
    }
    .section-note {
        font-size: 10px;
        letter-spacing: 1.3px;
        color: var(--text-muted);
        text-align: right;
        text-transform: uppercase;
    }

    p.lead {
        font-family: Georgia, serif;
        font-size: 19px;
        line-height: 1.6;
        color: #cbd5e1;
        margin-bottom: 22px;
    }

    /* 4-Box Research Questions Grid */
    .questions-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 30px;
    }
    .question-card {
        padding: 20px;
        border: 1px solid var(--line-subtle);
        background: var(--surface-base);
    }
    .question-card > span {
        font-size: 10px;
        letter-spacing: 1.4px;
        color: var(--blue-primary);
        font-weight: 700;
        text-transform: uppercase;
    }
    .question-card h3 {
        font-size: 15px;
        font-weight: 600;
        margin: 8px 0 6px 0;
        color: var(--text-headline);
    }
    .question-card p {
        font-size: 13px;
        margin: 0;
        color: var(--text-body);
        line-height: 1.5;
    }

    /* Cohort Flow List */
    .cohort-flow {
        list-style: none;
        padding: 0;
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0;
        border: 1px solid var(--line-subtle);
        margin: 22px 0 28px 0;
    }
    .cohort-flow li {
        padding: 22px;
        border-right: 1px solid var(--line-subtle);
        background: var(--surface-base);
    }
    .cohort-flow li:last-child {
        border-right: 0;
        background: var(--surface-elevated);
    }
    .cohort-flow span {
        display: block;
        font-size: 11px;
        font-weight: 700;
        color: var(--text-muted);
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .cohort-flow strong {
        display: block;
        font-family: 'Libre Baskerville', Georgia, serif;
        font-size: 22px;
        font-weight: 400;
        color: var(--blue-primary);
        margin: 10px 0 6px 0;
        font-variant-numeric: tabular-nums;
    }
    .cohort-flow p {
        font-size: 13px;
        margin: 0;
        color: var(--text-body);
        line-height: 1.5;
    }

    /* Statistical Indicator Strip (Varied Editorial) */
    .editorial-stat-bar {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        border: 1px solid var(--line-subtle);
        background: var(--surface-base);
        margin: 24px 0 30px 0;
    }
    .editorial-stat-bar > div {
        padding: 20px 18px;
        border-right: 1px solid var(--line-subtle);
    }
    .editorial-stat-bar > div:last-child {
        border-right: 0;
    }
    .editorial-stat-bar strong {
        font-family: 'Libre Baskerville', Georgia, serif;
        font-weight: 400;
        font-size: 26px;
        display: block;
        color: var(--blue-primary);
        line-height: 1.2;
        font-variant-numeric: tabular-nums;
    }
    .editorial-stat-bar span {
        font-size: 11px;
        color: var(--text-muted);
        display: block;
        margin-top: 6px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        line-height: 1.4;
    }

    /* Analytical Figure Presentation Box */
    .figure-frame {
        background: var(--surface-base);
        border: 1px solid var(--line-subtle);
        padding: 22px 24px 18px 24px;
        margin-bottom: 24px;
    }
    .figure-top {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 14px;
        border-bottom: 1px solid var(--line-subtle);
        padding-bottom: 10px;
    }
    .figure-title {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-headline);
        margin: 0;
    }
    .figure-tag {
        font-size: 10px;
        letter-spacing: 1px;
        color: var(--blue-primary);
        text-transform: uppercase;
        font-weight: 700;
    }
    .figure-caption-text {
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 10px;
        line-height: 1.6;
    }

    /* Two-Column Editorial Insight Block */
    .insight-strip {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin: 24px 0;
    }
    .insight-card {
        background: var(--surface-base);
        border: 1px solid var(--line-subtle);
        padding: 22px;
    }
    .insight-card h4 {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-headline);
        margin: 0 0 8px 0;
    }
    .insight-card p {
        font-size: 13px;
        color: var(--text-body);
        line-height: 1.6;
        margin: 0;
    }

    /* Editorial Finding Feature (Prominent Numbers) */
    .finding-feature {
        background: var(--surface-base);
        border: 1px solid var(--line-subtle);
        border-top: 3px solid var(--blue-primary);
        padding: 26px;
        margin-bottom: 26px;
    }
    .finding-numbers {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin: 18px 0 14px 0;
    }
    .finding-numbers strong {
        font-family: 'Libre Baskerville', Georgia, serif;
        font-size: 26px;
        font-weight: 400;
        display: block;
        color: var(--blue-primary);
        line-height: 1.2;
        font-variant-numeric: tabular-nums;
    }
    .finding-numbers span {
        display: block;
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 6px;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }

    /* Project Progress Grid */
    .progress-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 22px;
        margin-top: 24px;
        margin-bottom: 30px;
    }
    .progress-card {
        border: 1px solid var(--line-subtle);
        background: var(--surface-base);
        padding: 24px;
    }
    .progress-card .card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid var(--line-subtle);
        padding-bottom: 12px;
        margin-bottom: 16px;
    }
    .progress-card h3 {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-headline);
        margin: 0;
    }
    .pill {
        font-size: 10px;
        letter-spacing: 0.5px;
        font-weight: 700;
        padding: 4px 8px;
        text-transform: uppercase;
    }
    .pill.green {
        background: #11281e;
        color: #34d399;
        border: 1px solid #1c4b38;
    }
    .pill.blue {
        background: #132038;
        color: #60a5fa;
        border: 1px solid #1f365d;
    }
    .progress-card ul, .progress-card ol {
        margin: 0;
        padding-left: 20px;
    }
    .progress-card li {
        padding: 0 0 14px 4px;
        font-size: 13px;
        color: var(--text-body);
        line-height: 1.5;
    }
    .progress-card li:last-child {
        padding-bottom: 0;
    }
    .progress-card strong {
        display: block;
        color: var(--text-headline);
        font-size: 13.5px;
        margin-bottom: 3px;
    }
    .progress-card li span {
        font-size: 12px;
        color: var(--text-muted);
    }

    /* Boundary Banner */
    .boundary-banner {
        background: var(--surface-base);
        border: 1px solid var(--line-subtle);
        border-left: 3px solid var(--blue-primary);
        padding: 16px 20px;
        margin-bottom: 24px;
        font-size: 13px;
        line-height: 1.6;
        color: var(--text-body);
    }
    .boundary-banner strong {
        color: var(--text-headline);
    }

    /* Publication Table Wrapper */
    .table-caption-box {
        font-size: 12px;
        color: var(--text-muted);
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        text-transform: uppercase;
        font-weight: 600;
    }
    .fineprint {
        font-size: 11.5px !important;
        color: var(--text-muted) !important;
        line-height: 1.6;
        margin-top: 10px;
    }

    /* Footer */
    .site-footer {
        border-top: 1px solid var(--line-subtle);
        padding: 30px 0;
        margin-top: 50px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 12px;
        color: var(--text-muted);
    }
    .site-footer strong {
        color: var(--text-headline);
    }

    @media (max-width: 1100px) {
        .paper-hero {
            grid-template-columns: 1fr;
            gap: 30px;
        }
        .questions-grid, .editorial-stat-bar, .cohort-flow {
            grid-template-columns: 1fr 1fr;
        }
        .progress-grid, .insight-strip {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# MATPLOTLIB TECHNICAL RESEARCH PLOTTING SYSTEM
# -----------------------------------------------------------------------------
plt.style.use("default")
plt.rcParams.update({
    "font.sans-serif": "Arial",
    "font.size": 8.5,
    "text.color": "#f1f5f9",
    "axes.labelcolor": "#94a3b8",
    "xtick.color": "#94a3b8",
    "ytick.color": "#94a3b8",
    "axes.edgecolor": "#1e293b",
    "axes.linewidth": 0.8,
    "grid.color": "#182234",
    "grid.linestyle": "-",
    "grid.linewidth": 0.6,
    "figure.facecolor": "#111827",
    "axes.facecolor": "#111827",
    "figure.titlesize": 10.5,
    "axes.titlesize": 10.0,
    "axes.labelsize": 8.5,
    "xtick.labelsize": 8.0,
    "ytick.labelsize": 8.0,
})

def format_dark_axes(ax):
    """Apply uniform research-grade slate styling to axes."""
    ax.set_facecolor("#111827")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#1e293b")
    ax.spines["bottom"].set_color("#1e293b")
    ax.tick_params(colors="#94a3b8", which="both", direction="out", length=3)
    ax.grid(True, color="#182234", linestyle="-", linewidth=0.6, alpha=0.9)


# -----------------------------------------------------------------------------
# CACHED DATA LOADERS (Frozen Analytical Backend)
# -----------------------------------------------------------------------------
@st.cache_data
def load_session_data() -> pd.DataFrame:
    path = Path("data/processed/cleaned_sessions.csv")
    if not path.exists():
        st.error(f"Missing processed sessions file: {path}. Run `python main.py --phase preprocess`.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["conn_dt_local"] = pd.to_datetime(df["connectionTime_local"], utc=True).dt.tz_convert("America/Los_Angeles")
    return df


@st.cache_data
def load_hourly_data() -> pd.DataFrame:
    path = Path("data/processed/hourly_demand.csv")
    if not path.exists():
        st.error(f"Missing hourly demand file: {path}.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["ts_local"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    return df


@st.cache_data
def load_anomaly_results() -> pd.DataFrame:
    path = Path("outputs/results/session_anomaly_predictions.csv")
    if not path.exists():
        st.error(f"Missing anomaly predictions file: {path}.")
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data
def load_forecast_test_predictions() -> pd.DataFrame:
    path = Path("outputs/results/forecast_predictions_test.csv")
    if not path.exists():
        st.error(f"Missing test forecast predictions: {path}.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["ts_local"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    return df


@st.cache_data
def load_summary_tables() -> Dict[str, pd.DataFrame]:
    tables = {}
    table_files = {
        "summary_stats": "table1_session_summary_stats.csv",
        "temporal_demand": "table2_temporal_demand_summary.csv",
        "station_util": "table3_station_utilization_summary.csv",
        "covid_comparison": "table4_covid_period_comparison.csv",
        "data_quality": "table5_data_quality_flags_summary.csv",
        "model_comparison": "table6_forecasting_model_comparison.csv",
        "hyperparameters": "table7_hyperparameters_and_features.csv",
        "residual_analysis": "table8_residual_analysis.csv",
        "anomaly_summary": "table9_anomaly_summary.csv",
        "algo_agreement": "table10_algorithm_comparison.csv",
        "top_anomalies": "table11_top_anomalous_sessions.csv",
        "anomaly_profile": "table12_anomaly_feature_profile.csv",
        "consensus_matrix": "table13_algorithm_consensus.csv",
        "anomaly_dq": "table14_anomaly_vs_data_quality_flags.csv",
    }
    for key, filename in table_files.items():
        p = Path("outputs/tables") / filename
        if p.exists():
            tables[key] = pd.read_csv(p)
    return tables


# -----------------------------------------------------------------------------
# INITIALIZE BACKEND DATA
# -----------------------------------------------------------------------------
sessions_df = load_session_data()
hourly_df = load_hourly_data()
anomaly_df = load_anomaly_results()
forecast_test_df = load_forecast_test_predictions()
tables_dict = load_summary_tables()

if sessions_df.empty or hourly_df.empty:
    st.error("Essential analytical datasets could not be loaded. Please ensure the pipeline has completed.")
    st.stop()


# -----------------------------------------------------------------------------
# SIDEBAR FILTERS & METADATA CARD
# -----------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div class="sb-brand">
        <div class="sb-brand-icon">EV</div>
        <div class="sb-brand-text">
            EV CHARGING ANALYTICS
            <small>RESEARCH ARCHIVE · 2024–2026</small>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown('<div class="sb-section-hdr">Data Filtering Controls</div>', unsafe_allow_html=True)

# Filter 1: Station Selector
all_stations = sorted(list(sessions_df["stationID"].unique()))
selected_station = st.sidebar.selectbox("Station Cohort:", ["All Stations (54)"] + all_stations)

# Filter 2: Day Type Selector
day_type_filter = st.sidebar.selectbox("Day Classification:", ["All Days", "Weekdays Only", "Weekends Only"])

# Filter 3: COVID Period Selector
covid_filter = st.sidebar.selectbox("Campus Period:", ["All Periods", "Pre-Lockdown", "Lockdown", "Post-Lockdown-Recovery"])

# Filter 4: Anomaly Status Selector
if not anomaly_df.empty and "is_consensus_anomaly" in anomaly_df.columns:
    anomaly_filter = st.sidebar.selectbox("Session Status:", ["All Sessions", "Typical Sessions Only", "Consensus Outliers Only"])
else:
    anomaly_filter = "All Sessions"

# Non-destructive session filtering
filtered_sessions = sessions_df.copy()

if selected_station != "All Stations (54)":
    filtered_sessions = filtered_sessions[filtered_sessions["stationID"] == selected_station]

if day_type_filter == "Weekdays Only":
    filtered_sessions = filtered_sessions[filtered_sessions["is_weekend"] == 0]
elif day_type_filter == "Weekends Only":
    filtered_sessions = filtered_sessions[filtered_sessions["is_weekend"] == 1]

if covid_filter != "All Periods":
    filtered_sessions = filtered_sessions[filtered_sessions["covid_period"] == covid_filter]

if anomaly_filter == "Typical Sessions Only" and not anomaly_df.empty:
    typical_ids = set(anomaly_df.loc[anomaly_df["is_consensus_anomaly"] == 0, "sessionID"])
    filtered_sessions = filtered_sessions[filtered_sessions["sessionID"].isin(typical_ids)]
elif anomaly_filter == "Consensus Outliers Only" and not anomaly_df.empty:
    anom_ids = set(anomaly_df.loc[anomaly_df["is_consensus_anomaly"] == 1, "sessionID"])
    filtered_sessions = filtered_sessions[filtered_sessions["sessionID"].isin(anom_ids)]

# Sidebar Dataset Metadata Card
st.sidebar.markdown(
    """
    <div class="sb-dataset-card">
        <div class="tag">Empirical Data Provenance</div>
        <div class="title">Caltech ACN-Data</div>
        <dl>
            <dt>Observation Period</dt>
            <dd>Jan 2020 – Sep 2021</dd>
            <dt>Project Horizon</dt>
            <dd>2024–2026 Presentation</dd>
            <dt>Verified Sessions</dt>
            <dd>5,000 completed</dd>
            <dt>Total Monitored Time</dt>
            <dd>14,422 continuous hours</dd>
            <dt>Delivered Energy</dt>
            <dd>53,668.78 kWh (53.67 MWh)</dd>
            <dt>Active EVSE Ports</dt>
            <dd>54 Level-2 stations</dd>
        </dl>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# EDITORIAL TOP SITE HEADER & HORIZONTAL NAVIGATION
# -----------------------------------------------------------------------------
st.markdown(
    """
    <header class="site-header">
        <div class="site-brand">
            <div class="site-brand-icon">EV</div>
            <div class="site-brand-title">
                EV CHARGING ANALYTICS
                <small>RESEARCH ARCHIVE & BENCHMARK</small>
            </div>
        </div>
        <div class="site-header-meta">
            <span class="site-meta-pill">PROJECT TIMELINE 2024–2026</span>
            <span class="site-meta-date">CALTECH ACN-DATA · GARAGE 0039</span>
        </div>
    </header>
    """,
    unsafe_allow_html=True,
)

# Compact Horizontal Research Navigation Bar
nav_options = [
    "Overview",
    "Charging Behavior",
    "Demand & Peaks",
    "Forecasting",
    "Anomaly Detection",
    "Smart-Grid Context",
]

selected_nav = st.radio(
    "Navigation Sections",
    nav_options,
    index=0,
    horizontal=True,
    label_visibility="collapsed",
)


# -----------------------------------------------------------------------------
# 1. OVERVIEW VIEW
# -----------------------------------------------------------------------------
if selected_nav == "Overview":
    # Editorial Paper Hero
    st.markdown(
        """
        <section class="paper-hero">
            <div class="hero-main">
                <div class="eyebrow">
                    <span class="category-tag">ENERGY INFORMATICS</span>
                    <span>RESEARCH MONOGRAPH · 2024–2026 ARCHIVE</span>
                </div>
                <h1 class="hero-title">
                    EV Charging Analytics
                    <span>Empirical Demand Dynamics, Flexibility Buffers, and Telemetry Outliers</span>
                </h1>
                <p class="hero-subtitle">
                    A multi-phase empirical investigation of workplace charging behavior at the Caltech Adaptive Charging Network.
                </p>
                <div class="authors-block">
                    <span>Applied Data Analytics Lab</span>
                    <span>Energy Systems Division</span>
                    <span>Smart Grid Research Group</span>
                </div>
                <div class="paper-meta-row">
                    <span><strong>5,000</strong> verified sessions</span>
                    <span><strong>14,422</strong> continuous hours</span>
                    <span><strong>53.67 MWh</strong> total energy</span>
                    <span><strong>54</strong> Level-2 EVSE ports</span>
                    <span>ACN-Data Garage 0039</span>
                </div>
            </div>
            <aside class="hero-aside">
                <div class="aside-top">
                    <span>THE CENTRAL INQUIRY</span>
                    <span class="index">01 / 06</span>
                </div>
                <h2>Can long dwell times mitigate morning peak ramps?</h2>
                <p>
                    Workplace vehicle arrivals concentrate sharply between 08:00 and 10:00 PST/PDT. 
                    However, vehicles dwell for a median of 1.30 hours after full charging is complete, 
                    creating substantial operational slack for managed charging without degrading driver utility.
                </p>
                <div class="aside-foot">
                    Diurnal load · Flexibility windows · Regularized forecasting · Consensus anomalies
                </div>
            </aside>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Status Banner
    st.markdown(
        """
        <div class="status-banner">
            <span class="status-label">RESEARCH PLATFORM · 2024–2026</span>
            <p>
                Presentation and analytical benchmark updated for the 2024–2026 research timeline. 
                Underlying observations reflect exactly 5,000 real-world sessions collected from January 2020 through September 2021 
                under the Caltech Adaptive Charging Network (ACN-Data) protocol.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 01: Research Questions
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">01</span>
            <h2>Core Research Questions</h2>
            <span class="section-note">ANALYTICAL SCOPE</span>
        </div>
        <p class="lead">
            Four targeted questions structure this empirical investigation of workplace EV charging infrastructure.
        </p>
        <div class="questions-grid">
            <article class="question-card">
                <span>RQ 01</span>
                <h3>Diurnal Arrivals & Dwell</h3>
                <p>How do commuter arrival distributions, energy requests, and connection durations cluster across workplace charging ports?</p>
            </article>
            <article class="question-card">
                <span>RQ 02</span>
                <h3>Aggregated Demand Peaks</h3>
                <p>What are the coincidence factors and peak hourly demand profiles across business weekdays versus weekends?</p>
            </article>
            <article class="question-card">
                <span>RQ 03</span>
                <h3>Time-Series Generalization</h3>
                <p>Can regularized linear models match or outperform gradient-boosted trees when forecasting zero-inflated hourly demand?</p>
            </article>
            <article class="question-card">
                <span>RQ 04</span>
                <h3>Unsupervised Anomaly Consensus</h3>
                <p>Which charging sessions reflect extreme physical dwell, logging telemetry corruptions, or unusual energy over-deliveries?</p>
            </article>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 02: Dataset & Groundwork
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">02</span>
            <h2>Dataset Provenance & Boundary Audit</h2>
            <span class="section-note">DATASET SUMMARY</span>
        </div>
        <p class="lead">
            Continuous Level-2 charging telemetry from Caltech Garage Site 0002 (Cluster 0039), audited for exact conservation of energy.
        </p>
        <ol class="cohort-flow">
            <li>
                <span>01 · RAW TELEMETRY</span>
                <strong>5,000 sessions</strong>
                <p>54 Level-2 charging ports observed from January 2020 through September 2021.</p>
            </li>
            <li>
                <span>02 · TEMPORAL HARMONIZATION</span>
                <strong>14,422 hours</strong>
                <p>Continuous hourly grid series with zero-demand preservation (79.14% zero-demand intervals).</p>
            </li>
            <li>
                <span>03 · CONSERVED ENERGY</span>
                <strong>53,668.78 kWh</strong>
                <p>Exact mathematical conservation between session sums and hourly aggregations (53.67 MWh).</p>
            </li>
        </ol>
        """,
        unsafe_allow_html=True,
    )

    # Editorial Stat Bar for Current Filtered Slice
    tot_sessions = len(filtered_sessions)
    tot_energy = filtered_sessions["kWhDelivered"].sum()
    avg_energy = filtered_sessions["kWhDelivered"].mean() if tot_sessions > 0 else 0.0
    med_conn = filtered_sessions["connection_duration_hr"].median() if tot_sessions > 0 else 0.0

    st.markdown(
        f"""
        <div class="editorial-stat-bar">
            <div>
                <strong>{tot_sessions:,}</strong>
                <span>Filtered Sessions ({tot_sessions/len(sessions_df)*100:.1f}%)</span>
            </div>
            <div>
                <strong>{tot_energy/1000.0:.2f} MWh</strong>
                <span>Delivered Energy ({tot_energy:,.2f} kWh)</span>
            </div>
            <div>
                <strong>{avg_energy:.2f} kWh</strong>
                <span>Mean Delivery (Med: {filtered_sessions['kWhDelivered'].median():.2f} kWh)</span>
            </div>
            <div>
                <strong>{med_conn:.2f} h</strong>
                <span>Median Dwell (Mean: {filtered_sessions['connection_duration_hr'].mean():.2f} h)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 03: Primary Demand Evidence
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">03</span>
            <h2>Primary Analytical Evidence</h2>
            <span class="section-note">CONTINUOUS FACILITY LOAD</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="figure-frame">
            <div class="figure-top">
                <h4 class="figure-title">Continuous Facility EV Charging Demand (14,422 Hours)</h4>
                <span class="figure-tag">Figure 1 · Time Series</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    fig, ax = plt.subplots(figsize=(15, 3.8), facecolor="#111827", dpi=160)
    format_dark_axes(ax)
    ts = pd.to_datetime(hourly_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    ax.fill_between(ts, 0, hourly_df["total_kwh_delivered"], color="#3b82f6", alpha=0.12)
    ax.plot(ts, hourly_df["total_kwh_delivered"], color="#3b82f6", linewidth=0.8, label="Hourly EV Demand (kWh)")

    lockdown_start = pd.Timestamp("2020-03-19", tz="America/Los_Angeles")
    lockdown_end = pd.Timestamp("2020-10-31", tz="America/Los_Angeles")
    ax.axvspan(lockdown_start, lockdown_end, color="#1e293b", alpha=0.75, label="COVID-19 Campus Lockdown (Structural Break)")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_ylabel("Demand (kWh)")
    ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9", loc="upper right")
    st.pyplot(fig)
    plt.close()
    st.markdown(
        """
            <p class="figure-caption-text">
                Continuous hourly aggregated energy delivery across the full 14,422-hour monitoring horizon. 
                The COVID-19 lockdown (March–October 2020) precipitated an 89% structural reduction in charging volume, 
                followed by steady post-lockdown commuter recovery.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Key Empirical Insights Beside Figure
    st.markdown(
        """
        <div class="insight-strip">
            <div class="insight-card">
                <h4>Diurnal Commuter Clustering</h4>
                <p>
                    Session connections peak sharply between 08:00 and 10:00 PST/PDT, driving facility hourly demand to 
                    22.45 kWh/hr at 10:00 AM. Weekend volume drops by over 80% compared to typical business days.
                </p>
            </div>
            <div class="insight-card">
                <h4>Dwell-Time Flexibility Window</h4>
                <p>
                    Vehicles remain plugged in for a median of 1.30 idle hours after energy replenishment is complete 
                    (median connection: 2.46 h vs median charging: 1.46 h), creating operational flexibility for site scheduling.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 04: Project Progress & Roadmap (2024–2026)
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">04</span>
            <h2>Project Status & Research Deliverables</h2>
            <span class="section-note">ROADMAP · 2024–2026</span>
        </div>
        <p class="lead">
            Deliverables completed for the current release and planned extensions for multi-site grid integration.
        </p>
        <div class="progress-grid">
            <article class="progress-card">
                <div class="card-top">
                    <h3>Completed Groundwork</h3>
                    <span class="pill green">Available Evidence</span>
                </div>
                <ul>
                    <li>
                        <strong>Data Quality & Energy Conservation Audit</strong>
                        <span>5,000 sessions audited; exact 53,668.78 kWh conservation verified between session and hourly aggregations.</span>
                    </li>
                    <li>
                        <strong>Empirical EDA & Dwell Characterization</strong>
                        <span>Arrival distributions, energy demand skewness, and 1.30-hour median idle dwell buffers quantified.</span>
                    </li>
                    <li>
                        <strong>Time-Series Forecasting Benchmark</strong>
                        <span>Rigorous 70/15/15 chronological split; Ridge Regression (Validation RMSE 13.168 kWh) selected over naive baselines.</span>
                    </li>
                    <li>
                        <strong>Dual-Model Anomaly Detection</strong>
                        <span>Isolation Forest and LOF consensus identified 33 extreme outliers (0.66%) with domain explanations.</span>
                    </li>
                    <li>
                        <strong>Smart-Grid Flexibility Analysis</strong>
                        <span>Morning peak ramp coincidence and 41.7% mean idle ratio evaluated for managed charging.</span>
                    </li>
                </ul>
            </article>
            <article class="progress-card">
                <div class="card-top">
                    <h3>Future Research Extensions</h3>
                    <span class="pill blue">Planned Scope</span>
                </div>
                <ol>
                    <li>
                        <strong>Multi-Site Transfer Benchmarking</strong>
                        <span>Extend forecasting and anomaly algorithms to JPL and Office Garage sites in the wider ACN network.</span>
                    </li>
                    <li>
                        <strong>Online Real-Time Current Modulation</strong>
                        <span>Deploy Model Predictive Control (MPC) algorithms using the empirical 1.30-hour dwell buffer.</span>
                    </li>
                    <li>
                        <strong>Transformer Substation Telemetry Integration</strong>
                        <span>Harmonize garage EVSE demand with physical building sub-meters and utility feed constraints.</span>
                    </li>
                    <li>
                        <strong>Dynamic Time-of-Use (TOU) Tariff Optimization</strong>
                        <span>Evaluate automated cost-minimization under California CAISO and Southern California Edison rate structures.</span>
                    </li>
                </ol>
            </article>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# 2. CHARGING BEHAVIOR VIEW
# -----------------------------------------------------------------------------
elif selected_nav == "Charging Behavior":
    st.markdown(
        """
        <div class="section-head" style="margin-top: 10px;">
            <span class="section-number">01</span>
            <h2>Diurnal Arrival & Departure Dynamics</h2>
            <span class="section-note">COMMUTER PATTERNS</span>
        </div>
        <p class="lead">
            Arrivals concentrate acutely during the morning commute, while departures distribute broadly across afternoon work hours.
        </p>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Connection vs Disconnection Hours</h4>
                    <span class="figure-tag">Diurnal Profile</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.6), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        conn_h = filtered_sessions["conn_hour"].value_counts().sort_index()
        disc_h = filtered_sessions["disc_hour"].value_counts().sort_index()
        ax.plot(conn_h.index, conn_h.values, marker="o", markersize=3.5, color="#3b82f6", linewidth=1.6, label="Arrivals (Connection)")
        ax.plot(disc_h.index, disc_h.values, marker="s", markersize=3.5, color="#14b8a6", linewidth=1.5, linestyle="--", label="Departures (Disconnect)")
        ax.set_xlabel("Hour of Day (PST/PDT)")
        ax.set_ylabel("Sessions")
        ax.set_xticks(range(0, 24, 2))
        ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Arrivals peak sharply at 08:00–10:00 PST/PDT (workplace morning commute), whereas departures ramp smoothly between 14:00 and 18:00.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Weekly Volume Distribution</h4>
                    <span class="figure-tag">Day of Week</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.6), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if "conn_day_name" in filtered_sessions.columns:
            dow_counts = filtered_sessions["conn_day_name"].value_counts().reindex(day_order).fillna(0)
        elif "conn_dt_local" in filtered_sessions.columns:
            dow_counts = filtered_sessions["conn_dt_local"].dt.day_name().value_counts().reindex(day_order).fillna(0)
        else:
            dow_counts = pd.Series(0, index=day_order)
        ax.bar(dow_counts.index, dow_counts.values, color="#3b82f6", width=0.6)
        ax.set_ylabel("Total Sessions")
        plt.xticks(rotation=25, ha="right")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Tuesday through Thursday represent peak charging traffic. Weekend demand drops by >80%, affirming workplace-dominant utilization.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Numbered Section 02: Energy Distribution & Driver Requests
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">02</span>
            <h2>Energy Delivery & Driver Requests</h2>
            <span class="section-note">CONSUMPTION PROFILE</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Requested vs Delivered Energy Parity</h4>
                    <span class="figure-tag">Scatter · Parity</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        valid_req = filtered_sessions.dropna(subset=["kWhRequested", "kWhDelivered"]).copy()
        if not valid_req.empty:
            fig, ax = plt.subplots(figsize=(8, 4.0), facecolor="#111827", dpi=160)
            format_dark_axes(ax)
            norm = valid_req[valid_req["over_delivery_flag"] == 0]
            over = valid_req[valid_req["over_delivery_flag"] == 1]
            ax.scatter(norm["kWhRequested"], norm["kWhDelivered"], alpha=0.35, color="#3b82f6", s=18, label=f"Normal Delivery ({len(norm):,})")
            ax.scatter(over["kWhRequested"], over["kWhDelivered"], alpha=0.7, color="#d97706", s=22, label=f"Over-Delivered ({len(over):,})")
            ax.plot([0, 150], [0, 150], color="#64748b", linestyle="--", linewidth=1.0, label="1:1 Parity Line")
            ax.set_xlabel("Driver Requested Energy (kWh)")
            ax.set_ylabel("Actual Delivered Energy (kWh)")
            ax.set_xlim(0, 150)
            ax.set_ylim(0, 80)
            ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9")
            st.pyplot(fig)
            plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Vehicles typically receive less than requested due to full battery saturation prior to departure. Over-delivery occurs in 255 sessions (5.1%).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Session Summary Statistics</h4>
                    <span class="figure-tag">Table 1 Excerpt</span>
                </div>
                <div class="table-caption-box">Parametric vs Non-Parametric Metrics</div>
            """,
            unsafe_allow_html=True,
        )
        if "summary_stats" in tables_dict:
            t1_sub = tables_dict["summary_stats"][tables_dict["summary_stats"]["Variable"].isin(["kWhDelivered", "kWhRequested", "energy_error_kwh"])][["Variable", "Mean", "Median", "Q75", "Max"]]
            st.dataframe(t1_sub, hide_index=True, use_container_width=True)
        st.markdown(
            """
                <p class="fineprint">
                    Delivered energy is heavily right-skewed (median 6.33 kWh vs mean 10.73 kWh). 
                    The 75th percentile of delivered energy is 13.73 kWh, indicating most sessions require modest top-ups.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Numbered Section 03: Connection Dwell vs Active Charging
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">03</span>
            <h2>Connection Duration & Operational Idle Time</h2>
            <span class="section-note">FLEXIBILITY BUFFER</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_x, col_y = st.columns(2)
    with col_x:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Connection vs Active Charging Duration</h4>
                    <span class="figure-tag">Histograms</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.5), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        c_dur = filtered_sessions["connection_duration_hr"].dropna()
        ch_dur = filtered_sessions["charging_duration_hr"].dropna()
        ax.hist(c_dur, bins=40, range=(0, 20), alpha=0.55, color="#3b82f6", label="Connection Duration")
        ax.hist(ch_dur, bins=40, range=(0, 20), alpha=0.65, color="#14b8a6", label="Active Charging Duration")
        ax.set_xlabel("Duration (hours)")
        ax.set_ylabel("Frequency")
        ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Median connection duration is 2.46 hours, whereas active charging requires only a median of 1.46 hours (1.54 hours across all valid sessions).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_y:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Post-Charge Idle Stall Occupancy</h4>
                    <span class="figure-tag">Idle Buffer</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.5), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        idle_dur = filtered_sessions.loc[filtered_sessions["is_charging_completed"] == 1, "idle_duration_hr"].dropna()
        ax.hist(idle_dur, bins=35, range=(0, 15), color="#d97706", edgecolor="#111827", linewidth=0.5, alpha=0.85)
        med_idle = idle_dur.median()
        ax.axvline(med_idle, color="#f1f5f9", linestyle="--", linewidth=1.2, label=f"Median Idle: {med_idle:.2f} h")
        ax.set_xlabel("Idle Duration (hours)")
        ax.set_ylabel("Frequency")
        ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Median idle buffer is 1.30 hours across completed sessions. On average, 41.7% of plug-in duration is spent idle.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# 3. DEMAND & PEAKS VIEW
# -----------------------------------------------------------------------------
elif selected_nav == "Demand & Peaks":
    st.markdown(
        """
        <div class="boundary-banner">
            <strong>Target Specification Boundary:</strong> All metrics represent <strong>aggregated EV charging energy demand</strong> across the 54-station garage facility. This quantifies site-level EV load and does not represent total campus building consumption or local utility substation feeder load.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 01: Facility Hourly Demand Time Series
    st.markdown(
        """
        <div class="section-head" style="margin-top: 10px;">
            <span class="section-number">01</span>
            <h2>Facility-Wide Hourly Demand Series</h2>
            <span class="section-note">14,422 HOURS</span>
        </div>
        <p class="lead">
            The full uninterrupted hourly series preserves zero-demand intervals (79.14% of hours) and campus operating breaks.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="figure-frame">
            <div class="figure-top">
                <h4 class="figure-title">Continuous Facility EV Load (January 2020 – September 2021)</h4>
                <span class="figure-tag">Figure 2 · Empirical Demand</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    fig, ax = plt.subplots(figsize=(15, 3.8), facecolor="#111827", dpi=160)
    format_dark_axes(ax)
    ts = pd.to_datetime(hourly_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    ax.fill_between(ts, 0, hourly_df["total_kwh_delivered"], color="#3b82f6", alpha=0.10)
    ax.plot(ts, hourly_df["total_kwh_delivered"], color="#3b82f6", linewidth=0.75, label="Hourly EV Charging Demand (kWh)")

    lockdown_start = pd.Timestamp("2020-03-19", tz="America/Los_Angeles")
    lockdown_end = pd.Timestamp("2020-10-31", tz="America/Los_Angeles")
    ax.axvspan(lockdown_start, lockdown_end, color="#1e293b", alpha=0.75, label="COVID-19 Lockdown (Structural Contraction)")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_ylabel("Energy Demand (kWh)")
    ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9", loc="upper right")
    st.pyplot(fig)
    plt.close()
    st.markdown(
        """
            <p class="figure-caption-text">
                Continuous 14,422-hour aggregate series. The historical single-hour maximum was 77.7 kWh, observed during simultaneous multi-vehicle fast connection.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 02: Diurnal Load Profiles & Weekday–Weekend Contrast
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">02</span>
            <h2>Diurnal Demand Profiles & Day-Type Divergence</h2>
            <span class="section-note">DIURNAL METRICS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Mean Demand by Hour of Day</h4>
                    <span class="figure-tag">Diurnal Mean</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.6), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        h_ts = pd.to_datetime(hourly_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
        h_temp = hourly_df.copy()
        h_temp["hour"] = h_ts.dt.hour
        h_mean = h_temp.groupby("hour")["total_kwh_delivered"].mean()

        colors = ["#3b82f6" if h in [9, 10, 11] else "#1e293b" for h in h_mean.index]
        ax.bar(h_mean.index, h_mean.values, color=colors, width=0.75)
        ax.set_xlabel("Hour of Day (PST/PDT)")
        ax.set_ylabel("Mean Demand (kWh)")
        ax.set_xticks(range(0, 24, 2))
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Aggregated demand peaks at 10:00 AM with an empirical mean of 11.89 kWh/hr across all days (22.45 kWh/hr on weekdays).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Weekday vs Weekend Contrast</h4>
                    <span class="figure-tag">Overlay</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.6), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        h_temp["is_weekend"] = h_ts.dt.dayofweek.isin([5, 6]).astype(int)
        profiles = h_temp.groupby(["hour", "is_weekend"])["total_kwh_delivered"].mean().unstack()
        ax.plot(profiles.index, profiles[0], marker="o", markersize=3.5, color="#3b82f6", linewidth=1.8, label="Weekdays (Mon–Fri)")
        ax.plot(profiles.index, profiles[1], marker="s", markersize=3.5, color="#14b8a6", linewidth=1.5, linestyle="--", label="Weekends (Sat–Sun)")
        ax.set_xlabel("Hour of Day (PST/PDT)")
        ax.set_ylabel("Mean Demand (kWh)")
        ax.set_xticks(range(0, 24, 2))
        ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Weekday demand reaches 22.45 kWh/hr at 10:00 AM, dropping to near-zero after 22:00. Weekend demand remains subdued (<3 kWh/hr).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Numbered Section 03: Peak Demand Heatmap
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">03</span>
            <h2>Peak Demand Concentration Heatmap</h2>
            <span class="section-note">HOURLY × DAY MATRIX</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="figure-frame">
            <div class="figure-top">
                <h4 class="figure-title">Mean Demand by Day of Week and Hour of Day</h4>
                <span class="figure-tag">Figure 3 · Heatmap</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    fig, ax = plt.subplots(figsize=(14, 3.6), facecolor="#111827", dpi=160)
    format_dark_axes(ax)
    h_temp["dow"] = h_ts.dt.dayofweek
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    pivot = h_temp.pivot_table(index="dow", columns="hour", values="total_kwh_delivered", aggfunc="mean")
    pivot = pivot.reindex(range(7)).fillna(0)
    pivot.index = dow_names
    sns.heatmap(pivot, cmap="mako", ax=ax, cbar_kws={"label": "Mean kWh"}, linewidths=0.2, linecolor="#111827")
    ax.set_xlabel("Hour of Day (PST/PDT)")
    ax.set_ylabel("Day of Week")
    st.pyplot(fig)
    plt.close()
    st.markdown(
        """
            <p class="figure-caption-text">
                Heatmap of mean energy draw across all 168 hours of the weekly cycle. The Tuesday–Thursday 09:00–11:00 window represents the coincident peak.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 04: COVID Period Structural Break
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">04</span>
            <h2>Campus Operating Discontinuity Analysis</h2>
            <span class="section-note">TABLE 4 · COVID PERIODS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "covid_comparison" in tables_dict:
        st.markdown('<div class="table-caption-box">Table 4 · Structural Break Across Operating Phases</div>', unsafe_allow_html=True)
        st.dataframe(tables_dict["covid_comparison"], hide_index=True, use_container_width=True)
        st.markdown(
            """
            <p class="fineprint">
                The COVID-19 lockdown produced an 89% drop in monthly sessions. 
                Recovery shifted driver behavior toward shorter, higher-intensity connections (mean dwell: 3.00 h post-lockdown vs 5.82 h pre-lockdown).
            </p>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# 4. FORECASTING VIEW
# -----------------------------------------------------------------------------
elif selected_nav == "Forecasting":
    st.markdown(
        """
        <div class="section-head" style="margin-top: 10px;">
            <span class="section-number">01</span>
            <h2>Forecasting Model Selection & Protocol</h2>
            <span class="section-note">STRICT CHRONOLOGICAL BENCHMARK</span>
        </div>
        <p class="lead">
            Candidate forecasting models evaluated under strict chronological 70/15/15 train/validation/test partitions with zero lookahead leakage.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Top Model Selection Finding Bar
    st.markdown(
        """
        <div class="finding-feature">
            <span class="category-tag">SELECTED MODEL · VALIDATION PROTOCOL</span>
            <div class="finding-numbers">
                <div>
                    <strong>Ridge Regression</strong>
                    <span>Selected Pipeline (α=10.0)</span>
                </div>
                <div>
                    <strong>13.168 kWh</strong>
                    <span>Validation RMSE (Selection Target)</span>
                </div>
                <div>
                    <strong>15.713 kWh</strong>
                    <span>Holdout Test RMSE (July–Sept 2021)</span>
                </div>
            </div>
            <p style="font-size: 13px; color: var(--text-body); margin: 0;">
                Ridge Regression was selected based strictly on Validation RMSE (May–June 2021). 
                On the untouched test set (July–September 2021), XGBoost attained 15.633 kWh and Random Forest attained 15.851 kWh, 
                confirming strong concordance across linear regularized and tree ensemble approaches. Both beat naive seasonal baselines by >23%.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 02: Holdout Actual vs Forecast
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">02</span>
            <h2>Holdout Actual vs Forecast Evaluation</h2>
            <span class="section-note">TEST HORIZON · JULY – SEPTEMBER 2021</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pred_ts = pd.to_datetime(forecast_test_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    min_date = pred_ts.min().date()
    max_date = pred_ts.max().date()

    col_ctrl1, col_ctrl2 = st.columns([2, 3])
    with col_ctrl1:
        date_range = st.date_input("Filter Zoom Window:", (min_date, max_date), min_value=min_date, max_value=max_date)

    if isinstance(date_range, tuple) and len(date_range) == 2:
        mask = (pred_ts.dt.date >= date_range[0]) & (pred_ts.dt.date <= date_range[1])
        plot_df = forecast_test_df[mask]
        plot_ts = pred_ts[mask]
    else:
        plot_df = forecast_test_df
        plot_ts = pred_ts

    st.markdown(
        """
        <div class="figure-frame">
            <div class="figure-top">
                <h4 class="figure-title">Actual Demand vs Model Predictions (1,795 Test Hours)</h4>
                <span class="figure-tag">Figure 4 · Forecast Curves</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    fig, ax = plt.subplots(figsize=(15, 4.0), facecolor="#111827", dpi=160)
    format_dark_axes(ax)
    ax.plot(plot_ts, plot_df["actual"], color="#60a5fa", linewidth=1.1, label="Actual EV Demand (kWh)")
    ax.plot(plot_ts, plot_df["Ridge_Regression"], color="#14b8a6", linewidth=1.2, linestyle="-", label="Ridge Regression (Selected)")
    ax.plot(plot_ts, plot_df["XGBoost"], color="#d97706", linewidth=1.0, linestyle="--", label="XGBoost Regressor")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.set_ylabel("Energy Demand (kWh)")
    ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9", loc="upper right")
    st.pyplot(fig)
    plt.close()
    st.markdown(
        """
            <p class="figure-caption-text">
                Comparison of holdout actual demand against Ridge Regression and XGBoost forecasts across 1,795 test hours. 
                Models capture the diurnal rhythm accurately while smoothing acute burst spikes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 03: Model Performance Benchmark Table
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">03</span>
            <h2>Model Performance Comparison</h2>
            <span class="section-note">TABLE 6 · VALIDATED BENCHMARK</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "model_comparison" in tables_dict:
        st.markdown('<div class="table-caption-box">Table 6 · Forecasting Model Benchmark across Validation and Test Sets</div>', unsafe_allow_html=True)
        st.dataframe(tables_dict["model_comparison"], hide_index=True, use_container_width=True)
        st.markdown(
            """
            <p class="fineprint">
                Metric definitions: RMSE (Root Mean Squared Error, primary optimization criterion), MAE (Mean Absolute Error), 
                R² (Coefficient of Determination), sMAPE (Symmetric Mean Absolute Percentage Error). 
                Seasonal Naive models exhibit negative R², verifying that static calendar persistence fails under dynamic EV charging demand.
            </p>
            """,
            unsafe_allow_html=True,
        )

    # Numbered Section 04: Residual Analysis & Diagnostics
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">04</span>
            <h2>Residual Diagnostics & Demand Tier Errors</h2>
            <span class="section-note">ERROR ANALYSIS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Ridge Regression Residual Distribution</h4>
                    <span class="figure-tag">Histogram</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.6), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        residuals = forecast_test_df["actual"] - forecast_test_df["Ridge_Regression"]
        ax.hist(residuals, bins=45, color="#3b82f6", edgecolor="#111827", linewidth=0.5, alpha=0.85)
        ax.axvline(0, color="#f1f5f9", linestyle="--", linewidth=1.0)
        ax.set_xlabel("Residual Error (Actual - Predicted, kWh)")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Residuals center cleanly near zero with an extended right tail during rare simultaneous-connection bursts.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_r2:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Residual Analysis by Demand Tier</h4>
                    <span class="figure-tag">Table 8 Diagnostics</span>
                </div>
                <div class="table-caption-box">Forecast Performance Stratified by Demand Tiers</div>
            """,
            unsafe_allow_html=True,
        )
        if "residual_analysis" in tables_dict:
            st.dataframe(tables_dict["residual_analysis"], hide_index=True, use_container_width=True)
        st.markdown(
            """
                <p class="fineprint">
                    Point forecasts under-predict high-demand spikes (>59.1 kWh) by +63.3 kWh on average, demonstrating that smart charging infrastructure requires dynamic real-time current throttling rather than relying solely on deterministic forecasts.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# 5. ANOMALY DETECTION VIEW
# -----------------------------------------------------------------------------
elif selected_nav == "Anomaly Detection":
    st.markdown(
        """
        <div class="boundary-banner">
            <strong>Methodological Boundary Note:</strong> Detected anomaly flags represent <strong>statistical outliers</strong> in multivariate charging behavior. In the absence of physical charger maintenance records, these flags should not be interpreted as confirmed equipment hardware failures, cyber attacks, or billing fraud.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 01: Unsupervised Ensemble Framework
    st.markdown(
        """
        <div class="section-head" style="margin-top: 10px;">
            <span class="section-number">01</span>
            <h2>Unsupervised Anomaly Framework & Score Distributions</h2>
            <span class="section-note">DUAL-MODEL METHODOLOGY</span>
        </div>
        <p class="lead">
            Isolation Forest (isolation path depth) and Local Outlier Factor (local reachability density) deployed with fixed 3.00% contamination thresholds.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Ensemble Overview Bar
    st.markdown(
        """
        <div class="editorial-stat-bar">
            <div>
                <strong>150</strong>
                <span>Isolation Forest Flags (3.00%)</span>
            </div>
            <div>
                <strong>150</strong>
                <span>Local Outlier Factor Flags (3.00%)</span>
            </div>
            <div>
                <strong>33</strong>
                <span>Consensus Outliers (0.66%)</span>
            </div>
            <div>
                <strong>267</strong>
                <span>Union Flagged Sessions (5.34%)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Isolation Forest Anomaly Scores</h4>
                    <span class="figure-tag">iForest Score</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.4), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        ax.hist(anomaly_df["score_isolation_forest"], bins=40, color="#3b82f6", edgecolor="#111827", linewidth=0.5, alpha=0.85)
        thresh_if = anomaly_df.loc[anomaly_df["flag_isolation_forest"] == 1, "score_isolation_forest"].max()
        ax.axvline(thresh_if, color="#d97706", linestyle="--", linewidth=1.2, label=f"3% Cutoff: {thresh_if:.4f}")
        ax.set_xlabel("Isolation Forest Score")
        ax.set_ylabel("Frequency")
        ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Lower decision values represent shorter isolation tree paths, indicating multidimensional abnormality.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_s2:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Local Outlier Factor (LOF) Scores</h4>
                    <span class="figure-tag">Negative LOF</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.4), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        ax.hist(anomaly_df["score_lof"], bins=40, color="#14b8a6", edgecolor="#111827", linewidth=0.5, alpha=0.85)
        thresh_lof = anomaly_df.loc[anomaly_df["flag_lof"] == 1, "score_lof"].min()
        ax.axvline(thresh_lof, color="#d97706", linestyle="--", linewidth=1.2, label=f"3% Cutoff: {thresh_lof:.4f}")
        ax.set_xlabel("Negative Local Outlier Factor")
        ax.set_ylabel("Frequency")
        ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Significantly negative scores denote local reachability densities substantially lower than k=25 nearest neighbors.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Numbered Section 02: Concordance Scatter Plot
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">02</span>
            <h2>Algorithm Concordance & Consensus Separation</h2>
            <span class="section-note">DUAL-DETECTOR AGREEMENT</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_p1, c_p2 = st.columns([2, 3])
    with c_p1:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Dual-Detector Agreement Matrix</h4>
                    <span class="figure-tag">Concordance</span>
                </div>
                <div class="table-caption-box">Binary Overlap & Similarity</div>
            """,
            unsafe_allow_html=True,
        )
        if "algo_agreement" in tables_dict:
            st.dataframe(tables_dict["algo_agreement"], hide_index=True, use_container_width=True)
        st.markdown(
            """
                <p class="fineprint">
                    The two algorithms attain 95.32% overall classification concordance and a Jaccard overlap index of 0.1236. 
                    The 33 consensus anomalies represent the most robust and extreme deviations across both density and tree projection spaces.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_p2:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Score Space Concordance Scatter</h4>
                    <span class="figure-tag">Figure 5 · Consensus Scatter</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.8), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        norm_mask = anomaly_df["is_consensus_anomaly"] == 0
        anom_mask = anomaly_df["is_consensus_anomaly"] == 1
        ax.scatter(anomaly_df.loc[norm_mask, "score_isolation_forest"], anomaly_df.loc[norm_mask, "score_lof"], alpha=0.25, color="#64748b", s=14, label="Normal / Single Flag")
        ax.scatter(anomaly_df.loc[anom_mask, "score_isolation_forest"], anomaly_df.loc[anom_mask, "score_lof"], alpha=0.85, color="#d97706", s=28, label="Consensus Outliers (n=33)")
        ax.set_xlabel("Isolation Forest Score")
        ax.set_ylabel("Local Outlier Factor Score")
        ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Isolation Forest decision score vs LOF score across all 5,000 sessions. Consensus anomalies (amber) occupy the joint bottom-left quadrant.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Numbered Section 03: Anomaly Characteristics
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">03</span>
            <h2>Anomaly Characteristics vs Typical Sessions</h2>
            <span class="section-note">TABLE 12 · FEATURE PROFILE</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "anomaly_profile" in tables_dict:
        st.markdown('<div class="table-caption-box">Table 12 · Quantitative Divergence between Typical Sessions and Consensus Anomalies</div>', unsafe_allow_html=True)
        st.dataframe(tables_dict["anomaly_profile"], hide_index=True, use_container_width=True)
        st.markdown(
            """
            <p class="fineprint">
                Consensus anomalies consume <strong>4.87x higher median energy</strong> (30.7 kWh vs 6.3 kWh) and experience 
                <strong>7.23x longer idle stall occupancy</strong> (9.26 h vs 1.28 h).
            </p>
            """,
            unsafe_allow_html=True,
        )

    # Numbered Section 04: Flagged Sessions Table
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">04</span>
            <h2>Top Flagged Sessions & Domain Explanations</h2>
            <span class="section-note">TABLE 11 · AUDITED CASES</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "top_anomalies" in tables_dict:
        st.markdown('<div class="table-caption-box">Table 11 · Audited High-Rank Anomalous Sessions with Domain Explanations</div>', unsafe_allow_html=True)
        st.dataframe(tables_dict["top_anomalies"], hide_index=True, use_container_width=True)
        st.markdown(
            """
            <p class="fineprint">
                Explanations synthesize behavioral indicators: extreme dwell duration (>24h), uncharacteristic non-charging stall occupancy, 
                and telemetry data artifacts (e.g. impossible charging rates resulting from truncated duration timestamps).
            </p>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# 6. SMART-GRID CONTEXT VIEW
# -----------------------------------------------------------------------------
elif selected_nav == "Smart-Grid Context":
    st.markdown(
        """
        <div class="boundary-banner">
            <strong>Mandatory Scope Boundary Callout:</strong> This analysis is grounded strictly in <strong>facility-level EV charging telemetry</strong>. Transformer head loading, total campus building electricity draw, municipal substation loading, and distribution feeder constraints were not measured in the Caltech ACN-Data telemetry.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 01: Morning Peak Coincidence
    st.markdown(
        """
        <div class="section-head" style="margin-top: 10px;">
            <span class="section-number">01</span>
            <h2>Morning Peak Coincidence & Ramp Profile</h2>
            <span class="section-note">FACILITY LOAD DYNAMICS</span>
        </div>
        <p class="lead">
            Unmanaged charging initiates immediately upon driver plug-in, concentrating peak facility demand into the 08:00–10:00 morning commute window.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="figure-frame">
            <div class="figure-top">
                <h4 class="figure-title">Weekday Mean Charging Demand Profile & Morning Peak Window</h4>
                <span class="figure-tag">Figure 6 · Load Profile</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    fig, ax = plt.subplots(figsize=(15, 3.8), facecolor="#111827", dpi=160)
    format_dark_axes(ax)
    h_ts = pd.to_datetime(hourly_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    h_temp = hourly_df.copy()
    h_temp["hour"] = h_ts.dt.hour
    h_temp["is_weekend"] = h_ts.dt.dayofweek.isin([5, 6]).astype(int)
    weekday_profile = h_temp[h_temp["is_weekend"] == 0].groupby("hour")["total_kwh_delivered"].mean()

    ax.plot(weekday_profile.index, weekday_profile.values, color="#3b82f6", linewidth=2.0, marker="o", markersize=4, label="Weekday Mean Demand (kWh)")
    ax.axvspan(8, 10, color="#162032", alpha=0.9, label="Morning Peak Window (08:00–10:00)")
    ax.axvline(10, color="#d97706", linestyle=":", linewidth=1.2, label="Peak Hour: 10:00 AM (22.45 kWh)")

    ax.set_xlabel("Hour of Day (PST/PDT)")
    ax.set_ylabel("Mean Energy Demand (kWh)")
    ax.set_xticks(range(0, 24))
    ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9", loc="upper right")
    st.pyplot(fig)
    plt.close()
    st.markdown(
        """
            <p class="figure-caption-text">
                Weekday hourly demand profile. The sharp morning ramp coincides with building HVAC and lighting startup, multiplying commercial peak demand charges.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Numbered Section 02: Quantified Dwell-Time Flexibility
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">02</span>
            <h2>Quantified Dwell-Time Flexibility Windows</h2>
            <span class="section-note">LOAD-SHIFTING POTENTIAL</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_flx1, col_flx2 = st.columns(2)
    with col_flx1:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Duration Components Breakdown</h4>
                    <span class="figure-tag">Median Hours</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.4), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        durations = filtered_sessions[["connection_duration_hr", "charging_duration_hr", "idle_duration_hr"]].dropna()
        medians = [durations["connection_duration_hr"].median(), durations["charging_duration_hr"].median(), durations["idle_duration_hr"].median()]
        labels = ["Connection", "Active Charging", "Idle Dwell"]
        colors = ["#3b82f6", "#14b8a6", "#d97706"]
        ax.bar(labels, medians, color=colors, width=0.55)
        ax.set_ylabel("Median Hours")
        for i, v in enumerate(medians):
            ax.text(i, v + 0.08, f"{v:.2f} h", ha="center", color="#f1f5f9", fontsize=8.5, fontweight="600")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    Vehicles occupy stalls for a median of 2.46 hours while requiring active power for only 1.46 hours.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_flx2:
        st.markdown(
            """
            <div class="figure-frame">
                <div class="figure-top">
                    <h4 class="figure-title">Idle Ratio Distribution</h4>
                    <span class="figure-tag">Stall Utilization</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig, ax = plt.subplots(figsize=(7, 3.4), facecolor="#111827", dpi=160)
        format_dark_axes(ax)
        ratios = filtered_sessions["idle_to_connection_ratio"].dropna()
        ax.hist(ratios, bins=35, color="#14b8a6", edgecolor="#111827", linewidth=0.5, alpha=0.85)
        ax.axvline(ratios.mean(), color="#d97706", linestyle="--", linewidth=1.2, label=f"Mean Ratio: {ratios.mean()*100:.1f}%")
        ax.set_xlabel("Idle-to-Connection Ratio")
        ax.set_ylabel("Frequency")
        ax.legend(facecolor="#162032", edgecolor="#1e293b", labelcolor="#f1f5f9")
        st.pyplot(fig)
        plt.close()
        st.markdown(
            """
                <p class="figure-caption-text">
                    On average, 41.7% of total plug-in duration is spent idle, providing a substantial operational buffer for smart charging modulation.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Numbered Section 03: Site-Level Managed Charging Opportunities
    st.markdown(
        """
        <div class="section-head">
            <span class="section-number">03</span>
            <h2>Site-Level Managed Charging Strategies</h2>
            <span class="section-note">OPERATIONAL RECOMMENDATIONS</span>
        </div>
        <p class="lead">
            Translating empirical findings into actionable facility-level smart charging policies.
        </p>
        <div class="questions-grid">
            <article class="question-card">
                <span>STRATEGY 01</span>
                <h3>Morning Peak Shaving</h3>
                <p>Stagger charging initiation across the 08:00–10:00 morning arrival rush to avoid coincident peak demand spikes that reach 22.45 kWh/hr.</p>
            </article>
            <article class="question-card">
                <span>STRATEGY 02</span>
                <h3>Dwell Buffer Modulation</h3>
                <p>Leverage the 1.30-hour median idle dwell buffer (41.7% idle ratio) to curtail or throttle charging without impacting driver departure SOC.</p>
            </article>
            <article class="question-card">
                <span>STRATEGY 03</span>
                <h3>Dynamic Capacity Allocation</h3>
                <p>Forecasting models under-predict acute multi-vehicle bursts; deploy dynamic real-time current throttling instead of purely deterministic schedules.</p>
            </article>
            <article class="question-card">
                <span>STRATEGY 04</span>
                <h3>Turnaround & Idle Pricing</h3>
                <p>Consensus anomaly detection identifies extreme dwell times (>20h); implement progressive idle fees to improve port turnaround efficiency.</p>
            </article>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# EDITORIAL SITE FOOTER
# -----------------------------------------------------------------------------
st.markdown(
    """
    <footer class="site-footer">
        <div>
            <strong>EV Charging Analytics</strong> · Research Archive (2024–2026 Presentation Horizon)
        </div>
        <div>
            Caltech Adaptive Charging Network (ACN-Data Garage 0039) · 5,000 Verified Sessions (2020–2021)
        </div>
    </footer>
    """,
    unsafe_allow_html=True,
)
