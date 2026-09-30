"""Small, dependency-free UI translation layer for the dashboard."""

from __future__ import annotations

import streamlit as st


LANGUAGES = {"English": "en", "Shqip": "sq", "Deutsch": "de"}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "sq": {
        "Language": "Gjuha",
        "Independent analytics project": "Projekt i pavarur analitik",
        "Practical completion: 30.09.2026": "Përfundimi praktik: 30.09.2026",
        "Planned date: 01.10.2026": "Data e planifikuar: 01.10.2026",
        "Public-data controls": "Kontrollet e të dhënave publike",
        "Filters update the analysis in memory. The Excel workbook remains the only data source.": "Filtrat përditësojnë analizën në memorie. Workbook-u Excel mbetet burimi i vetëm i të dhënave.",
        "Source sheets": "Fletët burimore",
        "Data domains": "Domenet e të dhënave",
        "Year range": "Intervali i viteve",
        "Metric search": "Kërko metrikë",
        "Metrics (optional)": "Metrikat (opsionale)",
        "e.g. profit, loans, capital": "p.sh. fitim, kredi, kapital",
        "Overview": "Përmbledhje",
        "Data Quality": "Cilësia e të dhënave",
        "Exploratory Analysis": "Analiza eksploruese",
        "Statistical Tests": "Testet statistikore",
        "Machine Learning": "Mësimi makinerik",
        "Anomalies & Segments": "Anomalitë dhe segmentet",
        "Insights & Recommendations": "Gjetje dhe rekomandime",
        "Methodology": "Metodologjia",
        "Data Explorer": "Eksploruesi i të dhënave",
        "Executive overview": "Përmbledhje ekzekutive",
        "Data quality & preprocessing": "Cilësia dhe parapërpunimi i të dhënave",
        "Exploratory analysis": "Analiza eksploruese",
        "Statistical tests": "Testet statistikore",
        "Machine learning": "Mësimi makinerik",
        "Anomalies & segments": "Anomalitë dhe segmentet",
        "Insights & recommendations": "Gjetje dhe rekomandime",
        "Data explorer": "Eksploruesi i të dhënave",
        "No observations match the current sidebar filters. Expand the filters to continue.": "Asnjë vëzhgim nuk përputhet me filtrat aktualë. Zgjero filtrat për të vazhduar.",
        "No numeric observations are available for the current filters.": "Nuk ka vëzhgime numerike për filtrat aktualë.",
        "No rows match the current filters.": "Asnjë rresht nuk përputhet me filtrat aktualë.",
        "Download filtered CSV (in memory)": "Shkarko CSV-në e filtruar (në memorie)",
        "Independent banking analytics portfolio project": "Projekt i pavarur portfolio për analitikën bankare",
        "Decision intelligence workspace": "Hapësirë për inteligjencën e vendimmarrjes",
        "filtered observations": "vëzhgime të filtruara",
        "Source workbook": "Workbook-u burimor",
        "Data Science Internship": "Praktikë në Data Science",
        "TEB Open Data": "Të dhëna të hapura TEB",
        "ML + Analytics": "ML + Analitikë",
        "Latest period": "Periudha e fundit",
        "Observed quarters": "Tremujorë të vëzhguar",
        "Total assets": "Aktivet totale",
        "Net profit": "Fitimi neto",
        "Best model": "Modeli më i mirë",
        "Held-out RMSE": "RMSE i testimit",
        "Held-out R²": "R² i testimit",
        "Vs baseline": "Kundrejt bazës",
    },
    "de": {
        "Language": "Sprache",
        "Independent analytics project": "Unabhängiges Analyseprojekt",
        "Practical completion: 30.09.2026": "Praktischer Abschluss: 30.09.2026",
        "Planned date: 01.10.2026": "Geplantes Datum: 01.10.2026",
        "Public-data controls": "Steuerung öffentlicher Daten",
        "Filters update the analysis in memory. The Excel workbook remains the only data source.": "Filter aktualisieren die Analyse im Speicher. Die Excel-Arbeitsmappe bleibt die einzige Datenquelle.",
        "Source sheets": "Quellblätter",
        "Data domains": "Datenbereiche",
        "Year range": "Jahresbereich",
        "Metric search": "Metrik suchen",
        "Metrics (optional)": "Metriken (optional)",
        "e.g. profit, loans, capital": "z. B. Gewinn, Kredite, Kapital",
        "Overview": "Übersicht",
        "Data Quality": "Datenqualität",
        "Exploratory Analysis": "Explorative Analyse",
        "Statistical Tests": "Statistische Tests",
        "Machine Learning": "Maschinelles Lernen",
        "Anomalies & Segments": "Anomalien & Segmente",
        "Insights & Recommendations": "Erkenntnisse & Empfehlungen",
        "Methodology": "Methodik",
        "Data Explorer": "Datenexplorer",
        "Executive overview": "Managementübersicht",
        "Data quality & preprocessing": "Datenqualität & Vorverarbeitung",
        "Exploratory analysis": "Explorative Analyse",
        "Statistical tests": "Statistische Tests",
        "Machine learning": "Maschinelles Lernen",
        "Anomalies & segments": "Anomalien & Segmente",
        "Insights & recommendations": "Erkenntnisse & Empfehlungen",
        "Data explorer": "Datenexplorer",
        "No observations match the current sidebar filters. Expand the filters to continue.": "Keine Beobachtungen entsprechen den aktuellen Filtern. Erweitere die Filter, um fortzufahren.",
        "No numeric observations are available for the current filters.": "Für die aktuellen Filter sind keine numerischen Beobachtungen verfügbar.",
        "No rows match the current filters.": "Keine Zeilen entsprechen den aktuellen Filtern.",
        "Download filtered CSV (in memory)": "Gefilterte CSV herunterladen (im Speicher)",
        "Independent banking analytics portfolio project": "Unabhängiges Portfolio-Projekt für Bankanalysen",
        "Decision intelligence workspace": "Arbeitsbereich für Entscheidungsintelligenz",
        "filtered observations": "gefilterte Beobachtungen",
        "Source workbook": "Quell-Arbeitsmappe",
        "Data Science Internship": "Data-Science-Praktikum",
        "TEB Open Data": "Offene TEB-Daten",
        "ML + Analytics": "ML + Analytik",
        "Latest period": "Letzter Zeitraum",
        "Observed quarters": "Beobachtete Quartale",
        "Total assets": "Bilanzsumme",
        "Net profit": "Nettogewinn",
        "Best model": "Bestes Modell",
        "Held-out RMSE": "RMSE im Testzeitraum",
        "Held-out R²": "R² im Testzeitraum",
        "Vs baseline": "Gegenüber Basiswert",
    },
}


