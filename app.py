"""SIA Dashboard - translated, chart-safe view over the supplied TEB data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from utils.charts import (
    anomaly_scatter, correlation_heatmap, distribution, feature_importance,
    income_composition, latest_rankings, metric_line, model_comparison,
    multi_metric_lines, prediction_chart, residual_chart, quality_chart,
    segment_timeline,
)
from utils.data_loader import find_workbook, load_workbook
from utils.i18n import TRANSLATIONS, build_metric_translation_map, format_number, language_selector, metric_label, model_label, t
from utils.insights import recommendations, trend_sentence
from utils.ml_models import detect_anomalies, evaluate_regression, segment_periods
from utils.preprocessing import apply_filters, describe_data, run_statistical_tests
from utils.styling import inject_css, insight, kpi, render_explanation, render_footer, render_hero, render_logo


PROJECT_ROOT = Path(__file__).resolve().parent
PROJECT_LOGO = PROJECT_ROOT / "logo1.png"
PROJECT_LOGO_SMALL = PROJECT_ROOT / "assets" / "logo1_small.png"

st.set_page_config(page_title=t("page_title"), page_icon=str(PROJECT_LOGO_SMALL if PROJECT_LOGO_SMALL.exists() else PROJECT_LOGO), layout="wide", initial_sidebar_state="expanded")
inject_css()


@st.cache_data(show_spinner=False)
def get_bundle(workbook_path: str, modified_ns: int) -> dict:
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


def fmt(value: float | int | None, decimals: int = 0, locale: str | None = None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return format_number(value, decimals, locale)


def period_label(value, locale: str) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:%Y} {t('quarter_short', locale)}{value.quarter}"


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


def latest_item(data: pd.DataFrame, group: str) -> tuple[str, str, str]:
    subset = data[data["group"] == group].dropna(subset=["date", "value"])
    if subset.empty:
        return t("not_available"), "-", "-"
    latest_date = subset["date"].max()
    latest = subset[subset["date"] == latest_date].groupby("metric_english", as_index=False)["value"].mean()
    if latest.empty:
        return t("not_available"), "-", period_label(latest_date, st.session_state.get("lang", "en"))
    row = latest.loc[latest["value"].idxmax()]
    locale = st.session_state.get("lang", "en")
    return metric_label(row["metric_english"], locale), fmt(row["value"], 0, locale), period_label(latest_date, locale)


def latest_income_extremes(data: pd.DataFrame) -> tuple[str, str]:
    subset = data[data["group"] == "Income statement"].dropna(subset=["date", "value"])
    if subset.empty:
        return t("not_available"), t("not_available")
    latest = subset[subset["date"] == subset["date"].max()].groupby("metric_english", as_index=False)["value"].mean()
    locale = st.session_state.get("lang", "en")
    positive = latest.loc[latest["value"].idxmax()] if not latest.empty else None
    negative = latest.loc[latest["value"].idxmin()] if not latest.empty else None
    positive_text = f"{metric_label(positive['metric_english'], locale)} ({fmt(positive['value'], 0, locale)})" if positive is not None else t("not_available", locale)
    negative_text = f"{metric_label(negative['metric_english'], locale)} ({fmt(negative['value'], 0, locale)})" if negative is not None else t("not_available", locale)
    return positive_text, negative_text


def strongest_correlation(data: pd.DataFrame) -> tuple[str, str]:
    work = data.dropna(subset=["date", "value"])
    if work.empty:
        return t("not_available"), "-"
    pivot = work.pivot_table(index="date", columns="metric_english", values="value", aggfunc="mean")
    corr = pivot.corr(min_periods=4)
    if corr.empty or len(corr.columns) < 2:
        return t("not_available"), "-"
    values = corr.where(~np.eye(len(corr), dtype=bool)).abs()
    if values.isna().all().all():
        return t("not_available"), "-"
    first, second = values.stack().idxmax()
    locale = st.session_state.get("lang", "en")
    return f"{metric_label(first, locale)} / {metric_label(second, locale)}", fmt(corr.loc[first, second], 2, locale)


def render_empty_message(data: pd.DataFrame, locale: str) -> None:
    if data.empty:
        st.warning(t("no_filter_data", locale))


def render_explanation_key(prefix: str, locale: str, **kwargs) -> None:
    render_explanation(t(f"{prefix}_what", locale), t(f"{prefix}_how", locale), t(f"{prefix}_meaning", locale, **kwargs))


def safe_chart(factory, locale: str, prefix: str | None = None, available: bool = True, **kwargs) -> None:
    try:
        if not available:
            st.warning(t("no_data_chart", locale))
            return
        figure = factory()
        st.plotly_chart(figure, use_container_width=True)
    except Exception:
        st.warning(t("chart_error", locale))
    if prefix:
        render_explanation_key(prefix, locale, **kwargs)


def show_table(table, locale: str, explanation_key: str | None = None, height: int | None = None) -> None:
    try:
        display = table.copy() if isinstance(table, pd.DataFrame) else table
        if isinstance(display, pd.DataFrame):
            if "model" in display.columns:
                display["model"] = display["model"].map(lambda value: model_label(value, locale))
            if "metric_english" in display.columns:
                display["metric_english"] = display["metric_english"].map(lambda value: metric_label(value, locale))
            if "metric" in display.columns:
                display["metric"] = display["metric"].map(lambda value: metric_label(value, locale))
            for column in display.columns:
                if pd.api.types.is_numeric_dtype(display[column]) and not pd.api.types.is_bool_dtype(display[column]):
                    decimals = 0 if column in {"n", "count", "k", "raw_rows", "raw_columns", "data_rows", "period_columns", "records_after_cleaning", "missing_cells_before", "missing_values_after", "duplicates_removed", "period_headers_corrected", "outliers_found", "metric_count", "period_count"} else 1
                    display[column] = display[column].map(lambda value: format_number(value, decimals, locale) if pd.notna(value) else "-")
            column_labels = {
                "sheet": t("source_sheets", locale), "group": t("data_domains", locale), "metric": t("metric", locale), "metric_english": t("metric", locale), "period": t("quarter", locale), "date": t("date", locale), "value": t("value", locale), "value_raw": t("raw_value", locale), "outlier_iqr": t("outlier_flag", locale), "period_header_corrected": t("corrected_period", locale), "model": t("model", locale), "statistic": t("statistic", locale), "p_value": t("p_value", locale), "n": t("sample_size", locale), "RMSE": t("rmse_label", locale), "MAE": t("mae_label", locale), "R2": t("r2_label", locale), "MAPE": t("mape_label", locale), "CV_RMSE": t("cv_rmse", locale), "actual": t("actual", locale), "baseline": t("baseline", locale), "best_prediction": t("best_prediction", locale), "residual": t("residual", locale), "lower": t("lower_bound", locale), "upper": t("upper_bound", locale), "anomaly": t("flagged", locale), "anomaly_score": t("anomaly_score", locale), "segment": t("cluster", locale), "k": t("group_count", locale), "inertia": t("inertia", locale), "silhouette": t("silhouette", locale), "measure": t("measure", locale), "count": t("count", locale), "mean": t("mean", locale), "std": t("standard_deviation", locale), "min": t("minimum", locale), "25%": t("percentile_25", locale), "50%": t("median", locale), "75%": t("percentile_75", locale), "max": t("maximum", locale)}
            display = display.rename(columns={key: value for key, value in column_labels.items() if key in display.columns})
            if "model" in display.columns:
                display["model"] = display["model"].map(lambda value: model_label(value, locale))
        kwargs = {"hide_index": True, "use_container_width": True}
        if height is not None:
            kwargs["height"] = height
        st.dataframe(display, **kwargs)
    except Exception:
        st.warning(t("table_error", locale))
    if explanation_key:
        translation_keys = TRANSLATIONS.get(locale, TRANSLATIONS["en"])
        if f"{explanation_key}_what" in translation_keys:
            render_explanation_key(explanation_key, locale, count=len(table) if hasattr(table, "__len__") else 0)
        else:
            render_explanation(t("table_explanation_what", locale), t("table_explanation_how", locale), t(explanation_key, locale))


try:
    workbook_path = find_workbook(PROJECT_ROOT)
    bundle = get_bundle(str(workbook_path), workbook_path.stat().st_mtime_ns)
except Exception:
    st.error(t("workbook_error"))
    st.stop()

data = bundle["data"]
quality = bundle["quality"]
metric_translation_map = build_metric_translation_map(data)
metric_lookup = data.groupby("metric", dropna=True)["metric_english"].first().to_dict()

with st.container():
    st.markdown(f'<div class="language-bar-label">{t("language_label")}</div>', unsafe_allow_html=True)
    locale = language_selector()
    st.markdown(f'<script>document.documentElement.lang="{locale}";</script>', unsafe_allow_html=True)

with st.sidebar:
    render_logo(PROJECT_LOGO_SMALL if PROJECT_LOGO_SMALL.exists() else PROJECT_LOGO, width=128, alt=t("logo_alt", locale))
    st.markdown(f"### {t('public_data_controls', locale)}")
    st.caption(t("filter_help", locale))
    all_sheets = list(bundle["sheet_names"])
    selected_sheets = st.multiselect(t("source_sheets", locale), all_sheets, default=all_sheets, key="selected_sheets")
    all_groups = sorted(data["group"].dropna().unique().tolist())
    group_labels = {"Balance sheet": t("balance_sheet", locale), "Income statement": t("income_statement", locale), "Financial indicators": t("financial_indicators", locale)}
    selected_groups = st.multiselect(t("data_domains", locale), all_groups, default=all_groups, format_func=lambda value: group_labels.get(value, value), key="selected_groups")
    years = sorted(int(year) for year in data["year"].dropna().unique())
    if years:
        year_range = st.slider(t("year_range", locale), min_value=min(years), max_value=max(years), value=(min(years), max(years)), step=1, key="year_range")
        selected_years = [year for year in years if year_range[0] <= year <= year_range[1]]
    else:
        selected_years = []
    metric_query = st.text_input(t("metric_search", locale), placeholder=t("metric_placeholder", locale), key="metric_query")
    metric_options = sorted(data["metric"].dropna().unique().tolist())
    if metric_query.strip():
        metric_options = [metric for metric in metric_options if metric_query.strip().lower() in metric.lower()]
    selected_metrics = st.multiselect(t("metrics_optional", locale), metric_options, default=[], format_func=lambda value: metric_translation_map.get(metric_lookup.get(value, value), {}).get(locale, metric_label(metric_lookup.get(value, value), locale)), key="selected_metrics")
    st.divider()
    st.caption(f"{t('independent_project', locale)}\n\n{t('practical_completion', locale)}\n{t('planned_date', locale)}")

filtered = apply_filters(data, selected_sheets, selected_groups, selected_years, selected_metrics)
render_hero(PROJECT_LOGO, bundle["workbook_name"], len(filtered), locale)

tabs = st.tabs([t(key, locale) for key in ("overview_tab", "quality_tab", "eda_tab", "tests_tab", "ml_tab", "anomaly_tab", "insights_tab", "methodology_tab", "explorer_tab")])

with tabs[0]:
    st.markdown(f"## {t('executive_overview', locale)}")
    st.caption(t("reported_figures_caption", locale))
    latest_period = filtered["date"].max() if not filtered.empty else None
    total_assets = latest_metric(filtered, "Balance sheet", ("total assets", "gjithsej pasurit"))
    profit = latest_metric(filtered, "Income statement", ("net profit", "profit loss", "fitimi"))
    periods = int(filtered["date"].nunique()) if not filtered.empty else 0
    rank_item, rank_value, rank_period = latest_item(filtered, "Balance sheet")
    income_positive, income_negative = latest_income_extremes(filtered)
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("kpi_latest_period", period_label(latest_period, locale), "help_latest_period")
    with c2: kpi("kpi_observed_quarters", fmt(periods, 0, locale), "help_observed_quarters")
    with c3: kpi("kpi_total_assets", fmt(total_assets, 0, locale), "help_total_assets")
    with c4: kpi("kpi_net_profit", fmt(profit, 0, locale), "help_net_profit")
    render_explanation_key("exp_overview", locale, periods=fmt(periods, 0, locale), period=period_label(latest_period, locale), assets=fmt(total_assets, 0, locale), profit=fmt(profit, 0, locale))
    render_empty_message(filtered, locale)
    left, right = st.columns(2)
    with left:
        safe_chart(lambda: multi_metric_lines(filtered, "Balance sheet", ("total assets", "customer deposits", "loans and advances"), "overview_chart_balance"), locale, "exp_balance", start=fmt(latest_metric(filtered.iloc[:1], "Balance sheet", ("total assets", "gjithsej pasurit")), 0, locale), end=fmt(total_assets, 0, locale), first=period_label(filtered["date"].min() if not filtered.empty else None, locale), last=period_label(latest_period, locale))
        insight(trend_sentence(filtered, "Balance sheet", ("total assets", "gjithsej pasurit"), t("kpi_total_assets", locale), locale))
    with right:
        safe_chart(lambda: metric_line(filtered, ("net profit", "profit loss", "fitimi"), "Income statement", "overview_chart_profit"), locale, "exp_profit", start=fmt(latest_metric(filtered.iloc[:1], "Income statement", ("net profit", "profit loss", "fitimi")), 0, locale), end=fmt(profit, 0, locale), first=period_label(filtered["date"].min() if not filtered.empty else None, locale), last=period_label(latest_period, locale))
        insight(trend_sentence(filtered, "Income statement", ("net profit", "fitimi"), t("kpi_net_profit", locale), locale))
    left, right = st.columns(2)
    with left:
        safe_chart(lambda: latest_rankings(filtered, "Balance sheet", "overview_chart_rank"), locale, "exp_rank", item=rank_item, value=rank_value, period=rank_period)
    with right:
        safe_chart(lambda: income_composition(filtered), locale, "exp_income", positive=income_positive, negative=income_negative)

with tabs[1]:
    st.markdown(f"## {t('quality_heading', locale)}")
    st.caption(t("quality_caption", locale))
    q1, q2, q3, q4 = st.columns(4)
    with q1: kpi("kpi_source_sheets", fmt(len(bundle["sheet_names"]), 0, locale), "help_source_sheets")
    with q2: kpi("kpi_clean_records", fmt(len(data), 0, locale), "help_clean_records")
    with q3: kpi("kpi_missing_cells", fmt(int(quality["missing_cells_before"].sum()), 0, locale), "help_missing_cells")
    with q4: kpi("kpi_outliers", fmt(int(quality["outliers_found"].sum()), 0, locale), "help_outliers")
    render_explanation_key("exp_quality_kpi", locale, sheets=fmt(len(bundle["sheet_names"]), 0, locale), records=fmt(len(data), 0, locale), missing=fmt(int(quality["missing_cells_before"].sum()), 0, locale), outliers=fmt(int(quality["outliers_found"].sum()), 0, locale))
    safe_chart(lambda: quality_chart(quality), locale, "exp_quality_chart", missing=fmt(int(quality["missing_cells_before"].sum()), 0, locale), outliers=fmt(int(quality["outliers_found"].sum()), 0, locale))
    st.markdown(f"### {t('before_after_sheet', locale)}")
    show_table(quality, locale, "table_quality")
    st.markdown(f"### {t('cleaning_log', locale)}")
    show_table(bundle["cleaning_log"], locale, "table_cleaning")
    st.markdown(f"### {t('source_inventory', locale)}")
    inventory = [{"sheet": summary["sheet"], "metric_count": summary["categorical_values"]["metric_count"], "period_count": summary["categorical_values"]["period_count"], "value_min": summary["numeric_ranges"]["value"]["min"], "value_max": summary["numeric_ranges"]["value"]["max"]} for summary in bundle["raw_summaries"]]
    show_table(pd.DataFrame(inventory), locale, "table_inventory")
    st.markdown(f"### {t('full_source_profile', locale)}")
    st.caption(t("profile_caption", locale))
    for summary in bundle["raw_summaries"]:
        with st.expander(summary["sheet"], expanded=False):
            st.markdown(f"**{t('date', locale)}:** {summary['date_range']['min']} Ã¢â‚¬â€œ {summary['date_range']['max']}  \n**{t('missing_cells', locale)}:** {summary['missing_values']['value_missing']}  \n**{t('duplicate_rows', locale)}:** {summary['duplicates']}  \n**{t('metric_count', locale)}:** {summary['categorical_values']['metric_count']}  \n**{t('period_count', locale)}:** {summary['categorical_values']['period_count']}")
            st.code("\n".join(summary["columns"]))
            render_explanation(t("table_profile", locale), t("table_profile", locale), t("table_profile", locale))

with tabs[2]:
    st.markdown(f"## {t('eda_heading', locale)}")
    st.caption(t("eda_caption", locale))
    left, right = st.columns(2)
    with left: safe_chart(lambda: multi_metric_lines(filtered, "Financial indicators", ("capital adequacy", "return on assets", "return on equity", "net interest margin"), "eda_chart_indicators"), locale, "exp_indicator", start=fmt(filtered["value"].min() if not filtered.empty else None, 3, locale), end=fmt(filtered["value"].max() if not filtered.empty else None, 3, locale), periods=fmt(periods, 0, locale))
    with right: safe_chart(lambda: distribution(filtered, "Income statement", "eda_chart_distribution"), locale, "exp_distribution", count=fmt(int(filtered[filtered["group"] == "Income statement"]["value"].notna().sum()), 0, locale), minimum=fmt(filtered[filtered["group"] == "Income statement"]["value"].min() if not filtered.empty else None, 0, locale), maximum=fmt(filtered[filtered["group"] == "Income statement"]["value"].max() if not filtered.empty else None, 0, locale))
    left, right = st.columns(2)
    correlation_pair, correlation_score = strongest_correlation(filtered)
    latest_indicator, latest_indicator_value, latest_indicator_period = latest_item(filtered, "Financial indicators")
    with left: safe_chart(lambda: correlation_heatmap(filtered, "eda_chart_correlation"), locale, "exp_correlation", pair=correlation_pair, score=correlation_score)
    with right: safe_chart(lambda: latest_rankings(filtered, "Financial indicators", "eda_chart_latest"), locale, "exp_latest", item=latest_indicator, value=latest_indicator_value, period=latest_indicator_period)
    st.markdown(f"### {t('descriptive_statistics', locale)}")
    stats_table = describe_data(filtered)
    if stats_table.empty:
        st.info(t("no_numeric", locale))
    else:
        show_table(stats_table, locale, "table_stats")
        render_explanation_key("exp_stats", locale, count=fmt(len(filtered["value"].dropna()), 0, locale), minimum=fmt(filtered["value"].min(), 0, locale), maximum=fmt(filtered["value"].max(), 0, locale))

with tabs[3]:
    st.markdown(f"## {t('tests_heading', locale)}")
    st.caption(t("tests_caption", locale))
    test_results = run_statistical_tests(filtered, locale)
    if not test_results:
        st.info(t("no_tests", locale))
    else:
        test_df = pd.DataFrame(test_results)
        show_table(test_df[["test", "statistic", "p_value", "n"]], locale, "table_tests")
        render_explanation_key("exp_tests", locale, count=fmt(len(test_results), 0, locale))
        for result in test_results:
            insight(result["interpretation"])
    st.markdown(f"### {t('questions_answered', locale)}")
    st.markdown(t("questions_text", locale))

with tabs[4]:
    st.markdown(f"## {t('ml_heading', locale)}")
    st.caption(t("ml_caption", locale))
    model_result = get_regression(filtered)
    if not model_result["available"]:
        st.warning(t("not_enough_model", locale))
    else:
        metrics_df = model_result["metrics"].copy()
        best = metrics_df[metrics_df["model"] == model_result["best_model"]].iloc[0]
        baseline = metrics_df[metrics_df["model"] == "Baseline (training mean)"].iloc[0]
        improvement = (baseline["RMSE"] - best["RMSE"]) / baseline["RMSE"] * 100 if baseline["RMSE"] else 0
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi("kpi_best_model", model_label(model_result["best_model"], locale), "help_best_model")
        with c2: kpi("kpi_rmse", fmt(best["RMSE"], 1, locale), "help_rmse")
        with c3: kpi("kpi_r2", fmt(best["R2"], 3, locale), "help_r2")
        with c4: kpi("kpi_vs_baseline", f"{improvement:+.1f}%", "help_vs_baseline")
        render_explanation_key("exp_ml_kpi", locale, model=model_label(model_result["best_model"], locale), rmse=fmt(best["RMSE"], 1, locale), baseline=fmt(baseline["RMSE"], 1, locale))
        show_table(metrics_df, locale, "table_models")
        left, right = st.columns(2)
        with left: safe_chart(lambda: model_comparison(metrics_df), locale, "exp_models", model=model_label(model_result["best_model"], locale), rmse=fmt(best["RMSE"], 1, locale))
        with right: safe_chart(lambda: prediction_chart(model_result["predictions"]), locale, "exp_predictions", count=fmt(len(model_result["predictions"]), 0, locale), mae=fmt(best["MAE"], 1, locale))
        insight(t("model_ready", locale))
        left, right = st.columns(2)
        with left:
            predictions = model_result["predictions"]
            safe_chart(lambda: residual_chart(predictions), locale, "exp_residuals", mean=fmt(predictions["residual"].mean(), 1, locale), maximum=fmt(predictions["residual"].abs().max(), 1, locale))
        with right:
            driver = model_result["importance"].iloc[0]["feature"] if not model_result["importance"].empty else t("not_available", locale)
            safe_chart(lambda: feature_importance(model_result["importance"]), locale, "exp_drivers", driver=driver)
        st.markdown(f"### {t('held_out_predictions', locale)}")
        show_table(model_result["predictions"], locale, "exp_predictions_table")

with tabs[5]:
    st.markdown(f"## {t('anomaly_heading', locale)}")
    st.caption(t("anomaly_caption", locale))
    anomaly_result = get_anomalies(filtered)
    segment_result = get_segments(filtered)
    left, right = st.columns(2)
    with left:
        if anomaly_result["available"]:
            result = anomaly_result["result"]
            safe_chart(lambda: anomaly_scatter(result), locale, "exp_anomaly", count=fmt(int(result["anomaly"].sum()), 0, locale), total=fmt(len(result), 0, locale))
            flagged = result.loc[result["anomaly"]]
            show_table(flagged, locale, "exp_anomaly_table")
        else: st.warning(t("anomaly_unavailable", locale))
    with right:
        if segment_result["available"]:
            segment_data = segment_result["result"]
            safe_chart(lambda: segment_timeline(segment_data), locale, "exp_segment", k=fmt(segment_result["best_k"], 0, locale), periods=fmt(len(segment_data), 0, locale))
            st.markdown(f"**{t('selected_clusters', locale, k=segment_result['best_k'])}**")
            show_table(segment_result["profile"], locale, "exp_segment_table")
        else: st.warning(t("segments_unavailable", locale))
    if segment_result["available"]:
        st.markdown(f"### {t('cluster_diagnostics', locale)}")
        diag = pd.merge(segment_result["elbow"], segment_result["silhouette"], on="k")
        show_table(diag, locale, "table_diagnostics")
        render_explanation(t("what_this_shows", locale), t("how_to_read", locale), t("exp_diagnostics", locale))

with tabs[6]:
    st.markdown(f"## {t('insights_heading', locale)}")
    model_for_insights = get_regression(filtered)
    anomalies_for_insights = get_anomalies(filtered)
    segments_for_insights = get_segments(filtered)
    recs = recommendations(filtered, model_for_insights, anomalies_for_insights, segments_for_insights, locale)
    if not recs:
        st.info(t("no_recommendations", locale))
    else:
        for item in recs: insight(item)
    render_explanation(t("exp_recommendations_what", locale), t("exp_recommendations_how", locale), t("exp_recommendations_meaning", locale))
    st.markdown(f"### {t('practical_use_case', locale)}")
    st.markdown(t("banking_use_case_text", locale))
    render_explanation(t("what_this_shows", locale), t("how_to_read", locale), t("banking_use_case_text", locale))
    st.markdown(f"### {t('guardrails', locale)}")
    st.markdown(t("guardrails_text", locale))
    render_explanation(t("what_this_shows", locale), t("how_to_read", locale), t("guardrails_text", locale))

with tabs[7]:
    st.markdown(f"## {t('methodology_tab', locale)}")
    st.markdown(t("methodology_text", locale))
    st.markdown(f"### {t('reproducibility', locale)}")
    st.code("pip install -r requirements.txt\nstreamlit run app.py", language="bash")

with tabs[8]:
    st.markdown(f"## {t('data_explorer_heading', locale)}")
    st.caption(t("explorer_caption", locale))
    display_columns = ["sheet", "group", "metric", "metric_english", "period", "date", "value", "value_raw", "outlier_iqr", "period_header_corrected"]
    if filtered.empty:
        st.info(t("no_rows", locale))
    else:
        show_table(filtered[display_columns], locale, "table_explorer", height=520)
        csv_bytes = filtered[display_columns].to_csv(index=False).encode("utf-8")
        st.download_button(t("download_csv", locale), data=csv_bytes, file_name="sia_filtered_financial_data.csv", mime="text/csv")
        render_explanation(t("what_this_shows", locale), t("how_to_read", locale), t("explorer_caption", locale))

render_footer()
