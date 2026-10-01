"""Reusable cleaning, feature-engineering, and statistical helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from .data_loader import metric_contains
from .i18n import format_number, t


def apply_filters(
    data: pd.DataFrame,
    selected_sheets: list[str] | None = None,
    selected_groups: list[str] | None = None,
    selected_years: list[int] | None = None,
    selected_metrics: list[str] | None = None,
) -> pd.DataFrame:
    """Apply sidebar filters without changing the source dataframe."""

    if data.empty:
        return data.copy()
    result = data.copy()
    if selected_sheets:
        result = result[result["sheet"].isin(selected_sheets)]
    if selected_groups:
        result = result[result["group"].isin(selected_groups)]
    if selected_years:
        result = result[result["year"].isin(selected_years)]
    if selected_metrics:
        result = result[result["metric"].isin(selected_metrics)]
    return result


def pivot_financial_data(data: pd.DataFrame) -> pd.DataFrame:
    """Create a date-by-metric matrix from the cleaned long table."""

    if data.empty:
        return pd.DataFrame()
    work = data.dropna(subset=["date"]).copy()
    work["feature_id"] = work["group"].str.lower().str.replace(" ", "_", regex=False) + "__" + work["metric_key"]
    return work.pivot_table(index="date", columns="feature_id", values="value", aggfunc="mean").sort_index()


def _pick_metric_key(data: pd.DataFrame, group: str, terms: tuple[str, ...]) -> str | None:
    """Pick a stable metric key using English labels before local labels."""

    candidates = data[data["group"] == group][["metric_key", "metric_english", "metric"]].drop_duplicates()
    if candidates.empty:
        return None
    for term in terms:
        term_lower = term.lower()
        match = candidates[candidates["metric_english"].str.lower().str.contains(term_lower, na=False)]
        if match.empty:
            match = candidates[candidates["metric"].str.lower().str.contains(term_lower, na=False)]
        if not match.empty:
            return str(match.iloc[0]["metric_key"])
    return None


def build_model_frame(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    """Build a leakage-aware quarterly regression frame.

    The target is net profit.  Predictors are lagged balance-sheet/income
    drivers, so a held-out period is never explained using its own target or
    contemporaneous future information.
    """

    wide = pivot_financial_data(data)
    if wide.empty:
        return pd.DataFrame(), {}, []

    requests: dict[str, tuple[str, tuple[str, ...]]] = {
        "target": ("Income statement", ("Net profit", "profit loss")),
        "total_assets": ("Balance sheet", ("Total assets",)),
        "loans": ("Balance sheet", ("Loans and advances", "loans")),
        "customer_deposits": ("Balance sheet", ("Customer deposits",)),
        "total_equity": ("Balance sheet", ("Total equity",)),
        "net_interest_income": ("Income statement", ("Net interest income",)),
        "total_income": ("Income statement", ("Total income",)),
        "impairment": ("Income statement", ("Impairment losses",)),
        "capital_adequacy": ("Financial indicators", ("capital adequacy", "mjaftueshm")),
        "return_on_equity": ("Financial indicators", ("return on equity", "kthimit në ekuitetin")),
    }
    selected: dict[str, str] = {}
    for name, (group, terms) in requests.items():
        key = _pick_metric_key(data, group, terms)
        if key:
            full_key = group.lower().replace(" ", "_") + "__" + key
            if full_key in wide.columns:
                selected[name] = full_key

    if "target" not in selected:
        return pd.DataFrame(), selected, []

    frame = pd.DataFrame(index=wide.index)
    frame["target"] = wide[selected["target"]]
    feature_columns: list[str] = []
    # Lag every driver by one and two quarters.  The current quarter itself is
    # never fed into the model, which keeps the task interpretable as a short
    # horizon prediction exercise.
    for name, full_key in selected.items():
        if name == "target":
            source = wide[full_key]
        else:
            source = wide[full_key]
        frame[f"{name}_lag1"] = source.shift(1)
        frame[f"{name}_lag2"] = source.shift(2)
        feature_columns.extend([f"{name}_lag1", f"{name}_lag2"])
    frame["year"] = frame.index.year
    frame["quarter"] = frame.index.quarter
    feature_columns.extend(["year", "quarter"])
    frame = frame.reset_index(names="date")
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.dropna(subset=["target"]).sort_values("date").reset_index(drop=True)
    return frame, selected, feature_columns


def describe_data(data: pd.DataFrame) -> pd.DataFrame:
    """Return descriptive statistics for the currently filtered numeric facts."""

    if data.empty:
        return pd.DataFrame()
    numeric = data[["value"]].describe().T
    numeric.insert(0, "measure", numeric.index)
    return numeric.reset_index(drop=True)


def run_statistical_tests(data: pd.DataFrame, locale: str | None = None) -> list[dict[str, Any]]:
    """Run transparent, small-sample tests with plain-language outputs."""

    results: list[dict[str, Any]] = []
    assets = metric_contains(data, ("total assets", "gjithsej pasurit"), group="Balance sheet")
    deposits = metric_contains(data, ("customer deposits", "depozitat e klient"), group="Balance sheet")
    if not assets.empty and not deposits.empty:
        paired = assets[["date", "value"]].rename(columns={"value": "assets"}).merge(
            deposits[["date", "value"]].rename(columns={"value": "deposits"}), on="date", how="inner"
        ).dropna()
        if len(paired) >= 4 and paired["assets"].nunique() > 1 and paired["deposits"].nunique() > 1:
            corr, p_value = stats.pearsonr(paired["assets"], paired["deposits"])
            direction = t("positive", locale) if corr >= 0 else t("negative", locale)
            results.append(
                {
                    "test": t("test_pearson", locale),
                    "statistic": float(corr),
                    "p_value": float(p_value),
                    "n": int(len(paired)),
                    "interpretation": t("test_interpretation_relationship", locale, direction=direction, statistic=f"{corr:.2f}", significance=t("significant_5", locale) if p_value < 0.05 else t("not_significant_5", locale)),
                }
            )

    profit = metric_contains(data, ("net profit", "profit loss", "fitimi"), group="Income statement")
    if not profit.empty:
        profit = profit.dropna(subset=["date", "value"]).copy()
        before = profit.loc[profit["year"] < 2020, "value"]
        after = profit.loc[profit["year"] >= 2020, "value"]
        if len(before) >= 3 and len(after) >= 3:
            t_stat, p_value = stats.ttest_ind(before, after, equal_var=False, nan_policy="omit")
            results.append(
                {
                    "test": t("test_welch", locale),
                    "statistic": float(t_stat),
                    "p_value": float(p_value),
                    "n": int(len(before) + len(after)),
                    "interpretation": t("test_interpretation_difference", locale, significance=t("significant_5", locale) if p_value < 0.05 else t("not_significant_5", locale)),
                }
            )

    if not assets.empty:
        trend = assets.dropna(subset=["date", "value"]).sort_values("date")
        if len(trend) >= 4 and trend["value"].nunique() > 1:
            x = np.arange(len(trend), dtype=float)
            slope, intercept, r_value, p_value, _stderr = stats.linregress(x, trend["value"].to_numpy())
            results.append(
                {
                    "test": t("test_trend", locale),
                    "statistic": float(slope),
                    "p_value": float(p_value),
                    "n": int(len(trend)),
                    "interpretation": t("test_interpretation_trend", locale, slope=format_number(slope, 0, locale), significance=t("significant_5", locale) if p_value < 0.05 else t("not_significant_5", locale)),
                }
            )
    return results
