"""Plain-language interpretations and actionable banking recommendations."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .i18n import feature_label, format_number, model_label, t


def _pick(data: pd.DataFrame, group: str, terms: tuple[str, ...]) -> pd.DataFrame:
    if data.empty:
        return data
    subset = data[data["group"] == group]
    pattern = "|".join(terms)
    return subset[subset["metric_english"].str.lower().str.contains(pattern, na=False) | subset["metric"].str.lower().str.contains(pattern, na=False)].copy()


def trend_sentence(data: pd.DataFrame, group: str, terms: tuple[str, ...], label: str, locale: str | None = None) -> str:
    subset = _pick(data, group, terms).dropna(subset=["date", "value"]).sort_values("date")
    if len(subset) < 2:
        return t("trend_not_enough", locale, label=label)
    first = float(subset.iloc[0]["value"])
    last = float(subset.iloc[-1]["value"])
    change = last - first
    pct = (change / abs(first) * 100) if abs(first) > 1e-9 else np.nan
    direction = t("direction_increased" if change >= 0 else "direction_decreased", locale)
    quarter = t("quarter_short", locale)
    return t("insight_trend", locale, label=label, direction=direction, start=format_number(first, 0, locale), end=format_number(last, 0, locale), first=f"{subset.iloc[0]['date']:%Y} {quarter}{subset.iloc[0]['date'].quarter}", last=f"{subset.iloc[-1]['date']:%Y} {quarter}{subset.iloc[-1]['date'].quarter}")


def recommendations(data: pd.DataFrame, model_result: dict[str, Any], anomaly_result: dict[str, Any], segment_result: dict[str, Any], locale: str | None = None) -> list[str]:
    """Return 4-6 recommendations grounded in the workbook and model outputs."""

    items: list[str] = []
    assets = _pick(data, "Balance sheet", ("total assets", "gjithsej pasurit"))
    deposits = _pick(data, "Balance sheet", ("customer deposits", "depozitat e klient"))
    profit = _pick(data, "Income statement", ("net profit", "fitimi"))
    if not assets.empty and not deposits.empty:
        aligned = assets.groupby("date")["value"].mean().to_frame("assets").join(deposits.groupby("date")["value"].mean().to_frame("deposits"), how="inner").dropna()
        if len(aligned) >= 2:
            latest = aligned.iloc[-1]
            ratio = latest["deposits"] / latest["assets"] if latest["assets"] else np.nan
            items.append(t("recommend_funding", locale, ratio=f"{ratio:.1%}"))
    if not profit.empty:
        recent = profit.dropna(subset=["value"]).sort_values("date").tail(4)
        if len(recent) >= 2:
            volatility = recent["value"].std(ddof=1)
            items.append(t("recommend_earnings", locale, volatility=format_number(volatility, 0, locale)))
    if model_result.get("available"):
        metrics = model_result["metrics"]
        best = metrics.loc[metrics["model"] == model_result["best_model"]].iloc[0]
        baseline = metrics.loc[metrics["model"] == "Baseline (training mean)"].iloc[0]
        improvement = (baseline["RMSE"] - best["RMSE"]) / baseline["RMSE"] * 100 if baseline["RMSE"] else 0
        items.append(t("recommend_model", locale, model=model_label(model_result["best_model"], locale), improvement=f"{improvement:.1f}"))
        if not model_result["importance"].empty:
            top = model_result["importance"].iloc[0]["feature"].replace("_", " ")
            items.append(t("recommend_driver", locale, driver=feature_label(top, locale)))
    if anomaly_result.get("available"):
        count = int(anomaly_result["result"]["anomaly"].sum())
        items.append(t("recommend_anomaly", locale, count=count))
    if segment_result.get("available"):
        items.append(t("recommend_segments", locale, k=segment_result["best_k"]))
    return items[:6]
