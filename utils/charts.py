"""Plotly chart factory with one coherent fintech visual language."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.i18n import metric_label, t
from utils.styling import BRAND_COLORS, BRAND_COLORWAY, BRAND_CONTINUOUS_SCALE


COLORS = {
    "deep": BRAND_COLORS["plum_950"],
    "plum": BRAND_COLORS["plum_900"],
    "teal": BRAND_COLORS["secondary"],
    "mint": BRAND_COLORS["accent"],
    "gold": BRAND_COLORS["highlight"],
    "coral": BRAND_COLORS["primary"],
    "blue": BRAND_COLORS["secondary"],
    "ink": BRAND_COLORS["text"],
    "muted": BRAND_COLORS["muted"],
    "surface": BRAND_COLORS["plum_900"],
}


def _template() -> go.layout.Template:
    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"family": "Inter, Arial, sans-serif", "color": BRAND_COLORS["text_soft"]},
            colorway=BRAND_COLORWAY,
            margin={"l": 36, "r": 22, "t": 58, "b": 36},
            hoverlabel={"bgcolor": BRAND_COLORS["plum_800"], "bordercolor": BRAND_COLORS["accent"], "font": {"color": BRAND_COLORS["text"]}},
            xaxis={"showgrid": False, "zeroline": False, "linecolor": "rgba(255,192,222,.22)", "tickfont": {"color": BRAND_COLORS["muted"]}},
            yaxis={"showgrid": True, "gridcolor": "rgba(255,192,222,.14)", "zeroline": False, "tickfont": {"color": BRAND_COLORS["muted"]}},
            legend={"orientation": "h", "y": 1.02, "x": 0, "font": {"color": BRAND_COLORS["text_soft"]}},
            transition={"duration": 780, "easing": "cubic-in-out"},
        )
    )


FINTECH_TEMPLATE = _template()


def empty_figure(title: str, message: str = "Not enough data after the current filters.") -> go.Figure:
    title = t(title)
    message = t(message)
    fig = go.Figure()
    fig.update_layout(template=FINTECH_TEMPLATE, title=title, height=350)
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font={"color": BRAND_COLORS["muted"], "size": 14})
    return fig


def _metric_subset(data: pd.DataFrame, terms: tuple[str, ...], group: str | None = None) -> pd.DataFrame:
    if data.empty:
        return data
    subset = data if group is None else data[data["group"] == group]
    pattern = "|".join(terms)
    return subset[subset["metric"].str.lower().str.contains(pattern, na=False) | subset["metric_english"].str.lower().str.contains(pattern, na=False)].copy()


def metric_line(data: pd.DataFrame, terms: tuple[str, ...], group: str, title: str, value_format: str = ",.0f") -> go.Figure:
    subset = _metric_subset(data, terms, group)
    if subset.empty:
        return empty_figure(title)
    subset = subset.dropna(subset=["date", "value"]).sort_values("date")
    label = subset["metric_english"].iloc[0]
    display_label = metric_label(label)
    fig = px.line(subset, x="date", y="value", markers=True, title=t(title), labels={"value": t("Reported value"), "date": t("Quarter")})
    fig.update_traces(line={"color": BRAND_COLORS["secondary"], "width": 3}, marker={"color": BRAND_COLORS["highlight"], "size": 8}, hovertemplate=f"{display_label}<br>%{{x|%Y Q%q}}<br>{t('Value')}: %{{y:{value_format}}}<extra></extra>")
    fig.update_layout(template=FINTECH_TEMPLATE)
    return fig


def multi_metric_lines(data: pd.DataFrame, group: str, terms: tuple[str, ...], title: str) -> go.Figure:
    subset = data[data["group"] == group].copy()
    if terms:
        pattern = "|".join(terms)
        subset = subset[subset["metric_english"].str.lower().str.contains(pattern, na=False) | subset["metric"].str.lower().str.contains(pattern, na=False)]
    if subset.empty:
        return empty_figure(title)
    subset = subset.dropna(subset=["date", "value"])
    subset = subset.copy()
    subset["metric_display"] = subset["metric_english"].map(metric_label)
    fig = px.line(subset, x="date", y="value", color="metric_display", markers=True, title=t(title), labels={"metric_display": t("Metric"), "value": t("Reported value")})
    fig.update_layout(template=FINTECH_TEMPLATE, height=430)
    return fig


def latest_rankings(data: pd.DataFrame, group: str, title: str, n: int = 10) -> go.Figure:
    subset = data[data["group"] == group].dropna(subset=["date", "value"]).copy()
    if subset.empty:
        return empty_figure(title)
    latest_date = subset["date"].max()
    latest = subset[subset["date"] == latest_date].groupby("metric_english", as_index=False)["value"].mean().nlargest(n, "value").sort_values("value")
    if latest.empty:
        return empty_figure(title)
    latest = latest.copy()
    latest["metric_display"] = latest["metric_english"].map(metric_label)
    fig = px.bar(latest, x="value", y="metric_display", orientation="h", title=f"{t(title)} ({latest_date:%Y Q}{latest_date.quarter})", labels={"value": t("Reported value"), "metric_display": t("Metric")}, color="value", color_continuous_scale=BRAND_CONTINUOUS_SCALE)
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, coloraxis={"colorscale": BRAND_CONTINUOUS_SCALE}, height=420)
    return fig


def income_composition(data: pd.DataFrame, title: str = "Income statement composition") -> go.Figure:
    subset = data[data["group"] == "Income statement"].dropna(subset=["date", "value"]).copy()
    if subset.empty:
        return empty_figure(title)
    latest_date = subset["date"].max()
    latest = subset[subset["date"] == latest_date].groupby("metric_english", as_index=False)["value"].mean()
    latest["absolute"] = latest["value"].abs()
    latest = latest.nlargest(8, "absolute")
    latest = latest.sort_values("value").copy()
    latest["metric_display"] = latest["metric_english"].map(metric_label)
    fig = px.bar(latest, x="value", y="metric_display", orientation="h", color="value", color_continuous_scale=BRAND_CONTINUOUS_SCALE, title=f"{t(title)} - {t('Latest period').lower()}", labels={"value": t("Reported value"), "metric_display": t("Metric")})
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, height=460)
    return fig


def correlation_heatmap(data: pd.DataFrame, title: str = "Correlation heatmap") -> go.Figure:
    subset = data.dropna(subset=["date", "value"]).copy()
    if subset.empty:
        return empty_figure(title)
    pivot = subset.pivot_table(index="date", columns="metric_english", values="value", aggfunc="mean")
    valid = pivot.notna().sum().sort_values(ascending=False).head(12).index
    corr = pivot[valid].corr(min_periods=4)
    if corr.empty:
        return empty_figure(title)
    corr = corr.rename(columns=metric_label, index=metric_label)
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale=BRAND_CONTINUOUS_SCALE, zmin=-1, zmax=1, title=t(title), aspect="auto")
    fig.update_layout(template=FINTECH_TEMPLATE, height=560)
    return fig


def distribution(data: pd.DataFrame, group: str, title: str) -> go.Figure:
    subset = data[data["group"] == group].dropna(subset=["value"]).copy()
    if subset.empty:
        return empty_figure(title)
    subset = subset.copy()
    subset["metric_display"] = subset["metric_english"].map(metric_label)
    fig = px.histogram(subset, x="value", color="metric_display", marginal="box", opacity=0.75, title=t(title), labels={"value": t("Reported value"), "metric_display": t("Metric")})
    fig.update_layout(template=FINTECH_TEMPLATE, barmode="overlay", height=430)
    return fig


def model_comparison(metrics: pd.DataFrame) -> go.Figure:
    if metrics is None or metrics.empty:
        return empty_figure("Held-out model comparison")
    plot = metrics.sort_values("RMSE", ascending=True)
    fig = px.bar(plot, x="model", y="RMSE", color="model", title=t("Held-out RMSE: lower is better"), labels={"RMSE": "RMSE", "model": t("Model")})
    fig.update_layout(template=FINTECH_TEMPLATE, showlegend=False, height=390)
    return fig


def prediction_chart(predictions: pd.DataFrame, title: str = "Actual vs predicted on held-out quarters") -> go.Figure:
    if predictions is None or predictions.empty:
        return empty_figure(title)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["upper"], line={"width": 0}, showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["lower"], fill="tonexty", fillcolor="rgba(198,84,195,.16)", line={"width": 0}, name=t("Approx. 95% interval"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["actual"], mode="lines+markers", name=t("Actual"), line={"color": BRAND_COLORS["highlight"], "width": 3}, marker={"color": BRAND_COLORS["accent"], "size": 8}))
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["best_prediction"], mode="lines+markers", name=t("Best model trace"), line={"color": BRAND_COLORS["secondary"], "width": 3, "dash": "dot"}, marker={"color": BRAND_COLORS["secondary"], "size": 7}))
    fig.update_layout(template=FINTECH_TEMPLATE, title=t(title), height=430, yaxis_title=t("Net profit"), xaxis_title=t("Quarter"))
    return fig


def residual_chart(predictions: pd.DataFrame) -> go.Figure:
    if predictions is None or predictions.empty:
        return empty_figure("Residual diagnostics")
    fig = px.bar(predictions, x="date", y="residual", color="residual", color_continuous_scale=BRAND_CONTINUOUS_SCALE, title=t("Residuals by held-out quarter"), labels={"residual": t("Actual - predicted")})
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, height=360)
    return fig


def feature_importance(importance: pd.DataFrame) -> go.Figure:
    if importance is None or importance.empty:
        return empty_figure("Feature importance")
    plot = importance.head(12).sort_values("importance")
    fig = px.bar(plot, x="importance", y="feature", orientation="h", title=t("Top model drivers"), labels={"importance": t("Value"), "feature": t("Metric")}, color="importance", color_continuous_scale=BRAND_CONTINUOUS_SCALE)
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, height=450)
    return fig


def anomaly_scatter(anomalies: pd.DataFrame) -> go.Figure:
    if anomalies is None or anomalies.empty:
        return empty_figure("Anomaly timeline")
    value_cols = [c for c in anomalies.columns if c not in {"date", "anomaly", "anomaly_score"}]
    if not value_cols:
        return empty_figure("Anomaly timeline")
    y_col = value_cols[0]
    fig = px.scatter(anomalies, x="date", y=y_col, color="anomaly", size="anomaly_score", symbol="anomaly", title=f"{t('Anomaly timeline')} - {metric_label(y_col.split('__')[-1].replace('_', ' '))}", labels={y_col: t("Reported value"), "anomaly": t("Flagged")}, color_discrete_map={True: BRAND_COLORS["accent"], False: BRAND_COLORS["primary"]})
    fig.update_layout(template=FINTECH_TEMPLATE, height=410)
    return fig


def segment_timeline(segments: pd.DataFrame) -> go.Figure:
    if segments is None or segments.empty:
        return empty_figure("Segment timeline")
    fig = px.scatter(segments, x="date", y="segment", color="segment", title=t("Financial-period segments"), labels={"segment": t("Cluster")})
    fig.update_traces(marker={"size": 13})
    fig.update_layout(template=FINTECH_TEMPLATE, height=360, yaxis={"categoryorder": "category ascending"})
    return fig


def quality_chart(quality: pd.DataFrame) -> go.Figure:
    if quality is None or quality.empty:
        return empty_figure("Data-quality summary")
    chart = quality.melt(id_vars=["sheet"], value_vars=["missing_cells_before", "duplicates_removed", "outliers_found"], var_name="check", value_name="count")
    fig = px.bar(chart, x="sheet", y="count", color="check", barmode="group", title=t("Quality checks by source sheet"), labels={"count": t("Value"), "sheet": t("Source sheets")})
    fig.update_layout(template=FINTECH_TEMPLATE, height=400, xaxis_tickangle=-25)
    return fig