_BASE_EN = {
    "page_title": "SIA Dashboard | Banking Analytics",
    "Language": "Language",
    "hero_title": "Sales-Inventory Analytics",
    "hero_subtitle": "Quarterly intelligence and predictive modelling from the supplied TEB open-data workbook.",
    "Decision intelligence workspace": "Decision intelligence workspace",
    "Independent banking analytics portfolio project": "Independent banking analytics portfolio project",
    "Data Science Internship": "Data Science Internship",
    "TEB Open Data": "TEB Open Data",
    "ML + Analytics": "ML + Analytics",
    "Source workbook": "Source workbook",
    "filtered observations": "filtered observations",
    "Public-data controls": "Public-data controls",
    "Filters update the analysis in memory. The Excel workbook remains the only data source.": "Filters update the analysis in memory. The Excel workbook remains the only data source.",
    "Source sheets": "Source sheets",
    "Data domains": "Data domains",
    "Year range": "Year range",
    "Metric search": "Metric search",
    "Metrics (optional)": "Metrics (optional)",
    "e.g. profit, loans, capital": "e.g. profit, loans, capital",
    "Independent analytics project": "Independent analytics project",
    "Practical completion: 30.09.2026": "Practical completion: 30.09.2026",
    "Planned date: 01.10.2026": "Planned date: 01.10.2026",
    "Overview": "Overview",
    "Data Quality": "Data Quality",
    "Exploratory Analysis": "Exploratory Analysis",
    "Statistical Tests": "Statistical Tests",
    "Machine Learning": "Machine Learning",
    "Anomalies & Segments": "Anomalies & Segments",
    "Insights & Recommendations": "Insights & Recommendations",
    "Methodology": "Methodology",
    "Data Explorer": "Data Explorer",
    "Executive overview": "Executive overview",
    "Data quality & preprocessing": "Data quality & preprocessing",
    "Exploratory analysis": "Exploratory analysis",
    "Statistical tests": "Statistical tests",
    "Machine learning": "Machine learning",
    "Anomalies & segments": "Anomalies & segments",
    "Insights & recommendations": "Insights & recommendations",
    "Data explorer": "Data explorer",
    "No observations match the current sidebar filters. Expand the filters to continue.": "No observations match the current sidebar filters. Expand the filters to continue.",
    "No numeric observations are available for the current filters.": "No numeric observations are available for the current filters.",
    "No rows match the current filters.": "No rows match the current filters.",
    "Not enough data after the current filters.": "Not enough data after the current filters.",
    "Download filtered CSV (in memory)": "Download filtered CSV (in memory)",
    "Latest period": "Latest period",
    "Observed quarters": "Observed quarters",
    "Total assets": "Total assets",
    "Net profit": "Net profit",
    "Best model": "Best model",
    "Held-out RMSE": "Held-out RMSE",
    "Held-out R²": "Held-out R²",
    "Vs baseline": "Vs baseline",
    "Source sheets KPI": "All workbook sheets read",
    "Clean records KPI": "Long-format records",
    "Missing cells KPI": "Source values kept visible",
    "Outliers flagged KPI": "IQR flags, not deleted",
    "Latest period KPI": "Latest period in current filters",
    "Observed quarters KPI": "Unique cleaned periods",
    "Total assets KPI": "Latest aligned reported value",
    "Net profit KPI": "Latest aligned reported value",
    "Before / after by source sheet": "Before / after by source sheet",
    "Cleaning log": "Cleaning log",
    "Source-sheet inventory": "Source-sheet inventory",
    "Full source profile": "Full source profile",
    "Descriptive statistics": "Descriptive statistics",
    "Questions answered": "Questions answered",
    "Held-out predictions": "Held-out predictions",
    "Cluster diagnostics": "Cluster diagnostics",
    "Practical banking use case": "Practical banking use case",
    "Guardrails": "Guardrails",
    "Reproducibility": "Reproducibility",
    "footer_disclaimer": "Independent internship & portfolio project built on TEB open data. Not affiliated with TEB.",
    "footer_author": "SIA Dashboard • 2026",
    "Balance-sheet scale over time": "Balance-sheet scale over time",
    "Net profit trend": "Net profit trend",
    "Largest balance-sheet items": "Largest balance-sheet items",
    "Income statement composition": "Income statement composition",
    "Selected financial indicators": "Selected financial indicators",
    "Income-statement value distribution": "Income-statement value distribution",
    "Cross-metric correlation heatmap": "Cross-metric correlation heatmap",
    "Latest indicator values": "Latest indicator values",
    "Quality checks by source sheet": "Quality checks by source sheet",
    "Held-out model comparison": "Held-out model comparison",
    "Held-out RMSE: lower is better": "Held-out RMSE: lower is better",
    "Actual vs predicted on held-out quarters": "Actual vs predicted on held-out quarters",
    "Residual diagnostics": "Residual diagnostics",
    "Residuals by held-out quarter": "Residuals by held-out quarter",
    "Top model drivers": "Top model drivers",
    "Anomaly timeline": "Anomaly timeline",
    "Segment timeline": "Segment timeline",
    "Financial-period segments": "Financial-period segments",
    "Reported value": "Reported value",
    "Quarter": "Quarter",
    "Metric": "Metric",
    "Model": "Model",
    "Flagged": "Flagged",
    "Cluster": "Cluster",
    "Actual - predicted": "Actual - predicted",
    "Value": "Value",
    "Date": "Date",
    "Raw value": "Raw value",
    "Outlier flag": "Outlier flag",
    "Corrected period": "Corrected period",
    "Balance sheet": "Balance sheet",
    "Income statement": "Income statement",
    "Financial indicators": "Financial indicators",
    "Not enough aligned observations": "The selected filters do not leave enough aligned observations for the configured tests.",
    "Tests are exploratory": "Tests are exploratory and use the observed quarterly sample.",
    "Quality checks are shown before modelling.": "Quality checks are shown before modelling.",
    "The EDA uses the filtered real observations": "The EDA uses the filtered real observations and separates balance-sheet scale, earnings, and reported financial indicators.",
    "This table is a filtered in-memory view.": "This table is a filtered in-memory view. The download is generated in memory and does not write to the app filesystem.",
}

