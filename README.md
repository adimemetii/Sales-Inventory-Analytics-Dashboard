# Sales-Inventory-Analytics-Dashboard

An independent Python and Data Science internship project for Tectigon Academy. The dashboard analyses the supplied TEB open-data workbook and demonstrates reproducible preprocessing, exploratory analysis, statistics, predictive modelling, anomaly screening, segmentation, and practical interpretation in Streamlit.

The project name intentionally follows the current folder/repository name: `Sales-Inventory-Analytics-Dashboard`. The dataset itself is banking financial open data, so the app explains the domain inferred from the workbook rather than assuming a sales or inventory schema.

## Problem statement

Bank analysts need a repeatable way to understand how reported balance-sheet, income-statement, and financial-indicator lines move over time. This project turns three wide Excel sheets into a tidy quarterly data model and answers:

- What are the main balance-sheet and earnings trends?
- Which financial lines move together and what does the evidence say statistically?
- Can a short-horizon net-profit model outperform a simple training-mean baseline on held-out quarters?
- Which periods deserve manual review as unusual multivariate combinations?
- Which historical financial regimes can be described with data-driven segments?

The app is a portfolio and internship project. It does not claim affiliation with TEB and does not replace official reporting, risk governance, or regulatory analysis.

## Dataset

The only data source is `9.-TEB-Banka-Sh.A.-Raportet-Financiare-1 (1).xlsx`, read locally with pandas/openpyxl. It contains:

| Sheet | Domain | Cleaned scope |
|---|---|---:|
| `Bilanci i Gjendjes 2011-2025` | Balance sheet | 23 metrics, 52 periods, 1,196 records |
| `Pasqyra e te Ardhurave 2012-25` | Income statement | 17 metrics, 51 periods, 867 records |
| `Treguesit Financiar-2012-2025` | Financial indicators | 13 metrics, 48 periods, 624 records |

The full cleaned dataset contains 2,687 long-format records. The source has 155 missing financial cells, 0 duplicate metric-period records, 3 evident period-header corrections, and 138 IQR outlier flags. Missing facts remain visible; outliers are flagged but not deleted because they may represent real financial events.

## Methodology and key results

1. Read every workbook sheet and profile sheet names, headers, types, dates, missingness, duplicates, categorical counts, and numeric ranges.
2. Reshape wide statement rows into a tidy `metric-period-value` table; normalise labels, parse mixed quarter labels, and document corrections.
3. Explore time trends, distributions, latest-period rankings, correlations, and financial indicators.
4. Run Pearson correlation, Welch's t-test, and a linear trend test when sample sizes permit.
5. Predict quarterly net profit from lagged financial drivers using Ridge, Random Forest, and Gradient Boosting, compared with a training-mean baseline.
6. Screen for unusual quarters with Isolation Forest and segment financial periods with KMeans using silhouette selection.

On the default full dataset, the chronological holdout contains 8 quarters (training: 38 rows; holdout starts 2023-09-30). Random Forest is the best held-out-RMSE model:

| Model | MAE | RMSE | R² | MAPE |
|---|---:|---:|---:|---:|
| Mean baseline | 8,805.8 | 9,941.7 | -0.832 | 52.2% |
| Random Forest | 6,662.2 | 7,576.0 | -0.064 | 55.1% |
| Gradient Boosting | 6,617.6 | 7,720.7 | -0.105 | 66.0% |
| Ridge Regression | 9,373.6 | 10,381.0 | -0.997 | 91.9% |

Random Forest improves held-out RMSE by 23.8% versus the baseline, but its negative R² and higher MAPE show that the model is a cautious planning signal, not a production forecast. This limitation is intentionally visible in the app and final report.

## Tech stack

Python, pandas, NumPy, openpyxl, scikit-learn, SciPy, statsmodels-compatible statistical workflow, Plotly, Streamlit, ReportLab, and pdfplumber/pypdf for report verification.

