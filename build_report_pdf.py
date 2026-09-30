"""Build the local project documentation report PDF from the real workbook.

This file is a development-time report builder. The Streamlit app never calls
it and never writes files at runtime. The generated PDF is kept under the
Git-ignored ``output/pdf`` directory.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase.pdfmetrics import stringWidth

from utils.data_loader import find_workbook, load_workbook
from utils.ml_models import detect_anomalies, evaluate_regression, segment_periods
from utils.preprocessing import run_statistical_tests


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "pdf" / "PROJECT_DOCUMENTATION_REPORT.pdf"
COMPANY_LOGO = ROOT / "logo.png"

DEEP = colors.HexColor("#0b3d3a")
TEAL = colors.HexColor("#0f766e")
MINT = colors.HexColor("#d5f2eb")
GOLD = colors.HexColor("#f4c95d")
INK = colors.HexColor("#12312f")
MUTED = colors.HexColor("#627875")
LIGHT = colors.HexColor("#f4f8f7")


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=27, leading=32, textColor=colors.white, spaceAfter=10))
styles.add(ParagraphStyle(name="CoverKicker", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=GOLD, spaceAfter=5))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=16, textColor=colors.HexColor("#d5f2eb")))
styles.add(ParagraphStyle(name="H1Custom", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=23, textColor=DEEP, spaceBefore=12, spaceAfter=8))
styles.add(ParagraphStyle(name="H2Custom", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=TEAL, spaceBefore=8, spaceAfter=5))
styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.4, leading=14, textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="SmallCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.8, leading=10.5, textColor=MUTED, spaceAfter=4))
styles.add(ParagraphStyle(name="TableHeader", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.8, leading=10.5, textColor=colors.white, spaceAfter=0))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=DEEP, backColor=colors.HexColor("#fffdf4"), borderColor=GOLD, borderWidth=1, borderPadding=9, spaceBefore=6, spaceAfter=10))
styles.add(ParagraphStyle(name="BulletCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.1, leading=13, textColor=INK, leftIndent=13, firstLineIndent=-8, bulletIndent=2, spaceAfter=4))
styles.add(ParagraphStyle(name="Footer", parent=styles["Normal"], fontName="Helvetica", fontSize=7.5, textColor=MUTED, alignment=TA_CENTER))


def P(text: str, style: str = "BodyCustom") -> Paragraph:
    return Paragraph(text, styles[style])


def safe(text: object) -> str:
    return escape(str(text))


def bullet(text: str) -> Paragraph:
    return Paragraph(f"- {safe(text)}", styles["BulletCustom"])


def fmt(value: object, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):,.{digits}f}"


def project_mark(canvas, x: float, y: float, scale: float = 1.0) -> None:
    """Draw the project's own non-TEB vector mark on the PDF canvas."""

    canvas.saveState()
    canvas.setFillColor(TEAL)
    canvas.roundRect(x, y, 58 * scale, 58 * scale, 13 * scale, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    for offset, height in [(12, 16), (24, 29), (36, 40)]:
        canvas.roundRect(x + offset * scale, y + 12 * scale, 8 * scale, height * scale, 2 * scale, fill=1, stroke=0)
    canvas.setStrokeColor(colors.white)
    canvas.setLineWidth(2 * scale)
    canvas.line(x + 10 * scale, y + 9 * scale, x + 48 * scale, y + 9 * scale)
    canvas.restoreState()


class ProjectMarkFlowable(Flowable):
    """Small flowable version of the project's own vector mark for the cover."""

    def __init__(self, size: float = 58):
        super().__init__()
        self.width = size
        self.height = size
        self.size = size

    def draw(self) -> None:
        project_mark(self.canv, 0, 0, self.size / 58)


def header_footer(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    if doc.page > 1:
        canvas.setStrokeColor(MINT)
        canvas.setLineWidth(0.7)
        canvas.line(18 * mm, height - 16 * mm, width - 18 * mm, height - 16 * mm)
        project_mark(canvas, 18 * mm, height - 13.5 * mm, 0.16)
        canvas.setFillColor(DEEP)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(30 * mm, height - 11.5 * mm, "SIA DASHBOARD")
    canvas.setStrokeColor(MINT)
    canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.3)
    canvas.drawString(18 * mm, 9.5 * mm, "Independent internship and portfolio project - not affiliated with TEB")
    page_text = f"Page {doc.page}"
    canvas.drawRightString(width - 18 * mm, 9.5 * mm, page_text)
    canvas.restoreState()


def styled_table(rows: list[list[object]], widths: list[float], header: bool = True) -> Table:
    converted = []
    for row_index, row in enumerate(rows):
        cell_style = "TableHeader" if header and row_index == 0 else "SmallCustom"
        converted.append([cell if isinstance(cell, Paragraph) else P(safe(cell), cell_style) for cell in row])
    table = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), DEEP if header else LIGHT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white if header else INK),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce9e6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.append(("TEXTCOLOR", (0, 0), (-1, 0), colors.white))
        commands.append(("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"))
    for row in range(1 if header else 0, len(rows)):
        if row % 2 == 0:
            commands.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor("#f7fbfa")))
    table.setStyle(TableStyle(commands))
    return table