_SQ = {
    "page_title": "SIA Dashboard | Analitika bankare",
    "hero_title": "Analitika Sales-Inventory",
    "hero_subtitle": "Inteligjencë tremujore dhe modelim parashikues nga workbook-u i të dhënave të hapura të TEB.",
    "Language": "Gjuha",
    "Decision intelligence workspace": "Hapësirë për inteligjencën e vendimmarrjes",
    "Independent banking analytics portfolio project": "Projekt i pavarur portfolio për analitikën bankare",
    "Data Science Internship": "Praktikë në Data Science",
    "TEB Open Data": "Të dhëna të hapura TEB",
    "ML + Analytics": "ML + Analitikë",
    "Source workbook": "Workbook-u burimor",
    "filtered observations": "vëzhgime të filtruara",
    "Public-data controls": "Kontrollet e të dhënave publike",
    "Filters update the analysis in memory. The Excel workbook remains the only data source.": "Filtrat përditësojnë analizën në memorie. Workbook-u Excel mbetet burimi i vetëm i të dhënave.",
    "Source sheets": "Fletët burimore", "Data domains": "Domenet e të dhënave", "Year range": "Intervali i viteve", "Metric search": "Kërko metrikë", "Metrics (optional)": "Metrikat (opsionale)", "e.g. profit, loans, capital": "p.sh. fitim, kredi, kapital",
    "Independent analytics project": "Projekt i pavarur analitik", "Practical completion: 30.09.2026": "Përfundimi praktik: 30.09.2026", "Planned date: 01.10.2026": "Data e planifikuar: 01.10.2026",
    "Overview": "Përmbledhje", "Data Quality": "Cilësia e të dhënave", "Exploratory Analysis": "Analiza eksploruese", "Statistical Tests": "Testet statistikore", "Machine Learning": "Mësimi makinerik", "Anomalies & Segments": "Anomalitë dhe segmentet", "Insights & Recommendations": "Gjetje dhe rekomandime", "Methodology": "Metodologjia", "Data Explorer": "Eksploruesi i të dhënave",
    "Executive overview": "Përmbledhje ekzekutive", "Data quality & preprocessing": "Cilësia dhe parapërpunimi i të dhënave", "Exploratory analysis": "Analiza eksploruese", "Statistical tests": "Testet statistikore", "Machine learning": "Mësimi makinerik", "Anomalies & segments": "Anomalitë dhe segmentet", "Insights & recommendations": "Gjetje dhe rekomandime", "Data explorer": "Eksploruesi i të dhënave",
    "No observations match the current sidebar filters. Expand the filters to continue.": "Asnjë vëzhgim nuk përputhet me filtrat aktualë. Zgjero filtrat për të vazhduar.", "No numeric observations are available for the current filters.": "Nuk ka vëzhgime numerike për filtrat aktualë.", "No rows match the current filters.": "Asnjë rresht nuk përputhet me filtrat aktualë.", "Not enough data after the current filters.": "Nuk ka të dhëna të mjaftueshme pas filtrave aktualë.", "Download filtered CSV (in memory)": "Shkarko CSV-në e filtruar (në memorie)",
    "Latest period": "Periudha e fundit", "Observed quarters": "Tremujorë të vëzhguar", "Total assets": "Aktivet totale", "Net profit": "Fitimi neto", "Best model": "Modeli më i mirë", "Held-out RMSE": "RMSE i testimit", "Held-out R²": "R² i testimit", "Vs baseline": "Kundrejt bazës", "Date": "Data", "Raw value": "Vlera bruto", "Outlier flag": "Flamuri i devijimit", "Corrected period": "Periudha e korrigjuar", "Balance sheet": "Bilanci", "Income statement": "Pasqyra e të ardhurave", "Financial indicators": "Treguesit financiarë",
    "Source sheets KPI": "Të gjitha fletët u lexuan", "Clean records KPI": "Rreshta në format të gjatë", "Missing cells KPI": "Vlerat burimore të dukshme", "Outliers flagged KPI": "Flamuj IQR, pa fshirje", "Latest period KPI": "Periudha e fundit në filtrat aktualë", "Observed quarters KPI": "Periudha të pastruara unike", "Total assets KPI": "Vlera e fundit e raportuar", "Net profit KPI": "Vlera e fundit e raportuar",
    "Before / after by source sheet": "Para / pas sipas fletës", "Cleaning log": "Regjistri i pastrimit", "Source-sheet inventory": "Inventari i fletëve", "Full source profile": "Profili i plotë burimor", "Descriptive statistics": "Statistika përshkruese", "Questions answered": "Pyetje të përgjigjura", "Held-out predictions": "Parashikime të testimit", "Cluster diagnostics": "Diagnostika e klasterëve", "Practical banking use case": "Përdorim praktik bankar", "Guardrails": "Kufizime", "Reproducibility": "Riprodhueshmëria",
    "footer_disclaimer": "Projekt i pavarur internship dhe portfolio mbi të dhënat e hapura të TEB. Nuk është i lidhur me TEB.", "footer_author": "SIA Dashboard • 2026",
    "Balance-sheet scale over time": "Shkalla e bilancit me kalimin e kohës", "Net profit trend": "Trendi i fitimit neto", "Largest balance-sheet items": "Zërat më të mëdhenj të bilancit", "Income statement composition": "Përbërja e pasqyrës së të ardhurave", "Selected financial indicators": "Tregues financiarë të zgjedhur", "Income-statement value distribution": "Shpërndarja e vlerave të të ardhurave", "Cross-metric correlation heatmap": "Hartë korrelacioni ndërmjet metrikave", "Latest indicator values": "Vlerat e fundit të treguesve", "Quality checks by source sheet": "Kontrollet e cilësisë sipas fletës", "Held-out model comparison": "Krahasimi i modeleve në testim", "Held-out RMSE: lower is better": "RMSE në testim: më e ulët është më mirë", "Actual vs predicted on held-out quarters": "Aktuale kundrejt parashikimit", "Residual diagnostics": "Diagnostika e mbetjeve", "Residuals by held-out quarter": "Mbetjet sipas tremujorit", "Top model drivers": "Faktorët kryesorë të modelit", "Anomaly timeline": "Ecuria e anomalive", "Segment timeline": "Ecuria e segmenteve", "Financial-period segments": "Segmente të periudhave financiare", "Reported value": "Vlera e raportuar", "Quarter": "Tremujori", "Metric": "Metrika", "Model": "Modeli", "Flagged": "E shënuar", "Cluster": "Klasteri", "Actual - predicted": "Aktuale - parashikuar", "Value": "Vlera",
}

