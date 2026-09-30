"""Brand system, CSS injection, and small UI helpers for the dashboard."""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

import streamlit as st

from utils.i18n import t


# Keep the palette in Python as the single source used by Plotly and UI helpers.
BRAND_COLORS = {
    "primary": "#8E1EA2",
    "secondary": "#C654C3",
    "accent": "#ED96D7",
    "highlight": "#FFC0DE",
    "plum_950": "#12041A",
    "plum_900": "#1B0724",
    "plum_800": "#260B32",
    "text": "#FFF7FD",
    "text_soft": "#F1D8EC",
    "muted": "#D0B6D0",
}
BRAND_COLORWAY = [
    BRAND_COLORS["primary"],
    BRAND_COLORS["secondary"],
    BRAND_COLORS["accent"],
    BRAND_COLORS["highlight"],
    "#A93CB0",
    "#D978D0",
    "#F4A9DE",
]
BRAND_CONTINUOUS_SCALE = [
    [0.0, BRAND_COLORS["primary"]],
    [0.33, BRAND_COLORS["secondary"]],
    [0.66, BRAND_COLORS["accent"]],
    [1.0, BRAND_COLORS["highlight"]],
]

STYLE_PATH = Path(__file__).resolve().parents[1] / "assets" / "style.css"


def _data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    mime = "image/svg+xml" if path.suffix.lower() == ".svg" else "image/png"
    return f"data:{mime};base64,{encoded}"


def inject_css() -> None:
    """Apply the complete visual system once without changing app behavior."""

    css = STYLE_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_logo(path: str | Path, width: int = 230, alt: str = "Project logo") -> None:
    """Render a local logo as an embedded image for cloud-safe relative loading."""

    uri = _data_uri(Path(path))
    if uri:
        st.markdown(
            f'<div class="sidebar-logo-wrap"><img src="{uri}" width="{width}" alt="{html.escape(alt)}" /></div>',
            unsafe_allow_html=True,
        )


def render_hero(app_logo: str | Path, workbook_name: str, filtered_count: int, locale: str = "en") -> None:
    """Render the branded hero with the application mark."""

    locale = st.session_state.get("locale", locale)
    app_uri = _data_uri(Path(app_logo))
    app_mark = f'<img src="{app_uri}" alt="Sales Inventory Analytics logo" />' if app_uri else ""
    safe_workbook = html.escape(workbook_name)
    st.markdown(
        f"""
        <section class="hero reveal reveal-hero">
          <div class="hero-topline">
            <div class="app-mark">
              <div class="app-logo-frame">{app_mark}</div>
              <div class="app-brand-copy">
                <div class="app-name">SALES / INVENTORY / ANALYTICS</div>
                <div class="app-subname">{t("Decision intelligence workspace", locale)}</div>
              </div>
            </div>
            <div class="app-mark app-mark-code">
              <span class="app-mark-label">SIA / 01</span>
            </div>
          </div>
          <div class="hero-copy">
            <div class="eyebrow"><span class="live-dot"></span> {t("Independent banking analytics portfolio project", locale)}</div>
            <h1>Sales-Inventory <span>Analytics</span></h1>
            <p class="hero-subtitle">Quarterly intelligence and predictive modelling from the supplied TEB open-data workbook. Explore financial health, quality controls, model performance, anomalies, and practical decision support in one transparent workspace.</p>
            <div class="hero-badges">
              <span class="badge">{t("Data Science Internship", locale)}</span>
              <span class="badge">{t("TEB Open Data", locale)}</span>
              <span class="badge">{t("ML + Analytics", locale)}</span>
            </div>
            <div class="hero-meta"><span>{t("Source workbook", locale)}: {safe_workbook}</span><span class="meta-separator">•</span><span>{filtered_count:,} {t("filtered observations", locale)}</span></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


_KPI_ICONS = {
    "Latest period": "◷",
    "Observed quarters": "◫",
    "Total assets": "◈",
    "Net profit": "↗",
    "Source sheets": "▦",
    "Clean records": "✓",
    "Missing cells": "⌁",
    "Outliers flagged": "⚡",
    "Best model": "✦",
    "Held-out RMSE": "⌁",
    "Held-out R²": "R²",
    "Vs baseline": "↗",
}


def kpi(label: str, value: str, help_text: str = "") -> None:
    icon = _KPI_ICONS.get(label, "✦")
    locale = st.session_state.get("locale", "en")
    label_text = t(label, locale)
    help_text = t(help_text, locale)
    numeric_match = re.fullmatch(r"(?P<prefix>[+-]?)(?P<number>\d[\d,]*)", str(value).strip())
    if numeric_match:
        target = int(numeric_match.group("number").replace(",", ""))
        value_markup = f'<div class="kpi-value kpi-count" style="--kpi-target:{target};" data-prefix="{numeric_match.group("prefix")}" aria-label="{html.escape(str(value))}">{html.escape(str(value))}</div>'
    else:
        value_markup = f'<div class="kpi-value" data-value="{html.escape(str(value))}">{html.escape(str(value))}</div>'
    st.markdown(
        f"""
        <div class="kpi-card reveal reveal-kpi">
          <div class="kpi-top"><span class="kpi-icon">{icon}</span><span class="kpi-label">{html.escape(label_text)}</span><span class="kpi-spark"></span></div>
          {value_markup}
          <div class="kpi-help">{html.escape(help_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight(text: str) -> None:
    st.markdown(f'<div class="insight reveal">{html.escape(text)}</div>', unsafe_allow_html=True)