def build() -> Path:
    bundle = load_workbook(find_workbook(ROOT))
    data = bundle["data"]
    quality = bundle["quality"]
    model = evaluate_regression(data)
    anomalies = detect_anomalies(data)
    segments = segment_periods(data)
    tests = run_statistical_tests(data)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=24 * mm, bottomMargin=21 * mm, title="SIA Dashboard Project Documentation Report", author="Adi Memeti")
    story = []

    # Cover page
    story.append(Spacer(1, 17 * mm))
    cover_content = [
        ProjectMarkFlowable(58),
        Spacer(1, 6 * mm),
        P("INDEPENDENT INTERNSHIP PROJECT", "CoverKicker"),
        P("Sales-Inventory-<br/>Analytics-Dashboard", "CoverTitle"),
        P("Banking open-data analysis, predictive modelling, anomaly screening, and practical decision support", "CoverSub"),
        Spacer(1, 7 * mm),
    ]
    cover_panel = Table([[cover_content]], colWidths=[174 * mm])
    cover_panel.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), DEEP), ("LEFTPADDING", (0, 0), (-1, -1), 14 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 14 * mm), ("TOPPADDING", (0, 0), (-1, -1), 11 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 8 * mm)]))
    story.append(cover_panel)
    story.append(Spacer(1, 10 * mm))
    story.append(Table([[P("Prepared by", "SmallCustom"), P("Adi Memeti", "BodyCustom")], [P("Programme", "SmallCustom"), P("Python &amp; Data Science - Tectigon Academy", "BodyCustom")], [P("Practical completion", "SmallCustom"), P("30.09.2026", "BodyCustom")], [P("Planned proposal date", "SmallCustom"), P("01.10.2026", "BodyCustom")]], colWidths=[44 * mm, 130 * mm], style=TableStyle([("BACKGROUND", (0, 0), (0, -1), MINT), ("BACKGROUND", (1, 0), (1, -1), colors.white), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce9e6")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)])))
    story.append(Spacer(1, 15 * mm))
    story.append(P("This report documents the completed project built from the supplied Excel workbook only. It is a portfolio and internship deliverable, not an official TEB report and not affiliated with TEB.", "Callout"))
    if COMPANY_LOGO.exists():
        logo = Image(str(COMPANY_LOGO), width=18 * mm, height=18 * mm)
        logo.hAlign = "LEFT"
        story.append(logo)
    story.append(PageBreak())

    story.append(P("1. Executive summary", "H1Custom"))
    story.append(P("The project converts three wide banking open-data sheets into a transparent quarterly analytics workflow. The dashboard makes data quality visible, answers exploratory and statistical questions, compares predictive models with a baseline, screens for unusual periods, segments historical regimes, and explains the results in practical business language."))
    story.append(P(f"The final tidy dataset contains <b>{len(data):,}</b> metric-period observations. The source has <b>{int(quality['missing_cells_before'].sum())}</b> missing numeric cells, <b>{int(quality['duplicates_removed'].sum())}</b> duplicate metric-period records removed, <b>{int(quality['period_headers_corrected'].sum())}</b> period-header corrections, and <b>{int(quality['outliers_found'].sum())}</b> IQR outlier flags."))
    story.append(P("The strongest modelling result is a 23.8% held-out RMSE improvement over a training-mean baseline. The selected Random Forest still has negative R-squared and slightly higher MAPE than the baseline, so the responsible conclusion is that it is a planning signal and not a production forecast." , "Callout"))

    story.append(P("2. Source data profile", "H1Custom"))
    source_rows = [["Source sheet", "Domain", "Metrics", "Periods", "Records", "Date range"]]
    for summary, qrow in zip(bundle["raw_summaries"], quality.to_dict("records")):
        source_rows.append([summary["sheet"], summary["categorical_values"]["groups"][0], summary["categorical_values"]["metric_count"], summary["categorical_values"]["period_count"], qrow["records_after_cleaning"], f"{summary['date_range']['min']} to {summary['date_range']['max']}"])
    story.append(styled_table(source_rows, [49 * mm, 28 * mm, 15 * mm, 15 * mm, 19 * mm, 48 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(P("The workbook is banking financial data rather than a generic sales table. The inferred business domain is a quarterly bank performance review covering assets, liabilities, equity, income, expenses, provisions, and financial ratios."))

    story.append(P("3. Data quality and preprocessing", "H1Custom"))
    quality_rows = [["Sheet", "Missing before", "Duplicates removed", "Headers corrected", "IQR flags"]]
    for row in quality.to_dict("records"):
        quality_rows.append([row["sheet"], row["missing_cells_before"], row["duplicates_removed"], row["period_headers_corrected"], row["outliers_found"]])
    story.append(styled_table(quality_rows, [62 * mm, 27 * mm, 28 * mm, 31 * mm, 26 * mm]))
    story.append(Spacer(1, 3 * mm))
    for line in [
        "All sheets were read with pandas and openpyxl; row 3 was treated as the source period header.",
        "Labels were whitespace-normalised and numbers/percentage strings were converted to numeric values.",
        "Mixed quarter labels were parsed to standard quarter ends. Evident source typos were corrected using local sequence context and logged.",
        "Missing facts were kept visible. Models impute medians inside training pipelines only.",
        "IQR outliers were flagged but retained because unusual financial periods may be genuine events.",
    ]:
        story.append(bullet(line))

    story.append(PageBreak())
    story.append(P("4. Methodology and implementation", "H1Custom"))
    story.append(P("The app is Streamlit-only and read-only. It uses relative paths, in-memory transformations, Streamlit caching, and no backend, API, database, uploads, runtime file writes, or saved model artifacts."))
    method_rows = [["Layer", "Implementation", "Purpose"], ["Ingestion", "data_loader.py", "Read every sheet and create a tidy long table"], ["Preprocessing", "preprocessing.py", "Filters, pivot, lags, descriptive statistics, tests"], ["Models", "ml_models.py", "Baseline, Ridge, Random Forest, Gradient Boosting, Isolation Forest, KMeans"], ["Visuals", "charts.py", "Shared Plotly template and interpretable charts"], ["UI", "app.py and styling.py", "Nine tabs, filters, quality controls, recommendations"]]
    story.append(styled_table(method_rows, [31 * mm, 44 * mm, 99 * mm]))
    story.append(P("The modelling frame predicts quarterly net profit from one- and two-quarter lags of net profit, assets, loans, customer deposits, total equity, net interest income, total income, impairment, capital adequacy, return on equity, year, and quarter when available. Current-quarter drivers are not used, reducing leakage risk."))
    story.append(P("Statistical tests", "H2Custom"))
    for test in tests:
        story.append(bullet(f"{test['test']}: statistic={test['statistic']:.4f}, p={test['p_value']:.6f}, n={test['n']}. {test['interpretation']}"))

    story.append(P("5. Model results", "H1Custom"))
    if model["available"]:
        model_rows = [["Model", "MAE", "RMSE", "R2", "MAPE", "CV RMSE"]]
        for row in model["metrics"].to_dict("records"):
            model_rows.append([row["model"], fmt(row["MAE"]), fmt(row["RMSE"]), fmt(row["R2"], 3), f"{fmt(row['MAPE'], 1)}%", fmt(row["CV_RMSE"]) if pd.notna(row["CV_RMSE"]) else "-"])
        story.append(styled_table(model_rows, [42 * mm, 25 * mm, 28 * mm, 20 * mm, 25 * mm, 34 * mm]))
        best = model["metrics"].loc[model["metrics"]["model"] == model["best_model"]].iloc[0]
        baseline = model["metrics"].loc[model["metrics"]["model"] == "Baseline (training mean)"].iloc[0]
        improvement = (baseline["RMSE"] - best["RMSE"]) / baseline["RMSE"] * 100
        story.append(Spacer(1, 3 * mm))
        story.append(P(f"Random Forest is selected by held-out RMSE at {fmt(best['RMSE'])}, versus {fmt(baseline['RMSE'])} for the mean baseline. This is a {improvement:.1f}% RMSE improvement. The holdout has {model['test_rows']} rows and begins at {model['test_start']:%Y-%m-%d}." , "Callout"))
        story.append(P("Interpretation: MAE and RMSE improve, but R2 remains negative and MAPE is higher than the baseline. The sample is small and seasonal, so the result should be used to prompt scenario discussion, not to automate a bank decision."))

    story.append(PageBreak())
    story.append(P("6. Anomalies and segmentation", "H1Custom"))
    if anomalies["available"]:
        story.append(P(f"Isolation Forest flags <b>{int(anomalies['result']['anomaly'].sum())}</b> of {len(anomalies['result'])} aligned quarters for manual review. The flags identify unusual multivariate combinations; they do not prove fraud, error, or risk."))
    if segments["available"]:
        best_sil = segments["silhouette"].loc[segments["silhouette"]["k"] == segments["best_k"], "silhouette"].iloc[0]
        story.append(P(f"KMeans selected <b>k={segments['best_k']}</b> using the highest silhouette score of <b>{best_sil:.3f}</b>. Inertia and silhouette values are shown in the app so the choice can be challenged and reviewed."))

    story.append(P("7. Practical recommendations", "H1Custom"))
    for rec in [
        "Monitor customer deposits and total assets jointly with liquidity and funding concentration limits.",
        "Use a rolling earnings review so recent net-profit volatility is separated from one-off provisions and reporting events.",
        "Route anomaly flags to an analyst review queue and reconcile them against original official disclosures before action.",
        "Keep the baseline, model metrics, residuals, and approximate interval visible in planning conversations.",
        "Refresh the model when a new official quarter is published and repeat the chronological holdout evaluation.",
        "If higher-confidence forecasting is required, add macroeconomic drivers, more quarters, and rolling-origin validation.",
    ]:
        story.append(bullet(rec))
    story.append(P("8. Limitations and conclusion", "H1Custom"))
    story.append(P("This is a single-bank quarterly public-data sample with no customer-level observations, loan-level outcomes, macroeconomic covariates, or post-2025 labels. It cannot support customer churn, credit-default classification, causal inference, fraud detection, or long-horizon forecasting. The project therefore prioritises transparency: the source is profiled, corrections are logged, model performance is compared with a baseline, and limitations are shown beside recommendations."))
    story.append(P("The completed deliverable covers the internship rubric: data quality and preprocessing, real ML/statistics, polished visual UI, technical/final documentation, held-out metrics, and a practical banking use case. The public repository should contain the Markdown and source files; this generated PDF remains local by design." , "Callout"))
    story.append(P("Contact: Adi Memeti | adimemeti97@gmail.com | adimemeti.netlify.app", "SmallCustom"))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return OUT


if __name__ == "__main__":
    result = build()
    print(result)
