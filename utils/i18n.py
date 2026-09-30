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


def language_selector() -> str:
    """Render a compact language switcher and return the active locale."""

    current = st.session_state.get("locale", "en")
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
    st.session_state["locale"] = locale
    return locale


def t(text: str, locale: str = "en") -> str:
    return TRANSLATIONS.get(locale, {}).get(text, text)
