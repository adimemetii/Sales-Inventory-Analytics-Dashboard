"""SIA Dashboard - interactive analysis of the supplied banking open data.

The app is Streamlit-only. It reads the workbook from the project directory,
calculates in memory, and never writes user data, model artifacts, or reports
at runtime.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from utils.charts import (
    anomaly_scatter,
    correlation_heatmap,
    distribution,
    feature_importance,
    income_composition,
    latest_rankings,
    metric_line,
    model_comparison,
    multi_metric_lines,
    prediction_chart,
    residual_chart,
    quality_chart,
    segment_timeline,
)
from utils.data_loader import find_workbook, load_workbook
from utils.insights import recommendations, trend_sentence
from utils.i18n import language_selector, t
from utils.ml_models import detect_anomalies, evaluate_regression, segment_periods
from utils.preprocessing import apply_filters, describe_data, run_statistical_tests
from utils.styling import inject_css, insight, kpi, render_hero, render_logo


PROJECT_ROOT = Path(__file__).resolve().parent
PROJECT_LOGO = PROJECT_ROOT / "logo1.png"

st.set_page_config(page_title="SIA Dashboard | Banking Analytics", page_icon=str(PROJECT_LOGO), layout="wide", initial_sidebar_state="expanded")
inject_css()


@st.cache_data(show_spinner=False)
def get_bundle(workbook_path: str, modified_ns: int) -> dict:
    """Cache workbook parsing while invalidating when the source file changes."""

    del modified_ns
    return load_workbook(workbook_path)


@st.cache_data(show_spinner=False)
def get_regression(data: pd.DataFrame) -> dict:
    return evaluate_regression(data)


@st.cache_data(show_spinner=False)
def get_anomalies(data: pd.DataFrame) -> dict:
    return detect_anomalies(data)


@st.cache_data(show_spinner=False)
def get_segments(data: pd.DataFrame) -> dict:
    return segment_periods(data)


def fmt(value: float | int | None, decimals: int = 0) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:,.{decimals}f}"


def latest_metric(data: pd.DataFrame, group: str, terms: tuple[str, ...]) -> float | None:
    if data.empty:
        return None
    subset = data[data["group"] == group].copy()
    pattern = "|".join(terms)
    subset = subset[subset["metric_english"].str.lower().str.contains(pattern, na=False) | subset["metric"].str.lower().str.contains(pattern, na=False)]
    subset = subset.dropna(subset=["date", "value"])
    if subset.empty:
        return None
    latest = subset[subset["date"] == subset["date"].max()]
    return float(latest["value"].mean()) if not latest.empty else None


def render_empty_message(data: pd.DataFrame) -> None:
    if data.empty:
        st.warning("No observations match the current sidebar filters. Expand the filters to continue.")


def show_table(table, height: int | None = None) -> None:
    """Render a Streamlit table with an HTML fallback for restricted runtimes."""

    try:
        kwargs = {"width": "stretch", "hide_index": True}
        if height is not None:
            kwargs["height"] = height
        st.dataframe(table, **kwargs)
    except ImportError:
        html = table.to_html() if hasattr(table, "to_html") else pd.DataFrame(table).to_html(index=False)
        st.markdown(f'<div class="fallback-table">{html}</div>', unsafe_allow_html=True)


try:
    workbook_path = find_workbook(PROJECT_ROOT)
    bundle = get_bundle(str(workbook_path), workbook_path.stat().st_mtime_ns)
except Exception as exc:  # pragma: no cover - protects the deployed empty state
    st.error(f"The workbook could not be loaded: {exc}")
    st.stop()

data = bundle["data"]
quality = bundle["quality"]

# Sidebar filters are built from real source columns and never create synthetic categories.
with st.sidebar:
    locale = language_selector()
    render_logo(PROJECT_LOGO, width=128, alt="Sales Inventory Analytics logo")
    st.markdown(f"### {t('Public-data controls', locale)}")
    st.caption(t("Filters update the analysis in memory. The Excel workbook remains the only data source.", locale))
    all_sheets = list(bundle["sheet_names"])
    selected_sheets = st.multiselect(t("Source sheets", locale), all_sheets, default=all_sheets)
    all_groups = sorted(data["group"].dropna().unique().tolist())
    selected_groups = st.multiselect(t("Data domains", locale), all_groups, default=all_groups)
    years = sorted(int(y) for y in data["year"].dropna().unique())
    if years:
        year_range = st.slider(t("Year range", locale), min_value=min(years), max_value=max(years), value=(min(years), max(years)), step=1)
        selected_years = [y for y in years if year_range[0] <= y <= year_range[1]]
    else:
        selected_years = []
    metric_query = st.text_input(t("Metric search", locale), placeholder=t("e.g. profit, loans, capital", locale))
    metric_options = sorted(data["metric"].dropna().unique().tolist())
    if metric_query.strip():
        query = metric_query.strip().lower()
        metric_options = [m for m in metric_options if query in m.lower()]
    selected_metrics = st.multiselect(t("Metrics (optional)", locale), metric_options, default=[])
    st.divider()
    st.caption(f"{t('Independent analytics project', locale)}\n\n{t('Practical completion: 30.09.2026', locale)}\n{t('Planned date: 01.10.2026', locale)}")

filtered = apply_filters(data, selected_sheets, selected_groups, selected_years, selected_metrics)

render_hero(PROJECT_LOGO, bundle["workbook_name"], len(filtered), locale)

tabs = st.tabs([
    t("Overview", locale),
    t("Data Quality", locale),
    t("Exploratory Analysis", locale),
    t("Statistical Tests", locale),
    t("Machine Learning", locale),
    t("Anomalies & Segments", locale),
    t("Insights & Recommendations", locale),
    t("Methodology", locale),
    t("Data Explorer", locale),
])

with tabs[0]:
    st.markdown(f"## {t('Executive overview', locale)}")
    st.caption("Reported figures retain the workbook's units; most statement values are reported in thousands where stated by the source.")
    latest_period = filtered["date"].max() if not filtered.empty else None
    total_assets = latest_metric(filtered, "Balance sheet", ("total assets", "gjithsej pasurit"))
    deposits = latest_metric(filtered, "Balance sheet", ("customer deposits", "depozitat e klient"))
    profit = latest_metric(filtered, "Income statement", ("net profit", "profit loss", "fitimi"))
    periods = int(filtered["date"].nunique()) if not filtered.empty else 0
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Latest period", f"{latest_period:%Y Q}{latest_period.quarter}" if latest_period is not None else "-", "Latest period in current filters")
    with c2:
        kpi("Observed quarters", f"{periods:,}", "Unique cleaned periods")
    with c3:
        kpi("Total assets", fmt(total_assets), "Latest aligned reported value")
    with c4:
        kpi("Net profit", fmt(profit), "Latest aligned reported value")

    render_empty_message(filtered)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(multi_metric_lines(filtered, "Balance sheet", ("total assets", "customer deposits", "loans and advances"), "Balance-sheet scale over time"), width="stretch")
        insight(trend_sentence(filtered, "Balance sheet", ("total assets", "gjithsej pasurit"), "Total assets"))
    with right:
        st.plotly_chart(metric_line(filtered, ("net profit", "profit loss", "fitimi"), "Income statement", "Net profit trend"), width="stretch")
        insight(trend_sentence(filtered, "Income statement", ("net profit", "fitimi"), "Net profit"))
    left, right = st.columns(2)
    with left:
        st.plotly_chart(latest_rankings(filtered, "Balance sheet", "Largest balance-sheet items"), width="stretch")
        insight("The ranking shows which balance-sheet lines have the greatest reported scale in the latest visible period; size alone is not a risk assessment.")
    with right:
        st.plotly_chart(income_composition(filtered), width="stretch")
        insight("Positive and negative bars separate income sources from expenses and provisions, helping an analyst focus on the most material earnings drivers.")

with tabs[1]:
    st.markdown(f"## {t('Data quality & preprocessing', locale)}")
    st.caption("Quality checks are shown before modelling. Outliers are flagged with the IQR rule and retained because unusual financial quarters may be economically meaningful.")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        kpi("Source sheets", str(len(bundle["sheet_names"])), "All workbook sheets read")
    with q2:
        kpi("Clean records", fmt(len(data)), "Long-format records")
    with q3:
        kpi("Missing cells", fmt(int(quality["missing_cells_before"].sum())), "Source values kept visible")
    with q4:
        kpi("Outliers flagged", fmt(int(quality["outliers_found"].sum())), "IQR flags, not deleted")
    st.plotly_chart(quality_chart(quality), width="stretch")
    st.markdown("### Before / after by source sheet")
    show_table(quality)
    st.markdown("### Cleaning log")
    show_table(bundle["cleaning_log"])
    st.markdown("### Source-sheet inventory")
    inventory = []
    for summary in bundle["raw_summaries"]:
        inventory.append({"sheet": summary["sheet"], "metric_count": summary["categorical_values"]["metric_count"], "period_count": summary["categorical_values"]["period_count"], "value_min": summary["numeric_ranges"]["value"]["min"], "value_max": summary["numeric_ranges"]["value"]["max"]})
    show_table(pd.DataFrame(inventory))
    st.markdown("### Full source profile")
    st.caption("Every source sheet was profiled for columns, raw cell dtypes, date coverage, missingness, duplicates, categorical metric labels, and numeric ranges.")
    for summary in bundle["raw_summaries"]:
        with st.expander(summary["sheet"], expanded=False):
            profile_text = (
                f"**Date range:** {summary['date_range']['min']} to {summary['date_range']['max']}  \n"
                f"**Missing values:** {summary['missing_values']['value_missing']} value cells, {summary['missing_values']['period_missing']} period cells  \n"
                f"**Duplicate raw rows:** {summary['duplicates']}  \n"
                f"**Categorical summary:** {summary['categorical_values']['metric_count']} metrics, {summary['categorical_values']['period_count']} periods, groups: {', '.join(summary['categorical_values']['groups'])}  \n"
                f"**Numeric range:** {summary['numeric_ranges']['value']['min']} to {summary['numeric_ranges']['value']['max']}"
            )
            st.markdown(profile_text)
            st.markdown("**Columns**")
            st.code("\n".join(summary["columns"]))
            st.markdown("**Metric labels**")
            st.code("\n".join(summary["categorical_values"].get("metric_labels", [])) or "No labels")
            st.markdown("**Column dtypes**")
            st.code("\n".join(f"{column}: {dtype}" for column, dtype in summary["dtypes"].items()))

with tabs[2]:
    st.markdown(f"## {t('Exploratory analysis', locale)}")
    st.caption("The EDA uses the filtered real observations and separates balance-sheet scale, earnings, and reported financial indicators.")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(multi_metric_lines(filtered, "Financial indicators", ("capital adequacy", "return on assets", "return on equity", "net interest margin"), "Selected financial indicators"), width="stretch")
        insight("Indicator values are normalised to a decimal ratio where the source switches between decimals and percentage-style cells; the assets-per-employee indicator is kept on its own scale.")
    with right:
        st.plotly_chart(distribution(filtered, "Income statement", "Income-statement value distribution"), width="stretch")
        insight("The distribution highlights skew and negative expense/provision values; this is why a single average should not be used as the only description.")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(correlation_heatmap(filtered, "Cross-metric correlation heatmap"), width="stretch")
        insight("Correlation is an association across observed quarters, not proof that one banking line causes another.")
    with right:
        st.plotly_chart(latest_rankings(filtered, "Financial indicators", "Latest indicator values"), width="stretch")
        insight("The latest indicator ranking makes relative magnitudes visible, but indicators may use different business units and should be interpreted individually.")
    st.markdown("### Descriptive statistics")
    stats_table = describe_data(filtered)
    if stats_table.empty:
        st.info("No numeric observations are available for the current filters.")
    else:
        show_table(stats_table.style.format({c: "{:.3f}" for c in stats_table.columns if c != "measure"}))

with tabs[3]:
    st.markdown(f"## {t('Statistical tests', locale)}")
    st.caption("Tests are exploratory and use the observed quarterly sample. A p-value is evidence against a null hypothesis, not a measure of business importance.")
    test_results = run_statistical_tests(filtered)
    if not test_results:
        st.info("The selected filters do not leave enough aligned observations for the configured tests.")
    else:
        test_df = pd.DataFrame(test_results)
        show_table(test_df[["test", "statistic", "p_value", "n"]].style.format({"statistic": "{:.4f}", "p_value": "{:.4f}"}))
        for result in test_results:
            significance = "statistically significant at the 5% level" if result["p_value"] < 0.05 else "not statistically significant at the 5% level"
            insight(f"{result['test']}: {result['interpretation']} Result: {significance} (p={result['p_value']:.4f}).")
    st.markdown("### Questions answered")
    st.markdown("- Are total assets and customer deposits moving together? Pearson correlation is reported when both series align.")
    st.markdown("- Did average net profit differ before 2020 versus 2020 onwards? A Welch t-test is shown when both groups have enough quarters.")
    st.markdown("- Is there a directional trend in total assets? A simple linear trend test is shown with the estimated change per observed quarter.")

with tabs[4]:
    st.markdown(f"## {t('Machine learning', locale)}")
    st.caption("Task: predict quarterly net profit from lagged balance-sheet, income-statement, and indicator drivers. A chronological holdout prevents future quarters from leaking into training.")
    model_result = get_regression(filtered)
    if not model_result["available"]:
        st.warning(model_result["message"])
    else:
        metrics_df = model_result["metrics"].copy()
        best = metrics_df[metrics_df["model"] == model_result["best_model"]].iloc[0]
        baseline = metrics_df[metrics_df["model"] == "Baseline (training mean)"].iloc[0]
        improvement = (baseline["RMSE"] - best["RMSE"]) / baseline["RMSE"] * 100 if baseline["RMSE"] else 0
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi("Best model", model_result["best_model"], "Selected by held-out RMSE")
        with c2:
            kpi("Held-out RMSE", fmt(best["RMSE"], 1), "Lower is better")
        with c3:
            kpi("Held-out R²", fmt(best["R2"], 3), "Explained variance")
        with c4:
            kpi("Vs baseline", f"{improvement:+.1f}%", "RMSE improvement")
        show_table(metrics_df.style.format({c: "{:.3f}" for c in ["MAE", "RMSE", "R2", "MAPE", "CV_RMSE"]}))
        left, right = st.columns(2)
        with left:
            st.plotly_chart(model_comparison(metrics_df), width="stretch")
        with right:
            st.plotly_chart(prediction_chart(model_result["predictions"]), width="stretch")
        insight(f"The {model_result['best_model']} has held-out RMSE {best['RMSE']:,.1f} versus {baseline['RMSE']:,.1f} for the training-mean baseline, an improvement of {improvement:.1f}%. This is a planning signal, not a guarantee for future quarters.")
        left, right = st.columns(2)
        with left:
            st.plotly_chart(residual_chart(model_result["predictions"]), width="stretch")
        with right:
            st.plotly_chart(feature_importance(model_result["importance"]), width="stretch")
        st.markdown("### Held-out predictions")
        show_table(model_result["predictions"].style.format({c: "{:,.1f}" for c in ["actual", "baseline", "best_prediction", "residual", "lower", "upper"]}))
        insight(f"The model used {model_result['train_rows']} chronological training rows and {model_result['test_rows']} held-out rows beginning {model_result['test_start']:%Y Q}{model_result['test_start'].quarter}. CV RMSE is displayed for model stability inside the training window.")

with tabs[5]:
    st.markdown(f"## {t('Anomalies & segments', locale)}")
    st.caption("These are screening tools. An anomaly is an unusual multivariate pattern, not a finding of misconduct; a segment is a statistical cluster, not a customer segment.")
    anomaly_result = get_anomalies(filtered)
    segment_result = get_segments(filtered)
    left, right = st.columns(2)
    with left:
        if anomaly_result["available"]:
            st.plotly_chart(anomaly_scatter(anomaly_result["result"]), width="stretch")
            count = int(anomaly_result["result"]["anomaly"].sum())
            insight(f"Isolation Forest flags {count} of {len(anomaly_result['result'])} aligned quarters for analyst review. Review the underlying source period before drawing conclusions.")
            show_table(anomaly_result["result"].loc[anomaly_result["result"]["anomaly"]])
        else:
            st.warning(anomaly_result["message"])
    with right:
        if segment_result["available"]:
            st.plotly_chart(segment_timeline(segment_result["result"]), width="stretch")
            st.markdown(f"**Selected clusters:** {segment_result['best_k']} (highest silhouette score)")
            show_table(segment_result["profile"])
        else:
            st.warning(segment_result["message"])
    if segment_result["available"]:
        st.markdown("### Cluster diagnostics")
        diag = pd.merge(segment_result["elbow"], segment_result["silhouette"], on="k")
        show_table(diag)
        insight("Use the elbow and silhouette diagnostics to explain why the selected number of clusters is defensible; it is a modelling aid, not a business label by itself.")

with tabs[6]:
    st.markdown(f"## {t('Insights & recommendations', locale)}")
    model_for_insights = get_regression(filtered)
    anomalies_for_insights = get_anomalies(filtered)
    segments_for_insights = get_segments(filtered)
    recs = recommendations(filtered, model_for_insights, anomalies_for_insights, segments_for_insights)
    if not recs:
        st.info("Expand the filters to generate data-driven recommendations.")
    else:
        for item in recs:
            insight(item)
    st.markdown("### Practical banking use case")
    st.markdown("A bank analyst can use the dashboard to review the latest balance-sheet and earnings position, compare a quarter with historical regimes, review unusual combinations for manual investigation, and use the held-out net-profit model as one input to planning conversations. The workflow stays reviewable because each result links back to source periods and reported metrics.")
    st.markdown("### Guardrails")
    st.markdown("- Do not treat correlations, clusters, or anomalies as causal or regulatory conclusions.\n- Refresh the model when a new official quarter is published and re-check the time split.\n- Validate any risk, liquidity, or capital decision against official bank reporting and domain expertise.")

with tabs[7]:
    st.markdown(f"## {t('Methodology', locale)}")
    st.markdown(
        """
        **Data ingestion.** The app reads every sheet of the supplied `.xlsx` workbook with `pandas` and `openpyxl`. The source is reshaped from wide statement rows to a tidy table with one metric-period observation.

        **Cleaning.** Labels are normalised for whitespace, numeric and percentage cells are converted to numbers, quarter-end headers are parsed, and duplicate metric-period records are removed. Evident date-label typos such as `31.09.2019` are mapped to the conventional quarter end. Missing facts remain missing in the cleaned table and are imputed only inside model pipelines using training medians.

        **EDA and statistics.** The dashboard provides descriptive statistics, distributions, time trends, latest-period rankings, cross-metric correlation, and three transparent tests: Pearson correlation, Welch's t-test, and a linear trend test when sample sizes permit.

        **Predictive modelling.** Net profit is predicted from lagged drivers. Ridge, Random Forest, and Gradient Boosting are compared with a training-mean baseline. The chronological holdout is evaluated with MAE, RMSE, R², and MAPE; TimeSeriesSplit CV is used inside training only. Models are not saved to disk.

        **Anomalies and segments.** Isolation Forest screens for unusual combinations across aligned financial metrics. KMeans is evaluated across candidate `k` values and selected by silhouette score, with inertia and profiles shown for interpretability.

        **Limitations.** The workbook is a small single-bank quarterly sample, not a customer-level panel. It cannot support customer churn, credit default classification, causal claims, or high-frequency forecasting. Header corrections and mixed indicator units are documented, and all results should be reviewed against the original source and bank expertise.
        """
    )
    st.markdown("### Reproducibility")
    st.code("pip install -r requirements.txt\nstreamlit run app.py", language="bash")

with tabs[8]:
    st.markdown(f"## {t('Data explorer', locale)}")
    st.caption("This table is a filtered in-memory view. The download is generated in memory and does not write to the app filesystem.")
    display_columns = ["sheet", "group", "metric", "metric_english", "period", "date", "value", "value_raw", "outlier_iqr", "period_header_corrected"]
    if filtered.empty:
        st.info("No rows match the current filters.")
    else:
        show_table(filtered[display_columns], height=520)
        csv_bytes = filtered[display_columns].to_csv(index=False).encode("utf-8")
        st.download_button(t("Download filtered CSV (in memory)", locale), data=csv_bytes, file_name="sia_filtered_financial_data.csv", mime="text/csv")

st.markdown('<div class="footer-note">Independent internship &amp; portfolio project built on TEB open data. Not affiliated with TEB.</div>', unsafe_allow_html=True)