_DE = {
    "page_title": "SIA Dashboard | Bankanalyse",
    "hero_title": "Sales-Inventory-Analytik", "hero_subtitle": "Quartalsintelligenz und Prognosemodellierung aus dem offenen TEB-Datensatz.", "Language": "Sprache", "Decision intelligence workspace": "Arbeitsbereich für Entscheidungsintelligenz", "Independent banking analytics portfolio project": "Unabhängiges Portfolio-Projekt für Bankanalysen", "Data Science Internship": "Data-Science-Praktikum", "TEB Open Data": "Offene TEB-Daten", "ML + Analytics": "ML + Analytik", "Source workbook": "Quell-Arbeitsmappe", "filtered observations": "gefilterte Beobachtungen", "Public-data controls": "Steuerung öffentlicher Daten", "Filters update the analysis in memory. The Excel workbook remains the only data source.": "Filter aktualisieren die Analyse im Speicher. Die Excel-Arbeitsmappe bleibt die einzige Datenquelle.", "Source sheets": "Quellblätter", "Data domains": "Datenbereiche", "Year range": "Jahresbereich", "Metric search": "Metrik suchen", "Metrics (optional)": "Metriken (optional)", "e.g. profit, loans, capital": "z. B. Gewinn, Kredite, Kapital", "Independent analytics project": "Unabhängiges Analyseprojekt", "Practical completion: 30.09.2026": "Praktischer Abschluss: 30.09.2026", "Planned date: 01.10.2026": "Geplantes Datum: 01.10.2026",
    "Overview": "Übersicht", "Data Quality": "Datenqualität", "Exploratory Analysis": "Explorative Analyse", "Statistical Tests": "Statistische Tests", "Machine Learning": "Maschinelles Lernen", "Anomalies & Segments": "Anomalien & Segmente", "Insights & Recommendations": "Erkenntnisse & Empfehlungen", "Methodology": "Methodik", "Data Explorer": "Datenexplorer", "Executive overview": "Managementübersicht", "Data quality & preprocessing": "Datenqualität & Vorverarbeitung", "Exploratory analysis": "Explorative Analyse", "Statistical tests": "Statistische Tests", "Machine learning": "Maschinelles Lernen", "Anomalies & segments": "Anomalien & Segmente", "Insights & recommendations": "Erkenntnisse & Empfehlungen", "Data explorer": "Datenexplorer", "No observations match the current sidebar filters. Expand the filters to continue.": "Keine Beobachtungen entsprechen den aktuellen Filtern. Erweitere die Filter, um fortzufahren.", "No numeric observations are available for the current filters.": "Für die aktuellen Filter sind keine numerischen Beobachtungen verfügbar.", "No rows match the current filters.": "Keine Zeilen entsprechen den aktuellen Filtern.", "Not enough data after the current filters.": "Nach den aktuellen Filtern sind nicht genügend Daten vorhanden.", "Download filtered CSV (in memory)": "Gefilterte CSV herunterladen (im Speicher)",
    "Latest period": "Letzter Zeitraum", "Observed quarters": "Beobachtete Quartale", "Total assets": "Bilanzsumme", "Net profit": "Nettogewinn", "Best model": "Bestes Modell", "Held-out RMSE": "RMSE im Testzeitraum", "Held-out R²": "R² im Testzeitraum", "Vs baseline": "Gegenüber Basiswert", "Date": "Datum", "Raw value": "Rohwert", "Outlier flag": "Ausreißer-Markierung", "Corrected period": "Korrigierter Zeitraum", "Balance sheet": "Bilanz", "Income statement": "Erfolgsrechnung", "Financial indicators": "Finanzindikatoren", "Source sheets KPI": "Alle Quellblätter gelesen", "Clean records KPI": "Datensätze im Langformat", "Missing cells KPI": "Quellwerte sichtbar", "Outliers flagged KPI": "IQR-Markierungen, nicht gelöscht", "Latest period KPI": "Letzter Zeitraum in den Filtern", "Observed quarters KPI": "Eindeutige bereinigte Zeiträume", "Total assets KPI": "Letzter Berichtswert", "Net profit KPI": "Letzter Berichtswert", "Before / after by source sheet": "Vorher / nachher je Quellblatt", "Cleaning log": "Bereinigungsprotokoll", "Source-sheet inventory": "Quellblatt-Inventar", "Full source profile": "Vollständiges Quellenprofil", "Descriptive statistics": "Deskriptive Statistik", "Questions answered": "Beantwortete Fragen", "Held-out predictions": "Vorhersagen im Testzeitraum", "Cluster diagnostics": "Clusterdiagnostik", "Practical banking use case": "Praktischer Bankanwendungsfall", "Guardrails": "Leitplanken", "Reproducibility": "Reproduzierbarkeit", "footer_disclaimer": "Unabhängiges Praktikums- und Portfolio-Projekt auf Basis offener TEB-Daten. Keine Verbindung zu TEB.", "footer_author": "SIA Dashboard • 2026",
    "Balance-sheet scale over time": "Bilanzentwicklung im Zeitverlauf", "Net profit trend": "Nettogewinntrend", "Largest balance-sheet items": "Größte Bilanzpositionen", "Income statement composition": "Zusammensetzung der Erfolgsrechnung", "Selected financial indicators": "Ausgewählte Finanzindikatoren", "Income-statement value distribution": "Verteilung der Erfolgsrechnungswerte", "Cross-metric correlation heatmap": "Korrelations-Heatmap der Metriken", "Latest indicator values": "Aktuelle Indikatorwerte", "Quality checks by source sheet": "Qualitätsprüfungen je Quellblatt", "Held-out model comparison": "Modellvergleich im Testzeitraum", "Held-out RMSE: lower is better": "RMSE im Testzeitraum: niedriger ist besser", "Actual vs predicted on held-out quarters": "Istwerte gegenüber Vorhersagen", "Residual diagnostics": "Residualdiagnostik", "Residuals by held-out quarter": "Residuen je Testquartal", "Top model drivers": "Wichtigste Modelltreiber", "Anomaly timeline": "Anomalieverlauf", "Segment timeline": "Segmentverlauf", "Financial-period segments": "Segmente der Finanzperioden", "Reported value": "Berichteter Wert", "Quarter": "Quartal", "Metric": "Metrik", "Model": "Modell", "Flagged": "Markiert", "Cluster": "Cluster", "Actual - predicted": "Istwert - Prognose", "Value": "Wert",
}

