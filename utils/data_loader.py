"""Load and reshape the supplied TEB open-data workbook.

The workbook is intentionally kept as the only source of facts.  This module
does not download data, write files, or create synthetic observations.  It
turns the three wide financial-statement sheets into one tidy quarterly table
that the dashboard can reuse for EDA, statistics, and modelling.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


WORKBOOK_GLOB = "*.xlsx"


def find_workbook(base_dir: str | Path = ".") -> Path:
    """Return the workbook in ``base_dir`` using a relative, deployable path."""

    base = Path(base_dir)
    candidates = sorted(p for p in base.glob(WORKBOOK_GLOB) if not p.name.startswith("~$"))
    if not candidates:
        raise FileNotFoundError("No Excel workbook was found in the project folder.")
    return candidates[0]


def clean_text(value: Any) -> str:
    """Normalise whitespace and visibly damaged replacement characters."""

    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).replace("�", " ")
    return re.sub(r"\s+", " ", text).strip()


def _quarter_end(year: int, quarter: int) -> pd.Timestamp:
    """Create the conventional quarter-end date used by the source workbook."""

    month_day = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}[quarter]
    return pd.Timestamp(year=year, month=month_day[0], day=month_day[1])


def _parse_period(raw: Any) -> tuple[pd.Timestamp | pd.NaT, str, bool]:
    """Parse mixed date/quarter labels and correct obvious end-of-quarter typos.

    The source contains labels such as ``31.09.2019`` and ``30.12.2014``.
    They are mapped to the conventional quarter end (30 September and 31
    December).  The returned boolean records whether a local correction was
    made so the cleaning log can explain it.
    """

    if pd.isna(raw):
        return pd.NaT, "missing period label", True
    if isinstance(raw, (pd.Timestamp, np.datetime64)):
        dt = pd.Timestamp(raw)
        quarter = int((dt.month - 1) // 3 + 1)
        fixed = _quarter_end(dt.year, quarter)
        return fixed, fixed.strftime("%Y Q") + str(quarter), fixed != dt

    text = clean_text(raw)
    quarter_match = re.search(r"Q\s*([1-4])\s*[-_ ]?\s*(20\d{2})", text, flags=re.I)
    if quarter_match:
        quarter = int(quarter_match.group(1))
        year = int(quarter_match.group(2))
        return _quarter_end(year, quarter), f"{year} Q{quarter}", False

    ymd_match = re.search(r"(20\d{2})[-/]([0-9]{1,2})[-/]([0-9]{1,2})", text)
    dmy_match = re.search(r"([0-9]{1,2})[./-]([0-9]{1,2})[./-](20\d{2})", text)
    try:
        if ymd_match:
            year, month, _day = map(int, ymd_match.groups())
        elif dmy_match:
            _day, month, year = map(int, dmy_match.groups())
        else:
            parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
            if pd.isna(parsed):
                return pd.NaT, text, True
            year, month = int(parsed.year), int(parsed.month)
        quarter = int((month - 1) // 3 + 1)
        fixed = _quarter_end(year, quarter)
        original_month_day = f"{month:02d}-{fixed.day:02d}"
        return fixed, f"{year} Q{quarter}", original_month_day != f"{fixed.month:02d}-{fixed.day:02d}"
    except (ValueError, TypeError):
        return pd.NaT, text, True


def _to_numeric(value: Any) -> float:
    """Convert Excel values and percent strings to numeric values."""

    if pd.isna(value):
        return np.nan
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        is_percent = text.endswith("%")
        text = text.rstrip("%").strip()
        number = pd.to_numeric(text, errors="coerce")
        if pd.isna(number):
            return np.nan
        return float(number) / 100 if is_percent else float(number)
    number = pd.to_numeric(value, errors="coerce")
    return float(number) if not pd.isna(number) else np.nan


def _metric_english_name(label: str) -> str:
    """Prefer the English side of the bilingual balance/income labels."""

    if "/" in label:
        return label.split("/")[-1].strip()
    match = re.search(r"\(([^)]+)\)", label)
    return match.group(1).strip() if match else label


def _normalise_indicator_value(value: float, metric: str) -> float:
    """Make mixed ratio/percentage cells comparable without changing raw facts.

    In the indicator sheet, older cells are decimals (e.g. 0.1299) while a
    later block is expressed as percentages (e.g. 18.76 or ``18.76%``).  The
    ratio rows are therefore put on a decimal scale.  The assets-per-employee
    indicator is kept in its original numeric scale.
    """

    if pd.isna(value):
        return np.nan
    lower = metric.lower()
    if "numrit t\u00eb pun\u00ebtor\u00ebve" in lower or "number of employees" in lower:
        return value
    return value / 100 if abs(value) > 1 and abs(value) <= 100 else value


def _correct_non_monotonic_dates(
    parsed: list[pd.Timestamp | pd.NaT], corrections: list[bool]
) -> list[pd.Timestamp | pd.NaT]:
    """Repair duplicate/non-monotonic period headers using sequence context."""

    result: list[pd.Timestamp | pd.NaT] = []
    for idx, candidate in enumerate(parsed):
        previous = result[-1] if result else pd.NaT
        if pd.isna(candidate):
            if pd.isna(previous):
                result.append(candidate)
            else:
                next_period = previous + pd.DateOffset(months=3)
                result.append(_quarter_end(next_period.year, next_period.quarter))
                corrections[idx] = True
            continue
        if not pd.isna(previous) and candidate <= previous:
            next_period = previous + pd.DateOffset(months=3)
            result.append(_quarter_end(next_period.year, next_period.quarter))
            corrections[idx] = True
        else:
            result.append(candidate)
    return result


def _sheet_group(sheet_name: str) -> str:
    lower = sheet_name.lower()
    if "bilanc" in lower:
        return "Balance sheet"
    if "ardhur" in lower:
        return "Income statement"
    return "Financial indicators"


def load_workbook(path: str | Path) -> dict[str, Any]:
    """Read every workbook sheet and return tidy data plus quality metadata."""

    workbook_path = Path(path)
    excel = pd.ExcelFile(workbook_path, engine="openpyxl")
    long_parts: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    cleaning_log: list[dict[str, str]] = []
    raw_summaries: list[dict[str, Any]] = []

    for sheet_name in excel.sheet_names:
        raw = pd.read_excel(workbook_path, sheet_name=sheet_name, header=None, engine="openpyxl")
        group = _sheet_group(sheet_name)
        raw_labels = raw.iloc[3:, 0].map(clean_text)
        source_headers = list(raw.iloc[2, 1:])
        parsed_dates: list[pd.Timestamp | pd.NaT] = []
        parse_corrections: list[bool] = []
        for header in source_headers:
            parsed, _label, corrected = _parse_period(header)
            parsed_dates.append(parsed)
            parse_corrections.append(corrected)
        dates = _correct_non_monotonic_dates(parsed_dates, parse_corrections)
        corrections = int(sum(parse_corrections))

        records: list[dict[str, Any]] = []
        for row_idx, metric in raw_labels.items():
            if not metric:
                continue
            english_metric = _metric_english_name(metric)
            for col_idx, (source_header, date, corrected) in enumerate(
                zip(source_headers, dates, parse_corrections), start=1
            ):
                raw_value = raw.iat[row_idx, col_idx] if col_idx < raw.shape[1] else np.nan
                numeric_value = _to_numeric(raw_value)
                clean_value = (
                    _normalise_indicator_value(numeric_value, metric)
                    if group == "Financial indicators"
                    else numeric_value
                )
                records.append(
                    {
                        "sheet": sheet_name,
                        "group": group,
                        "metric": metric,
                        "metric_english": english_metric,
                        "metric_key": re.sub(r"[^a-z0-9]+", "_", english_metric.lower()).strip("_"),
                        "period_source": clean_text(source_header),
                        "date": date,
                        "year": int(date.year) if not pd.isna(date) else np.nan,
                        "quarter": int(date.quarter) if not pd.isna(date) else np.nan,
                        "value_raw": numeric_value,
                        "value": clean_value,
                        "period_header_corrected": bool(corrected),
                    }
                )

        sheet_df = pd.DataFrame.from_records(records)
        if not sheet_df.empty:
            duplicate_mask = sheet_df.duplicated(subset=["metric", "date"], keep="first")
            duplicates_removed = int(duplicate_mask.sum())
            sheet_df = sheet_df.loc[~duplicate_mask].copy()
            numeric_for_outliers = sheet_df["value"]
            grouped = sheet_df.groupby("metric")["value"]
            q1 = grouped.transform(lambda x: x.quantile(0.25))
            q3 = grouped.transform(lambda x: x.quantile(0.75))
            iqr = q3 - q1
            sheet_df["outlier_iqr"] = (numeric_for_outliers < q1 - 1.5 * iqr) | (
                numeric_for_outliers > q3 + 1.5 * iqr
            )
            sheet_df["outlier_iqr"] = sheet_df["outlier_iqr"].fillna(False)
        else:
            duplicates_removed = 0
            sheet_df["outlier_iqr"] = False

        missing_before = int(raw.iloc[3:, 1:].isna().sum().sum())
        missing_after = int(sheet_df["value"].isna().sum()) if not sheet_df.empty else 0
        outliers = int(sheet_df["outlier_iqr"].sum()) if not sheet_df.empty else 0
        quality_rows.append(
            {
                "sheet": sheet_name,
                "group": group,
                "raw_rows": int(raw.shape[0]),
                "raw_columns": int(raw.shape[1]),
                "data_rows": int(len(raw_labels[raw_labels != ""])),
                "period_columns": len(source_headers),
                "records_after_cleaning": int(len(sheet_df)),
                "missing_cells_before": missing_before,
                "missing_values_after": missing_after,
                "duplicates_removed": duplicates_removed,
                "period_headers_corrected": corrections,
                "outliers_found": outliers,
            }
        )
        raw_summaries.append(
            {
                "sheet": sheet_name,
                "columns": [clean_text(x) for x in raw.iloc[2, :].tolist()],
                "dtypes": {clean_text(raw.iloc[2, i]) or f"column_{i}": str(raw.dtypes.iloc[i]) for i in range(raw.shape[1])},
                "categorical_values": {},
                "numeric_ranges": {},
                "date_range": {"min": None, "max": None},
                "missing_values": {},
                "duplicates": int(raw.iloc[3:, :].duplicated().sum()),
            }
        )
        long_parts.append(sheet_df)
        cleaning_log.extend(
            [
                {"sheet": sheet_name, "step": "Header detection", "detail": "Row 3 treated as the period header; rows below are financial metrics."},
                {"sheet": sheet_name, "step": "Type conversion", "detail": "Numeric and percentage cells converted to numeric values; non-numeric blanks kept as missing."},
                {"sheet": sheet_name, "step": "Period parsing", "detail": f"Parsed {len(source_headers)} period columns; corrected {corrections} inconsistent/duplicate headers using quarter sequence context."},
                {"sheet": sheet_name, "step": "Whitespace normalisation", "detail": "Metric and source labels were trimmed and repeated whitespace collapsed."},
                {"sheet": sheet_name, "step": "Missing values", "detail": "Missing financial facts are preserved for transparency; model pipelines impute training medians only."},
                {"sheet": sheet_name, "step": "Duplicates", "detail": f"Removed {duplicates_removed} duplicate metric-period records."},
                {"sheet": sheet_name, "step": "Outliers", "detail": f"Flagged {outliers} IQR outliers; values were not deleted because they may represent real financial events."},
            ]
        )

    tidy = pd.concat(long_parts, ignore_index=True) if long_parts else pd.DataFrame()
    if not tidy.empty:
        tidy["date"] = pd.to_datetime(tidy["date"], errors="coerce")
        tidy = tidy.sort_values(["date", "group", "metric"]).reset_index(drop=True)
        tidy["period"] = tidy["date"].dt.strftime("%Y Q") + tidy["date"].dt.quarter.astype("Int64").astype(str)

    # These summaries are populated with real values after the tidy data exists.
    for summary in raw_summaries:
        subset = tidy[tidy["sheet"] == summary["sheet"]]
        summary["numeric_ranges"] = {
            "value": {
                "min": float(subset["value"].min()) if subset["value"].notna().any() else None,
                "max": float(subset["value"].max()) if subset["value"].notna().any() else None,
            }
        }
        if not subset.empty and subset["date"].notna().any():
            summary["date_range"] = {"min": subset["date"].min().strftime("%Y-%m-%d"), "max": subset["date"].max().strftime("%Y-%m-%d")}
        summary["categorical_values"] = {
            "metric_count": int(subset["metric"].nunique()),
            "period_count": int(subset["date"].nunique()),
            "groups": sorted(subset["group"].dropna().unique().tolist()),
            "metric_labels": sorted(subset["metric"].dropna().unique().tolist()),
        }
        summary["missing_values"] = {
            "value_missing": int(subset["value"].isna().sum()),
            "period_missing": int(subset["date"].isna().sum()),
        }

    return {
        "data": tidy,
        "quality": pd.DataFrame(quality_rows),
        "cleaning_log": pd.DataFrame(cleaning_log),
        "raw_summaries": raw_summaries,
        "sheet_names": excel.sheet_names,
        "workbook_name": workbook_path.name,
    }


def metric_contains(data: pd.DataFrame, terms: tuple[str, ...], group: str | None = None) -> pd.DataFrame:
    """Filter metrics whose bilingual/English labels contain any requested term."""

    if data.empty:
        return data.copy()
    subset = data if group is None else data[data["group"] == group]
    pattern = "|".join(re.escape(term.lower()) for term in terms)
    mask = subset["metric"].str.lower().str.contains(pattern, na=False) | subset["metric_english"].str.lower().str.contains(pattern, na=False)
    return subset[mask].copy()
