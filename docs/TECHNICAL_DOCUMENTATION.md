# Technical Documentation

## 1. Scope and architecture

`Sales-Inventory-Analytics-Dashboard` is a Streamlit-only, read-only analytics application. The Excel workbook is the only source of data. Every calculation is performed in memory; models are fitted on demand and cached by Streamlit, but no model, database, API response, upload, or user profile is written to disk.

```text
Excel workbook
    |
    v
utils/data_loader.py  -> tidy long table + quality metadata
    |
    +--> utils/preprocessing.py -> filters, pivot, features, tests
    +--> utils/charts.py        -> shared Plotly template and charts
    +--> utils/ml_models.py     -> baseline, regressors, anomalies, segments
    +--> utils/insights.py      -> data-driven plain-language recommendations
    v
app.py                  -> Streamlit tabs, controls, interpretation
```

## 2. Project structure

```text
app.py
assets/project-logo.svg
logo.png
requirements.txt
.streamlit/config.toml
utils/
  data_loader.py
  preprocessing.py
  ml_models.py
  charts.py
  styling.py
  insights.py
docs/
  PROJECT_PROPOSAL.md
  TECHNICAL_DOCUMENTATION.md
  FINAL_REPORT.md
output/pdf/PROJECT_DOCUMENTATION_REPORT.pdf  # local only; Git-ignored
```

## 3. Data dictionary

| Field | Meaning | Treatment |
|---|---|---|
| `sheet` | Original Excel sheet name | Preserved for traceability |
| `group` | Balance sheet, Income statement, or Financial indicators | Inferred from sheet title |
| `metric` | Cleaned source metric label | Whitespace-normalised; replacement characters made visible as spaces |
| `metric_english` | English-side label where available | Used for readable chart labels and matching |
| `metric_key` | Stable lowercase identifier | Used in pivot/model feature names |
| `period_source` | Original period header | Preserved so corrections can be audited |
| `date` | Standardised quarter-end timestamp | Parsed from mixed date/quarter formats |
| `year`, `quarter`, `period` | Derived time fields | Used for filters and time features |
| `value_raw` | Numeric source value before indicator normalisation | Preserved for auditability |
| `value` | Analysis value | Percentage-style indicator cells normalised to decimal scale where appropriate |
| `outlier_iqr` | IQR-based screening flag | Flag only; never removed |
| `period_header_corrected` | Header correction flag | True for invalid/non-monotonic date labels |

## 4. Preprocessing pipeline

1. Discover the `.xlsx` file using a relative path.
2. Read all sheets with `pd.ExcelFile` and `pd.read_excel(..., header=None, engine="openpyxl")`.
3. Treat row 3 as the source period header and rows below it as metrics.
4. Normalise whitespace and labels; keep the source and English labels.
5. Convert numeric cells and percent strings; non-numeric blanks become `NaN`.
6. Parse `Q1-2023`, `31.03.2020`, `2024-03-31`, and similar labels to quarter ends.
7. Correct evident quarter-header errors using local sequence context. For example, `31.09.2019` becomes 30 September, and a duplicate non-monotonic 2024 header advances to the next expected quarter. Corrections are logged, not hidden.
8. Melt to one record per metric-period and remove exact duplicate metric-period records.
9. Compute IQR flags by metric using `Q1 - 1.5*IQR` and `Q3 + 1.5*IQR`. Outliers remain in the dataset because deleting them could remove real financial events.
10. Preserve missing financial facts. Model pipelines perform median imputation inside the training fold only, avoiding leakage.

The raw source has 155 missing financial cells, 0 duplicate source data rows in the metric-period key, and 3 period-header corrections. The app exposes this evidence in Data Quality.

## 5. Feature engineering

The modelling target is income-statement net profit. The feature frame joins aligned quarter-end values and creates:

- one- and two-quarter lags of net profit;
- one- and two-quarter lags of total assets, loans, customer deposits, total equity, net interest income, total income, impairment, capital adequacy, and return on equity when present;
- calendar year and quarter indicators.

The current quarter's driver values are not used. This is a short-horizon historical prediction experiment rather than a contemporaneous explanation task.

## 6. Algorithms and hyperparameters

### Regression

- Baseline: mean net profit in the training window.
- Ridge Regression: `alpha=1.0`, median imputation and standard scaling.
- Random Forest: 250 trees, `max_depth=5`, `min_samples_leaf=2`, `random_state=42`.
- Gradient Boosting: 120 estimators, `learning_rate=0.04`, `max_depth=2`, Huber loss, `random_state=42`.

The first 80% of chronological observations form training data and the final 8 quarters form the holdout. `TimeSeriesSplit` cross-validation is applied only inside the training window. Metrics are MAE, RMSE, R², and MAPE.

### Anomaly detection

Isolation Forest uses aligned financial metrics, standard scaling, 200 trees, a small deterministic contamination rate, and `random_state=42`. It is a screening model, not an investigation conclusion.

### Segmentation

KMeans is evaluated for `k=2..5` with 20 initialisations and `random_state=42`. The displayed selection maximises silhouette score; inertia, silhouette values, period assignments, and cluster profiles are shown.

## 7. Current benchmark results

| Model | MAE | RMSE | R² | MAPE | Training CV RMSE |
|---|---:|---:|---:|---:|---:|
| Baseline | 8,805.8 | 9,941.7 | -0.832 | 52.2% | - |
| Random Forest | 6,662.2 | 7,576.0 | -0.064 | 55.1% | 4,288.7 |
| Gradient Boosting | 6,617.6 | 7,720.7 | -0.105 | 66.0% | 3,873.3 |
| Ridge | 9,373.6 | 10,381.0 | -0.997 | 91.9% | 5,517.1 |

Random Forest is selected by held-out RMSE and improves the baseline RMSE by 23.8%. The negative R² and higher MAPE are retained in the result rather than hidden.

## 8. UI and chart inventory

The dashboard has nine tabs: Overview, Data Quality, Exploratory Analysis, Statistical Tests, Machine Learning, Anomalies & Segments, Insights & Recommendations, Methodology, and Data Explorer. It includes time-series lines, sorted bars, income composition, indicator lines, distributions, correlation heatmap, model comparison, actual-vs-predicted interval, residuals, feature importance, anomaly timeline, segment timeline, and quality-check charts. Every chart has a short interpretation below it.

## 9. Limitations and future work

This is a small single-bank quarterly dataset with no customer-level records, macroeconomic variables, loan-level risk outcomes, or true future labels after 2025 Q2. Therefore it cannot support credit-default classification, customer segmentation, causal impact, fraud detection, or high-confidence long-horizon forecasting. Future work could add later official quarters, macroeconomic covariates, a rolling-origin evaluation, prediction intervals calibrated on a longer sample, and domain review of indicator definitions.