_previous = TRANSLATIONS
TRANSLATIONS = {
    "en": _BASE_EN,
    "sq": {**_BASE_EN, **_previous.get("sq", {}), **_SQ},
    "de": {**_BASE_EN, **_previous.get("de", {}), **_DE},
}

_EXTRA_EN = {
    "reported_figures_caption": "Reported figures retain the workbook's units; most statement values are reported in thousands where stated by the source.",
    "quality_caption": "Quality checks are shown before modelling. Outliers are flagged with the IQR rule and retained because unusual financial quarters may be economically meaningful.",
    "profile_caption": "Every source sheet was profiled for columns, raw cell dtypes, date coverage, missingness, duplicates, categorical metric labels, and numeric ranges.",
    "eda_caption": "The EDA uses the filtered real observations and separates balance-sheet scale, earnings, and reported financial indicators.",
    "tests_caption": "Tests are exploratory and use the observed quarterly sample. A p-value is evidence against a null hypothesis, not a measure of business importance.",
    "ml_caption": "Task: predict quarterly net profit from lagged balance-sheet, income-statement, and indicator drivers. A chronological holdout prevents future quarters from leaking into training.",
    "anomaly_caption": "These are screening tools. An anomaly is an unusual multivariate pattern, not a finding of misconduct; a segment is a statistical cluster, not a customer segment.",
    "explorer_caption": "This table is a filtered in-memory view. The download is generated in memory and does not write to the app filesystem.",
    "no_numeric": "No numeric observations are available for the current filters.",
    "not_enough_tests": "The selected filters do not leave enough aligned observations for the configured tests.",
    "no_recommendations": "Expand the filters to generate data-driven recommendations.",
    "no_rows": "No rows match the current filters.",
    "Actual": "Actual",
    "Best model trace": "Best model",
    "Approx. 95% interval": "Approx. 95% interval",
}
_EXTRA_SQ = {
    "reported_figures_caption": "Vlerat e raportuara ruajnë njësitë e workbook-ut; shumica e vlerave të pasqyrave raportohen në mijëra kur burimi e përcakton.",
    "quality_caption": "Kontrollet e cilësisë shfaqen para modelimit. Devijimet shënohen me rregullin IQR dhe ruhen sepse mund të jenë ekonomikisht të rëndësishme.",
    "profile_caption": "Çdo fletë burimore u profilizua për kolonat, tipet, datat, mungesat, dublikatat, metrikat dhe intervalet numerike.",
    "eda_caption": "EDA përdor vëzhgimet reale të filtruara dhe ndan shkallën e bilancit, fitimet dhe treguesit financiarë.",
    "tests_caption": "Testet janë eksploruese dhe përdorin kampionin tremujor. Vlera p është evidencë kundër hipotezës zero, jo matës i rëndësisë së biznesit.",
    "ml_caption": "Detyra: parashiko fitimin neto tremujor nga drejtues të vonuar të bilancit, të ardhurave dhe treguesve. Ndarja kronologjike shmang rrjedhjen e së ardhmes.",
    "anomaly_caption": "Këto janë mjete kontrolli. Anomalia është një model multivariat i pazakontë, jo provë shkeljeje; segmenti është klaster statistikor.",
    "explorer_caption": "Kjo tabelë është pamje e filtruar në memorie. Shkarkimi krijohet në memorie dhe nuk shkruan në filesystem.",
    "no_numeric": "Nuk ka vëzhgime numerike për filtrat aktualë.", "not_enough_tests": "Filtrat nuk lënë mjaftueshëm vëzhgime të lidhura për testet.", "no_recommendations": "Zgjero filtrat për të gjeneruar rekomandime të bazuara në të dhëna.", "no_rows": "Asnjë rresht nuk përputhet me filtrat aktualë.", "Actual": "Aktuale", "Best model trace": "Modeli më i mirë", "Approx. 95% interval": "Interval i përafërt 95%",
}
_EXTRA_DE = {
    "reported_figures_caption": "Berichtete Werte behalten die Einheiten der Arbeitsmappe; viele Werte werden laut Quelle in Tausend angegeben.",
    "quality_caption": "Qualitätsprüfungen werden vor der Modellierung angezeigt. Ausreißer werden mit der IQR-Regel markiert und nicht gelöscht.",
    "profile_caption": "Jedes Quellblatt wurde auf Spalten, Datentypen, Datumsabdeckung, fehlende Werte, Duplikate, Metriken und Zahlenbereiche geprüft.",
    "eda_caption": "Die EDA nutzt die gefilterten Beobachtungen und trennt Bilanzgröße, Ergebnis und Finanzindikatoren.",
    "tests_caption": "Die Tests sind explorativ und verwenden die beobachtete Quartalsstichprobe. Ein p-Wert ist Evidenz gegen eine Nullhypothese.",
    "ml_caption": "Aufgabe: Quartalsnettogewinn aus verzögerten Bilanz-, Ergebnis- und Indikatorvariablen prognostizieren. Ein chronologischer Holdout verhindert Zukunftslecks.",
    "anomaly_caption": "Dies sind Prüfwerkzeuge. Eine Anomalie ist ein ungewöhnliches Muster, kein Fehlverhalten; ein Segment ist ein statistischer Cluster.",
    "explorer_caption": "Diese Tabelle ist eine gefilterte Ansicht im Speicher. Der Download schreibt keine Datei in das App-Dateisystem.",
    "no_numeric": "Für die aktuellen Filter sind keine numerischen Beobachtungen verfügbar.", "not_enough_tests": "Die Filter lassen nicht genügend ausgerichtete Beobachtungen für die Tests übrig.", "no_recommendations": "Erweitere die Filter, um datenbasierte Empfehlungen zu erzeugen.", "no_rows": "Keine Zeilen entsprechen den aktuellen Filtern.", "Actual": "Istwert", "Best model trace": "Bestes Modell", "Approx. 95% interval": "Ungefähres 95%-Intervall",
}
for _lang, _extra in (("en", _EXTRA_EN), ("sq", _EXTRA_SQ), ("de", _EXTRA_DE)):
    TRANSLATIONS[_lang].update(_extra)


