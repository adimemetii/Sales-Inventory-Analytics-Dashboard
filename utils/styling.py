"""Custom CSS and small UI helpers for the Streamlit dashboard."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


def _data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    mime = "image/svg+xml" if path.suffix.lower() == ".svg" else "image/png"
    return f"data:{mime};base64,{encoded}"


def inject_css() -> None:
    """Apply the dashboard visual system without changing Streamlit runtime behavior."""

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        :root { --deep:#0b3d3a; --teal:#0f766e; --mint:#8bd4c8; --gold:#f4c95d; --ink:#12312f; --muted:#627875; --surface:#ffffff; }
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background: linear-gradient(180deg, #f4f8f7 0%, #eef5f3 100%); color: var(--ink); }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #0b3d3a 0%, #0f5b54 100%); color: #f7fffd; }
        [data-testid="stSidebar"] * { color: #f7fffd !important; }
        [data-testid="stSidebar"] [data-baseweb="select"] > div, [data-testid="stSidebar"] input { background: rgba(255,255,255,.14) !important; border: 1px solid rgba(255,255,255,.25) !important; }
        .hero { padding: 28px 32px; border-radius: 26px; background: radial-gradient(circle at 85% 10%, rgba(244,201,93,.48), transparent 28%), linear-gradient(135deg, #0b3d3a 0%, #0f766e 70%, #1b958a 100%); box-shadow: 0 16px 40px rgba(11,61,58,.18); color: white; margin-bottom: 22px; }
        .hero h1 { font-size: clamp(28px, 4vw, 48px); line-height: 1.05; margin: 8px 0 10px; letter-spacing: -1.8px; }
        .hero p { max-width: 850px; color: #d5f2eb; margin: 0; font-size: 15px; }
        .eyebrow { font-size: 11px; font-weight: 800; letter-spacing: 2.2px; text-transform: uppercase; color: var(--gold); }
        .kpi-card { background: rgba(255,255,255,.78); border: 1px solid rgba(15,118,110,.13); border-radius: 18px; padding: 18px 20px; box-shadow: 0 10px 28px rgba(11,61,58,.07); min-height: 116px; }
        .kpi-label { color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .7px; }
        .kpi-value { color: var(--deep); font-size: 28px; font-weight: 800; margin: 6px 0 2px; }
        .kpi-help { color: var(--muted); font-size: 12px; }
        .section-card { background: rgba(255,255,255,.70); border: 1px solid rgba(15,118,110,.10); border-radius: 20px; padding: 18px 22px; box-shadow: 0 10px 28px rgba(11,61,58,.05); }
        .insight { border-left: 4px solid var(--gold); background: #fffdf4; padding: 12px 15px; border-radius: 0 13px 13px 0; margin: 8px 0; color: var(--ink); }
        .badge { display: inline-block; padding: 4px 9px; border-radius: 999px; background: #d5f2eb; color: var(--deep); font-size: 11px; font-weight: 800; }
        .fallback-table { overflow-x:auto; border:1px solid #dce9e6; border-radius:12px; background:#fff; margin:6px 0 16px; }
        .fallback-table table { width:100%; border-collapse:collapse; font-size:12px; }
        .fallback-table th { background:#e8f1ef; color:var(--deep); text-align:left; padding:8px; }
        .fallback-table td { border-top:1px solid #edf3f1; padding:8px; color:var(--ink); }
        div[data-testid="stMetric"] { background: rgba(255,255,255,.72); border: 1px solid rgba(15,118,110,.10); border-radius: 17px; padding: 12px 16px; box-shadow: 0 8px 22px rgba(11,61,58,.05); }
        div[data-testid="stTabs"] button { font-weight: 700; color: var(--muted); }
        div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--teal); border-bottom-color: var(--gold); }
        #MainMenu, footer { visibility: hidden; }
        .footer-note { text-align:center; color: var(--muted); font-size: 11px; padding: 22px 0 10px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_logo(path: str | Path, width: int = 230) -> None:
    """Render a local project logo as an embedded image."""

    uri = _data_uri(Path(path))
    if uri:
        st.markdown(f'<img src="{uri}" width="{width}" alt="Project logo" />', unsafe_allow_html=True)


def kpi(label: str, value: str, help_text: str = "") -> None:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-help">{help_text}</div></div>',
        unsafe_allow_html=True,
    )


def insight(text: str) -> None:
    st.markdown(f'<div class="insight">{text}</div>', unsafe_allow_html=True)