## Design system

The dashboard uses a dark navy glass system built around the exact blue-teal brand palette: `#2F39A9` deep indigo, `#2E6FA0` ocean blue, `#49A4BB` teal blue, and `#15D8B3` aqua mint. Inter is used for interface text and Space Grotesk for display headings. Charts use one shared high-contrast Plotly template, and chart containers never depend on animation for visibility. Global CSS lives in `assets/style.css`; Python constants and reusable render helpers live in `utils/styling.py`.

The app icon files are generated with `tools/make_logo.py`, which creates the transparent 1024×1024 `logo1.png` root logo and the `assets/logo1_small.png` 256×256 favicon. The Tectigon/company logos remain unchanged.

## Languages (EN/SQ/DE)

The dashboard supports English, Shqip (Albanian), and Deutsch. Use the language selector above the hero; the choice is stored in `st.session_state["lang"]`, so stable filter keys keep the selected data filters when the language changes. UI strings, metric names, number formats, and Plotly labels use `utils/i18n.py`.

### How to add a new language

Add the language code and label to `LANGUAGES`, add every existing key to that language in `TRANSLATIONS`, add the translated metric labels and number-format rule, then run `python tools/check_i18n.py`. The check verifies identical non-empty key sets, scans visible Streamlit/Plotly calls, and runs the app smoke test for English, Shqip, and Deutsch.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The workbook must stay beside `app.py` for local use and Streamlit Community Cloud deployment. The app uses a relative project path and does not write files at runtime.

## Deploy on Streamlit Community Cloud

1. Push the code, workbook, `requirements.txt`, `.streamlit/config.toml`, and `app.py` to a GitHub repository.
2. In Streamlit Community Cloud, select the repository and `main` branch.
3. Set the main file to `app.py`.
4. Deploy. No secrets, API keys, database, backend, or external data connection is required.

The generated PDF documentation report is intentionally stored locally under `output/pdf/` and is ignored by Git because the public repository should contain source documentation, not a private generated artifact.

## Documentation

- [Technical documentation](docs/TECHNICAL_DOCUMENTATION.md)
- [Final report](docs/FINAL_REPORT.md)
- [Project proposal](docs/PROJECT_PROPOSAL.md)
- Generated local report: `output/pdf/PROJECT_DOCUMENTATION_REPORT.pdf` (not committed or pushed)

## Screenshots

Add screenshots from the deployed app here before final portfolio publication:

`![Overview screenshot](docs/assets/overview-placeholder.png)`

`![Machine learning screenshot](docs/assets/ml-placeholder.png)`

## Public-repository safety

- No credentials, tokens, `.env` files, Streamlit secrets, databases, or model pickles are included.
- The app has no API, backend, database, user-data storage, or runtime file writing.
- The company `logo.png` is used as supplied for the internship context; the project also has a separate SIA vector logo.
- The footer clearly states that this is an independent portfolio project and not affiliated with TEB.

## Rubric checklist

- [x] Data analysis and preprocessing (30%): `utils/data_loader.py`, `utils/preprocessing.py`, Data Quality tab, missingness/duplicates/outliers/cleaning log.
- [x] ML/statistics algorithms (30%): `utils/ml_models.py`, Statistical Tests tab, chronological holdout, baseline, 3 regressors, CV, anomaly detection, KMeans segmentation.
- [x] Visualization and UI (10%): premium Streamlit styling in `assets/style.css` and `utils/styling.py`, shared Plotly template in `utils/charts.py`, 9 tabs and responsive charts.
- [x] Documentation and interpretation (20%): this README, technical documentation, final report, proposal, Methodology tab, computed “What this means” insights.
- [x] Accuracy and practical application (10%): held-out MAE/RMSE/R²/MAPE, baseline comparison, residuals, practical banking use case, limitations and guardrails.

Practical completion date: **30.09.2026**. Planned date in the proposal: **01.10.2026**.