def language_selector() -> str:
    """Render a compact language switcher and return the active locale."""

    current = st.session_state.get("lang", st.session_state.get("locale", "en"))
    current_label = next((label for label, code in LANGUAGES.items() if code == current), "English")
    selected = st.radio(
        "Language",
        list(LANGUAGES),
        index=list(LANGUAGES).index(current_label),
        horizontal=True,
        label_visibility="collapsed",
        key="language_selector",
    )
    locale = LANGUAGES[selected]
    st.session_state["lang"] = locale
    st.session_state["locale"] = locale
    return locale


def t(key: str, locale: str | None = None, **kwargs) -> str:
    """Translate a key from the active session language, with English fallback."""

    active = locale or st.session_state.get("lang", "en")
    value = TRANSLATIONS.get(active, {}).get(key, TRANSLATIONS["en"].get(key, key))
    return value.format(**kwargs) if kwargs else value


def format_number(value: float | int, decimals: int = 1, locale: str | None = None) -> str:
    """Format numbers with English or continental separators."""

    active = locale or st.session_state.get("lang", "en")
    formatted = f"{value:,.{decimals}f}"
    if active in {"sq", "de"}:
        formatted = formatted.replace(",", "§").replace(".", ",").replace("§", ".")
    return formatted


def metric_label(name: str, locale: str | None = None) -> str:
    """Translate workbook metric names using stable English labels as keys."""

    normalized = str(name).strip().lower()
    known = {
        "total assets": {"sq": "Aktivet totale", "de": "Bilanzsumme"},
        "customer deposits": {"sq": "Depozitat e klientëve", "de": "Kundeneinlagen"},
        "loans and advances": {"sq": "Kredi dhe paradhënie", "de": "Kredite und Vorschüsse"},
        "net profit": {"sq": "Fitimi neto", "de": "Nettogewinn"},
        "return on assets": {"sq": "Kthimi mbi aktivet", "de": "Eigenkapitalrendite"},
        "return on equity": {"sq": "Kthimi mbi kapitalin", "de": "Eigenkapitalrendite"},
        "capital adequacy": {"sq": "Mjaftueshmëria e kapitalit", "de": "Kapitaladäquanz"},
        "net interest margin": {"sq": "Marzhi neto i interesit", "de": "Nettozinsmarge"},
    }
    active = locale or st.session_state.get("lang", "en")
    return known.get(normalized, {}).get(active, name)


def build_metric_translation_map(data) -> dict[str, dict[str, str]]:
    """Build a stable mapping for every metric name read from the workbook."""

    names = sorted(set(data.get("metric_english", data.get("metric", [])).dropna().astype(str)))
    return {name: {lang: metric_label(name, lang) for lang in ("en", "sq", "de")} for name in names}
