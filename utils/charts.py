"""Plotly chart factory with one coherent fintech visual language."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.i18n import feature_label, metric_label, model_label, t
from utils.styling import BRAND_COLORS, BRAND_COLORWAY, BRAND_CONTINUOUS_SCALE


COLORS = {
    "deep": BRAND_COLORS["navy_950"],
    "plum": BRAND_COLORS["navy_900"],
    "teal": BRAND_COLORS["secondary"],
    "mint": BRAND_COLORS["accent"],
    "gold": BRAND_COLORS["highlight"],
    "coral": BRAND_COLORS["primary"],
    "blue": BRAND_COLORS["secondary"],
    "ink": BRAND_COLORS["text"],
    "muted": BRAND_COLORS["muted"],
    "surface": BRAND_COLORS["navy_900"],
}


def _template() -> go.layout.Template:
    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor=BRAND_COLORS["navy_950"],
            plot_bgcolor=BRAND_COLORS["navy_900"],
            font={"family": "Inter, Arial, sans-serif", "color": BRAND_COLORS["text"]},
            colorway=BRAND_COLORWAY,
            margin={"l": 36, "r": 22, "t": 58, "b": 36},
            hoverlabel={"bgcolor": BRAND_COLORS["navy_800"], "bordercolor": BRAND_COLORS["accent"], "font": {"color": BRAND_COLORS["text"]}},
            xaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,.12)", "zeroline": False, "linecolor": "rgba(234,242,255,.3)", "tickfont": {"color": BRAND_COLORS["text_soft"]}},
            yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,.12)", "zeroline": False, "tickfont": {"color": BRAND_COLORS["text_soft"]}},
            legend={"orientation": "h", "y": 1.02, "x": 0, "font": {"color": BRAND_COLORS["text"]}},
            coloraxis={"colorbar": {"tickfont": {"color": BRAND_COLORS["text_soft"]}}},
        )
    )


FINTECH_TEMPLATE = _template()


def empty_figure(title: str, message: str = "no_data_chart") -> go.Figure:
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
    fig = px.line(
        subset,
        x="date",
        y="value",
        markers=True,
        title=t(title),
        labels={"value": t("reported_value"), "date": t("quarter")},
        template=FINTECH_TEMPLATE,
    )
    fig.update_traces(line={"color": BRAND_COLORS["secondary"], "width": 3}, marker={"color": BRAND_COLORS["highlight"], "size": 8}, hovertemplate=f"{display_label}<br>%{{x|%Y-%m-%d}}<br>{t('quarter')}: %{{x|%Y}} {t('quarter_short')}<br>{t('value')}: %{{y:{value_format}}}<extra></extra>")
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
    fig = px.line(
        subset,
        x="date",
        y="value",
        color="metric_display",
        color_discrete_sequence=BRAND_COLORWAY,
        markers=True,
        title=t(title),
        labels={"metric_display": t("metric"), "value": t("reported_value")},
        template=FINTECH_TEMPLATE,
    )
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
    fig = px.bar(
        latest,
        x="value",
        y="metric_display",
        orientation="h",
        title=f"{t(title)} ({latest_date:%Y} {t('quarter_short')}{latest_date.quarter})",
        labels={"value": t("reported_value"), "metric_display": t("metric")},
        color="value",
        color_continuous_scale=BRAND_CONTINUOUS_SCALE,
        template=FINTECH_TEMPLATE,
    )
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, coloraxis={"colorscale": BRAND_CONTINUOUS_SCALE}, height=420)
    return fig


def income_composition(data: pd.DataFrame, title: str = "overview_chart_income") -> go.Figure:
    subset = data[data["group"] == "Income statement"].dropna(subset=["date", "value"]).copy()
    if subset.empty:
        return empty_figure(title)
    latest_date = subset["date"].max()
    latest = subset[subset["date"] == latest_date].groupby("metric_english", as_index=False)["value"].mean()
    latest["absolute"] = latest["value"].abs()
    latest = latest.nlargest(8, "absolute")
    latest = latest.sort_values("value").copy()
    latest["metric_display"] = latest["metric_english"].map(metric_label)
    fig = px.bar(
        latest,
        x="value",
        y="metric_display",
        orientation="h",
        color="value",
        color_continuous_scale=BRAND_CONTINUOUS_SCALE,
        title=f"{t(title)} - {t('latest_period_lower').lower()}",
        labels={"value": t("reported_value"), "metric_display": t("metric")},
        template=FINTECH_TEMPLATE,
    )
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, height=460)
    return fig


def correlation_heatmap(data: pd.DataFrame, title: str = "eda_chart_correlation") -> go.Figure:
    subset = data.dropna(subset=["date", "value"]).copy()
    if subset.empty:
        return empty_figure(title)
    pivot = subset.pivot_table(index="date", columns="metric_english", values="value", aggfunc="mean")
    valid = pivot.notna().sum().sort_values(ascending=False).head(12).index
    corr = pivot[valid].corr(min_periods=4)
    if corr.empty:
        return empty_figure(title)
    corr = corr.rename(columns=metric_label, index=metric_label)
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale=BRAND_CONTINUOUS_SCALE,
        zmin=-1,
        zmax=1,
        title=t(title),
        aspect="auto",
        template=FINTECH_TEMPLATE,
    )
    fig.update_layout(template=FINTECH_TEMPLATE, height=560)
    return fig


def distribution(data: pd.DataFrame, group: str, title: str) -> go.Figure:
    subset = data[data["group"] == group].dropna(subset=["value"]).copy()
    if subset.empty:
        return empty_figure(title)
    subset = subset.copy()
    subset["metric_display"] = subset["metric_english"].map(metric_label)
    fig = px.histogram(
        subset,
        x="value",
        color="metric_display",
        color_discrete_sequence=BRAND_COLORWAY,
        marginal="box",
        opacity=0.75,
        title=t(title),
        labels={"value": t("reported_value"), "metric_display": t("metric")},
        template=FINTECH_TEMPLATE,
    )
    fig.update_layout(template=FINTECH_TEMPLATE, barmode="overlay", height=430)
    return fig


def model_comparison(metrics: pd.DataFrame) -> go.Figure:
    if metrics is None or metrics.empty:
        return empty_figure("chart_model_comparison")
    plot = metrics.sort_values("RMSE", ascending=True).copy()
    plot["model_display"] = plot["model"].map(model_label)
    fig = px.bar(
        plot,
        x="model_display",
        y="RMSE",
        color="model_display",
        color_discrete_sequence=BRAND_COLORWAY,
        title=t("chart_model_rmse"),
        labels={"RMSE": t("rmse_label"), "model_display": t("model")},
        template=FINTECH_TEMPLATE,
    )
    fig.update_layout(template=FINTECH_TEMPLATE, showlegend=False, height=390)
    return fig


def prediction_chart(predictions: pd.DataFrame, title: str = "chart_predictions") -> go.Figure:
    if predictions is None or predictions.empty:
        return empty_figure(title)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["upper"], line={"width": 0}, showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["lower"], fill="tonexty", fillcolor="rgba(73,164,187,.22)", line={"width": 0}, name=t("approx_interval"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["actual"], mode="lines+markers", name=t("actual"), line={"color": BRAND_COLORS["highlight"], "width": 3}, marker={"color": BRAND_COLORS["accent"], "size": 8}))
    fig.add_trace(go.Scatter(x=predictions["date"], y=predictions["best_prediction"], mode="lines+markers", name=t("best_model_trace"), line={"color": BRAND_COLORS["secondary"], "width": 3, "dash": "dot"}, marker={"color": BRAND_COLORS["secondary"], "size": 7}))
    fig.update_layout(template=FINTECH_TEMPLATE, title=t(title), height=430, yaxis_title=t("kpi_net_profit"), xaxis_title=t("quarter"))
    return fig


def residual_chart(predictions: pd.DataFrame) -> go.Figure:
    if predictions is None or predictions.empty:
        return empty_figure("chart_residuals")
    fig = px.bar(
        predictions,
        x="date",
        y="residual",
        color="residual",
        color_continuous_scale=BRAND_CONTINUOUS_SCALE,
        title=t("chart_residuals"),
        labels={"residual": t("actual_predicted")},
        template=FINTECH_TEMPLATE,
    )
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, height=360)
    return fig


def feature_importance(importance: pd.DataFrame) -> go.Figure:
    if importance is None or importance.empty:
        return empty_figure("chart_drivers")
    plot = importance.head(12).sort_values("importance").copy()
    plot["feature_display"] = plot["feature"].map(feature_label)
    fig = px.bar(
        plot,
        x="importance",
        y="feature_display",
        orientation="h",
        title=t("chart_drivers"),
        labels={"importance": t("value"), "feature_display": t("metric")},
        color="importance",
        color_continuous_scale=BRAND_CONTINUOUS_SCALE,
        template=FINTECH_TEMPLATE,
    )
    fig.update_layout(template=FINTECH_TEMPLATE, coloraxis_showscale=False, height=450)
    return fig


def anomaly_scatter(anomalies: pd.DataFrame) -> go.Figure:
    if anomalies is None or anomalies.empty:
        return empty_figure("chart_anomaly")
    value_cols = [c for c in anomalies.columns if c not in {"date", "anomaly", "anomaly_score"}]
    if not value_cols:
        return empty_figure("chart_anomaly")
    y_col = value_cols[0]
    fig = px.scatter(
        anomalies,
        x="date",
        y=y_col,
        color="anomaly",
        size="anomaly_score",
        symbol="anomaly",
        title=f"{t('chart_anomaly')} - {metric_label(y_col.split('__')[-1].replace('_', ' '))}",
        labels={y_col: t("reported_value"), "anomaly": t("flagged")},
        color_discrete_map={True: BRAND_COLORS["accent"], False: BRAND_COLORS["primary"]},
        template=FINTECH_TEMPLATE,
    )
    fig.update_layout(template=FINTECH_TEMPLATE, height=410)
    return fig


def segment_timeline(segments: pd.DataFrame) -> go.Figure:
    if segments is None or segments.empty:
        return empty_figure("chart_segment")
    fig = px.scatter(
        segments,
        x="date",
        y="segment",
        color="segment",
        color_discrete_sequence=BRAND_COLORWAY,
        title=t("chart_segment"),
        labels={"segment": t("cluster")},
        template=FINTECH_TEMPLATE,
    )
    fig.update_traces(marker={"size": 13})
    fig.update_layout(template=FINTECH_TEMPLATE, height=360, yaxis={"categoryorder": "category ascending"})
    return fig


def quality_chart(quality: pd.DataFrame) -> go.Figure:
    if quality is None or quality.empty:
        return empty_figure("chart_data_quality")
    chart = quality.melt(id_vars=["sheet"], value_vars=["missing_cells_before", "duplicates_removed", "outliers_found"], var_name="check", value_name="count")
    fig = px.bar(
        chart,
        x="sheet",
        y="count",
        color="check",
        color_discrete_sequence=BRAND_COLORWAY,
        barmode="group",
        title=t("quality_chart"),
        labels={"count": t("value"), "sheet": t("source_sheets")},
        template=FINTECH_TEMPLATE,
    )
    fig.update_layout(template=FINTECH_TEMPLATE, height=400, xaxis_tickangle=-25)
    return fig



