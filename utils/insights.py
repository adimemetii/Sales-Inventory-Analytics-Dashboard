"""Plain-language interpretations and actionable banking recommendations."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _pick(data: pd.DataFrame, group: str, terms: tuple[str, ...]) -> pd.DataFrame:
    if data.empty:
        return data
    subset = data[data["group"] == group]
    pattern = "|".join(terms)
    return subset[subset["metric_english"].str.lower().str.contains(pattern, na=False) | subset["metric"].str.lower().str.contains(pattern, na=False)].copy()


def trend_sentence(data: pd.DataFrame, group: str, terms: tuple[str, ...], label: str) -> str:
    subset = _pick(data, group, terms).dropna(subset=["date", "value"]).sort_values("date")
    if len(subset) < 2:
        return f"{label}: not enough observations after the current filters."
    first = float(subset.iloc[0]["value"])
    last = float(subset.iloc[-1]["value"])
    change = last - first
    pct = (change / abs(first) * 100) if abs(first) > 1e-9 else np.nan
    direction = "increased" if change >= 0 else "decreased"
    pct_text = f" ({pct:.1f}%)" if np.isfinite(pct) else ""
    return f"{label} {direction} from {first:,.0f} to {last:,.0f} reported units{pct_text} between {subset.iloc[0]['date']:%Y Q}{subset.iloc[0]['date'].quarter} and {subset.iloc[-1]['date']:%Y Q}{subset.iloc[-1]['date'].quarter}."


def recommendations(data: pd.DataFrame, model_result: dict[str, Any], anomaly_result: dict[str, Any], segment_result: dict[str, Any]) -> list[str]:
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
            items.append(f"Monitor funding concentration: customer deposits are approximately {ratio:.1%} of total assets in the latest aligned period; use this ratio with liquidity limits and stress scenarios.")
    if not profit.empty:
        recent = profit.dropna(subset=["value"]).sort_values("date").tail(4)
        if len(recent) >= 2:
            volatility = recent["value"].std(ddof=1)
            items.append(f"Use a rolling earnings review: the latest four observed quarters have net-profit standard deviation of about {volatility:,.0f} reported units, so management should separate recurring trends from one-off movements.")
    if model_result.get("available"):
        metrics = model_result["metrics"]
        best = metrics.loc[metrics["model"] == model_result["best_model"]].iloc[0]
        baseline = metrics.loc[metrics["model"] == "Baseline (training mean)"].iloc[0]
        improvement = (baseline["RMSE"] - best["RMSE"]) / baseline["RMSE"] * 100 if baseline["RMSE"] else 0
        items.append(f"Use the {model_result['best_model']} as a planning signal, not an automated decision: it improves held-out RMSE versus the mean baseline by {improvement:.1f}% and should be refreshed as new quarters arrive.")
        if not model_result["importance"].empty:
            top = model_result["importance"].iloc[0]["feature"].replace("_", " ")
            items.append(f"Prioritise scenario monitoring for {top}; it is the strongest displayed model driver, but feature importance indicates association rather than causation.")
    if anomaly_result.get("available"):
        count = int(anomaly_result["result"]["anomaly"].sum())
        items.append(f"Route the {count} flagged quarter(s) to analyst review before using them in planning; Isolation Forest flags unusual combinations and does not prove fraud or data error.")
    if segment_result.get("available"):
        items.append(f"Use the {segment_result['best_k']} financial-period segments to compare operating regimes, then validate segment labels with a bank subject-matter expert before changing policy.")
    return items[:6]

