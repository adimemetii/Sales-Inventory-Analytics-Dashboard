"""Plotly chart factory with one coherent fintech visual language."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


COLORS = {
    "deep": "#0b3d3a",
    "teal": "#0f766e",
    "mint": "#8bd4c8",
    "gold": "#f4c95d",
    "coral": "#d65a5a",
    "blue": "#3f7cac",
    "ink": "#12312f",
    "muted": "#627875",
    "surface": "#ffffff",
}


def _template() -> go.layout.Template:
    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"family": "Inter, Arial, sans-serif", "color": COLORS["ink"]},
            colorway=[COLORS["teal"], COLORS["gold"], COLORS["blue"], COLORS["coral"], COLORS["deep"], COLORS["mint"]],
            margin={"l": 36, "r": 22, "t": 58, "b": 36},
            hoverlabel={"bgcolor": COLORS["deep"], "font": {"color": "white"}},
            xaxis={"showgrid": False, "zeroline": False, "linecolor": "#d7e5e2"},
            yaxis={"showgrid": True, "gridcolor": "#e8f0ee", "zeroline": False},
            legend={"orientation": "h", "y": 1.02, "x": 0},
        )
    )


FINTECH_TEMPLATE = _template()


def empty_figure(title: str, message: str = "Not enough data after the current filters.") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(template=FINTECH_TEMPLATE, title=title, height=350)
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font={"color": COLORS["muted"], "size": 14})
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
    fig = px.line(subset, x="date", y="value", markers=True, title=title, labels={"value": "Reported value", "date": "Quarter"})
    fig.update_traces(line={"color": COLORS["teal"], "width": 3}, marker={"color": COLORS["gold"], "size": 8}, hovertemplate=f"{label}<br>%{{x|%Y Q%q}}<br>Value: %{{y:{value_format}}}<extra></extra>")
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
    fig = px.line(subset, x="date", y="value", color="metric_english", markers=True, title=title, labels={"metric_english": "Metric", "value": "Reported value"})
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
    fig = px.bar(latest, x="value", y="metric_english", orientation="h", title=f"{title} ({latest_date:%Y Q}{latest_date.quarter})", labels={"value": "Reported value", "metric_english": "Metric"}, color="value", color_continuous_scale=[COLORS["mint"], COLORS["teal"]])
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, height=420)
    return fig


def income_composition(data: pd.DataFrame, title: str = "Income statement composition") -> go.Figure:
    subset = data[data["group"] == "Income statement"].dropna(subset=["date", "value"]).copy()
    if subset.empty:
        return empty_figure(title)
    latest_date = subset["date"].max()
    latest = subset[subset["date"] == latest_date].groupby("metric_english", as_index=False)["value"].mean()
    latest["absolute"] = latest["value"].abs()
    latest = latest.nlargest(8, "absolute")
    fig = px.bar(latest.sort_values("value"), x="value", y="metric_english", orientation="h", color="value", color_continuous_scale=[COLORS["coral"], COLORS["mint"], COLORS["teal"]], title=f"{title} - latest period", labels={"value": "Reported value", "metric_english": "Metric"})
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
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale=[COLORS["coral"], "#ffffff", COLORS["teal"]], zmin=-1, zmax=1, title=title, aspect="auto")
    fig.update_layout(template=FINTECH_TEMPLATE, height=560)
    return fig


def distribution(data: pd.DataFrame, group: str, title: str) -> go.Figure:
    subset = data[data["group"] == group].dropna(subset=["value"]).copy()
    if subset.empty:
        return empty_figure(title)
    fig = px.histogram(subset, x="value", color="metric_english", marginal="box", opacity=0.75, title=title, labels={"value": "Reported value"})
    fig.update_layout(template=FINTECH_TEMPLATE, barmode="overlay", height=430)
    return fig


def model_comparison(metrics: pd.DataFrame) -> go.Figure:
    if metrics is None or metrics.empty:
        return empty_figure("Held-out model comparison")
    plot = metrics.sort_values("RMSE", ascending=True)
    fig = px.bar(plot, x="model", y="RMSE", color="model", title="Held-out RMSE: lower is better", labels={"RMSE": "RMSE", "model": "Model"})
    fig.update_layout(template=FINTECH_TEMPLATE, showlegend=False, height=390)
    return fig


def prediction_chart(predictions: pd.DataFrame, title: str = "Actual vs predicted on held-out quarters") -> go.Figure:
    if predictions is None or predictions.empty:
        return empty_figure(title)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["upper"], line={"width": 0}, showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["lower"], fill="tonexty", fillcolor="rgba(15,118,110,.12)", line={"width": 0}, name="Approx. 95% interval", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["actual"], mode="lines+markers", name="Actual", line={"color": COLORS["deep"], "width": 3}, marker={"color": COLORS["gold"], "size": 8}))
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["best_prediction"], mode="lines+markers", name="Best model", line={"color": COLORS["teal"], "width": 3, "dash": "dot"}, marker={"color": COLORS["teal"], "size": 7}))
    fig.update_layout(template=FINTECH_TEMPLATE, title=title, height=430, yaxis_title="Net profit (reported units)", xaxis_title="Quarter")
    return fig


def residual_chart(predictions: pd.DataFrame) -> go.Figure:
    if predictions is None or predictions.empty:
        return empty_figure("Residual diagnostics")
    fig = px.bar(predictions, x="date", y="residual", color="residual", color_continuous_scale=[COLORS["coral"], "#ffffff", COLORS["teal"]], title="Residuals by held-out quarter", labels={"residual": "Actual - predicted"})
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, height=360)
    return fig


def feature_importance(importance: pd.DataFrame) -> go.Figure:
    if importance is None or importance.empty:
        return empty_figure("Feature importance")
    plot = importance.head(12).sort_values("importance")
    fig = px.bar(plot, x="importance", y="feature", orientation="h", title="Top model drivers", labels={"importance": "Absolute contribution / tree importance", "feature": "Feature"}, color="importance", color_continuous_scale=[COLORS["mint"], COLORS["teal"]])
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, height=450)
    return fig


def anomaly_scatter(anomalies: pd.DataFrame) -> go.Figure:
    if anomalies is None or anomalies.empty:
        return empty_figure("Anomaly timeline")
    value_cols = [c for c in anomalies.columns if c not in {"date", "anomaly", "anomaly_score"}]
    if not value_cols:
        return empty_figure("Anomaly timeline")
    y_col = value_cols[0]
    fig = px.scatter(anomalies, x="date", y=y_col, color="anomaly", size="anomaly_score", symbol="anomaly", title=f"Anomaly flags - {y_col.split('__')[-1].replace('_', ' ').title()}", labels={y_col: "Reported value", "anomaly": "Flagged"}, color_discrete_map={True: COLORS["coral"], False: COLORS["teal"]})
    fig.update_layout(template=FINTECH_TEMPLATE, height=410)
    return fig


def segment_timeline(segments: pd.DataFrame) -> go.Figure:
    if segments is None or segments.empty:
        return empty_figure("Segment timeline")
    fig = px.scatter(segments, x="date", y="segment", color="segment", title="Financial-period segments", labels={"segment": "Cluster"})
    fig.update_traces(marker={"size": 13})
    fig.update_layout(template=FINTECH_TEMPLATE, height=360, yaxis={"categoryorder": "category ascending"})
    return fig


def quality_chart(quality: pd.DataFrame) -> go.Figure:
    if quality is None or quality.empty:
        return empty_figure("Data-quality summary")
    chart = quality.melt(id_vars=["sheet"], value_vars=["missing_cells_before", "duplicates_removed", "outliers_found"], var_name="check", value_name="count")
    fig = px.bar(chart, x="sheet", y="count", color="check", barmode="group", title="Quality checks by source sheet", labels={"count": "Count", "sheet": "Source sheet"})
    fig.update_layout(template=FINTECH_TEMPLATE, height=400, xaxis_tickangle=-25)
    return fig

