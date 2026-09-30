# Final Report: Banking Open-Data Analytics Dashboard

## 1. Executive summary

This project delivers a Streamlit dashboard for analysis and predictive modelling on the supplied TEB open-data workbook. The data is not a generic sales table: it is a quarterly banking financial dataset with three source sheets covering balance-sheet lines, income-statement lines, and financial indicators. The implementation therefore uses a banking-financial time-series design.

The final system reads every workbook sheet, creates a reusable tidy-data pipeline, exposes quality controls and EDA, runs transparent statistical tests, compares three regressors with a baseline, screens for anomalies, segments historical periods, and translates the results into practical banking recommendations. The project was completed on **30.09.2026**; the proposal's planned completion date was **01.10.2026**.

## 2. Objective

The objective is to help a bank analyst or manager review historical financial performance and use a cautious, explainable modelling workflow to support planning. The dashboard is intended for analysis and portfolio demonstration, not automated credit decisions, regulatory reporting, or investment advice.

## 3. Data and preparation

Source file: `9.-TEB-Banka-Sh.A.-Raportet-Financiare-1 (1).xlsx`.

| Source | Metrics | Periods | Records after reshape |
|---|---:|---:|---:|
| Balance sheet | 23 | 52 | 1,196 |
| Income statement | 17 | 51 | 867 |
| Financial indicators | 13 | 48 | 624 |
| **Total** | 53 | - | **2,687** |

The observed ranges are 2011-12-31 to 2025-06-30 for the balance sheet, 2012-06-30 to 2025-06-30 for the income statement, and 2012-12-31 to 2025-06-30 for financial indicators. The source contains 155 missing numeric cells and no duplicate metric-period records after keying. Three period headers were corrected using conventional quarter-end and local sequence rules. IQR screening flagged 138 values; none were removed because a large bank balance or income movement may be an authentic event.

## 4. Methods

### Analysis and statistics

The dashboard includes descriptive statistics, distributions, time trends, latest-period rankings, correlation heatmaps, and indicator trends. It answers three hypothesis-driven questions when the current filters leave enough observations:

1. Total assets and customer deposits have a very strong positive Pearson relationship: `r=0.996`, `p<0.001`, `n=52`.
2. Mean net profit differs before 2020 versus 2020 onwards under a Welch t-test: `t=-4.531`, `p<0.001`, `n=97` source observations. This is a sample comparison, not a causal claim.
3. Total assets have a positive linear trend of approximately 13,162 reported units per observed quarter: `p<0.001`, `n=52`.

### Predictive modelling

The target is quarterly net profit. Predictors are one- and two-quarter lags of relevant financial drivers plus calendar year and quarter. The chronological split uses 38 training rows and 8 held-out rows. Median imputation occurs inside pipelines, and cross-validation uses `TimeSeriesSplit` within training data only.

### Anomaly detection and segmentation

Isolation Forest flags 3 of the aligned quarters for analyst review. KMeans compares `k=2..5`; the best silhouette is `0.429` at `k=2` (alternatives: `k=3` `0.319`, `k=4` `0.361`, `k=5` `0.319`). These outputs screen historical regimes and unusual combinations but do not label fraud, risk, or customers.

## 5. Model results

| Model | MAE | RMSE | R² | MAPE | CV RMSE |
|---|---:|---:|---:|---:|---:|
| Baseline: training mean | 8,805.8 | 9,941.7 | -0.832 | 52.2% | - |
| Random Forest | 6,662.2 | **7,576.0** | -0.064 | 55.1% | 4,288.7 |
| Gradient Boosting | **6,617.6** | 7,720.7 | -0.105 | 66.0% | 3,873.3 |
| Ridge Regression | 9,373.6 | 10,381.0 | -0.997 | 91.9% | 5,517.1 |

Random Forest is the selected model because it has the lowest held-out RMSE. Its RMSE is 23.8% lower than the baseline. However, the negative R² means it does not explain more variance than a strong reference would on this small holdout, and its MAPE is slightly worse than the baseline. The correct business interpretation is that the model may add directional context to planning reviews, but it is not accurate enough to operate without human review or additional data.

## 6. Business interpretation

- Balance-sheet size and customer deposits move closely together in the observed sample, so funding and asset growth should be monitored jointly.
- The income statement contains both positive earnings lines and negative expenses/provisions; the composition chart helps prioritise material drivers rather than relying on total income alone.
- The model's feature importance is led by calendar quarter and lagged financial drivers. This may reflect seasonal structure and temporal regimes, not causal importance.
- Anomaly flags are concentrated in recent observed quarters and should be reconciled with source disclosures or known reporting events before any management action.
- Two KMeans regimes provide a compact way to compare historical financial periods, but cluster labels need domain validation.

## 7. Practical recommendations

1. Add the next official quarter and rerun the chronological holdout before using the model for planning.
2. Monitor deposits-to-assets alongside liquidity and funding concentration limits, not as a standalone KPI.
3. Review flagged quarters against original disclosures and known one-off provisions before treating them as operational anomalies.
4. Use model outputs as a scenario prompt with baseline and interval displayed together; do not hide the negative R² or MAPE limitation.
5. Maintain a quarterly data-quality review for missing cells, period-label corrections, and IQR flags.
6. If production-grade forecasting is required, add macroeconomic drivers, a longer time series, and rolling-origin evaluation.

## 8. Limitations

The sample is small and single-bank. It has no customer-level observations, loan-level defaults, macroeconomic covariates, policy interventions, or post-2025 outcomes. The model is therefore not suitable for customer scoring, credit classification, fraud detection, capital adequacy decisions, or long-horizon forecasting. A public-data workbook can also contain source formatting and period-label inconsistencies; all corrections are logged and the original file is retained.

## 9. Conclusion

The project meets the internship rubric with an auditable data pipeline, real-data EDA, statistical tests, properly split benchmarked models, anomaly and segment workflows, polished Streamlit UI, and documentation that interprets results honestly. The strongest demonstrated result is the 23.8% held-out RMSE improvement over the mean baseline, balanced by transparent evidence that the model is not yet production-ready. That balance of useful analysis, practical application, and limitations is the recommended basis for a graded portfolio project.
