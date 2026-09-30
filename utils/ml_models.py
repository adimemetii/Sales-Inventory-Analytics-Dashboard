"""In-memory modelling utilities for the dashboard.

Models are fitted on each run (and cached by Streamlit at the app layer). No
pickle, model artifact, database, or runtime output file is created.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor, IsolationForest, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score

from .preprocessing import build_model_frame, pivot_financial_data


def _mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean absolute percentage error, excluding zero actual values."""

    denominator = np.where(np.abs(actual) < 1e-9, np.nan, np.abs(actual))
    value = np.nanmean(np.abs((actual - predicted) / denominator)) * 100
    return float(value) if np.isfinite(value) else float("nan")


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "RMSE": float(np.sqrt(mean_squared_error(actual, predicted))),
        "R2": float(r2_score(actual, predicted)) if len(actual) > 1 else float("nan"),
        "MAPE": _mape(actual, predicted),
    }


def _extract_importance(model: Pipeline, feature_names: list[str]) -> pd.DataFrame:
    """Extract comparable feature contributions from linear/tree estimators."""

    estimator = model.named_steps["model"]
    if hasattr(estimator, "feature_importances_"):
        values = estimator.feature_importances_
    elif hasattr(estimator, "coef_"):
        values = np.abs(np.asarray(estimator.coef_)).ravel()
    else:
        values = np.zeros(len(feature_names))
    return (
        pd.DataFrame({"feature": feature_names, "importance": values})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def evaluate_regression(data: pd.DataFrame) -> dict[str, Any]:
    """Evaluate baseline plus three regressors with a chronological holdout."""

    frame, selected_metrics, feature_columns = build_model_frame(data)
    empty = {
        "available": False,
        "message": "The workbook does not provide enough aligned quarterly observations for regression.",
        "frame": frame,
        "selected_metrics": selected_metrics,
        "feature_columns": feature_columns,
        "metrics": pd.DataFrame(),
        "predictions": pd.DataFrame(),
        "importance": pd.DataFrame(),
        "cv_scores": pd.DataFrame(),
        "best_model": None,
    }
    if frame.empty or len(frame) < 12 or len(feature_columns) == 0:
        return empty

    split = max(int(len(frame) * 0.8), len(frame) - 8)
    split = min(split, len(frame) - 4)
    train = frame.iloc[:split].copy()
    test = frame.iloc[split:].copy()
    X_train, X_test = train[feature_columns], test[feature_columns]
    y_train, y_test = train["target"].to_numpy(), test["target"].to_numpy()
    baseline_pred = np.full(len(test), float(np.nanmean(y_train)))

    model_defs: dict[str, Pipeline] = {
        "Ridge Regression": Pipeline(
            [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()), ("model", Ridge(alpha=1.0))]
        ),
        "Random Forest": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("model", RandomForestRegressor(n_estimators=250, max_depth=5, min_samples_leaf=2, random_state=42, n_jobs=1)),
            ]
        ),
        "Gradient Boosting": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("model", GradientBoostingRegressor(n_estimators=120, learning_rate=0.04, max_depth=2, random_state=42, loss="huber")),
            ]
        ),
    }

    predictions: dict[str, np.ndarray] = {"Baseline (training mean)": baseline_pred}
    rows: list[dict[str, Any]] = [{"model": "Baseline (training mean)", **_metrics(y_test, baseline_pred), "CV_RMSE": np.nan}]
    cv_rows: list[dict[str, Any]] = []
    n_splits = min(4, max(2, len(train) // 8))
    tscv = TimeSeriesSplit(n_splits=n_splits)
    fitted: dict[str, Pipeline] = {}
    for name, model in model_defs.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        predictions[name] = pred
        cv_rmse = float(-cross_val_score(model, X_train, y_train, cv=tscv, scoring="neg_root_mean_squared_error").mean())
        rows.append({"model": name, **_metrics(y_test, pred), "CV_RMSE": cv_rmse})
        cv_rows.append({"model": name, "CV_RMSE": cv_rmse})
        fitted[name] = model

    metrics_df = pd.DataFrame(rows).sort_values("RMSE").reset_index(drop=True)
    best_model = str(metrics_df.loc[metrics_df["model"] != "Baseline (training mean)", "model"].iloc[0])
    best_pred = predictions[best_model]
    residuals = y_test - best_pred
    interval = 1.96 * float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0
    pred_df = pd.DataFrame(
        {
            "date": test["date"].to_numpy(),
            "actual": y_test,
            "baseline": baseline_pred,
            "best_prediction": best_pred,
            "residual": residuals,
            "lower": best_pred - interval,
            "upper": best_pred + interval,
        }
    )
    importance = _extract_importance(fitted[best_model], feature_columns)
    return {
        "available": True,
        "message": "Models evaluated on a chronological held-out period.",
        "frame": frame,
        "selected_metrics": selected_metrics,
        "feature_columns": feature_columns,
        "metrics": metrics_df,
        "predictions": pred_df,
        "importance": importance,
        "cv_scores": pd.DataFrame(cv_rows),
        "best_model": best_model,
        "train_rows": len(train),
        "test_rows": len(test),
        "train_end": train["date"].max(),
        "test_start": test["date"].min(),
    }


def detect_anomalies(data: pd.DataFrame) -> dict[str, Any]:
    """Flag unusual quarters using Isolation Forest on aligned financial metrics."""

    wide = pivot_financial_data(data)
    if wide.empty:
        return {"available": False, "message": "No aligned financial metrics are available for anomaly detection.", "result": pd.DataFrame()}
    preferred = [
        col for col in wide.columns if any(term in col for term in ("total_assets", "net_profit", "customer_deposits", "capital_adequacy", "total_income"))
    ]
    cols = preferred[:8] if len(preferred) >= 2 else [col for col in wide.columns if wide[col].notna().sum() >= 8][:8]
    if len(cols) < 2 or len(wide) < 8:
        return {"available": False, "message": "At least eight quarters and two numeric metrics are needed for anomaly detection.", "result": pd.DataFrame()}
    features = wide[cols].copy().replace([np.inf, -np.inf], np.nan)
    features = features.loc[:, features.notna().sum() >= max(5, int(len(features) * 0.6))]
    features = features.fillna(features.median(numeric_only=True))
    if features.shape[1] < 2:
        return {"available": False, "message": "The selected metrics are too sparse for anomaly detection.", "result": pd.DataFrame()}
    model = IsolationForest(n_estimators=200, contamination=min(0.15, max(0.05, 2 / len(features))), random_state=42)
    labels = model.fit_predict(StandardScaler().fit_transform(features))
    result = features.copy()
    result["date"] = result.index
    result["anomaly"] = labels == -1
    result["anomaly_score"] = -model.score_samples(StandardScaler().fit_transform(features))
    result = result.reset_index(drop=True).sort_values("date")
    return {"available": True, "message": "Isolation Forest fitted on aligned financial metrics.", "result": result, "features": list(features.columns)}


def segment_periods(data: pd.DataFrame) -> dict[str, Any]:
    """Segment quarters with KMeans and select k using silhouette score."""

    wide = pivot_financial_data(data)
    if wide.empty or len(wide) < 10:
        return {"available": False, "message": "At least ten aligned quarters are needed for segmentation.", "result": pd.DataFrame(), "elbow": pd.DataFrame(), "silhouette": pd.DataFrame()}
    features = wide.loc[:, wide.notna().sum() >= int(len(wide) * 0.65)].copy()
    if features.shape[1] < 2:
        return {"available": False, "message": "Not enough complete numeric metrics are available for segmentation.", "result": pd.DataFrame(), "elbow": pd.DataFrame(), "silhouette": pd.DataFrame()}
    features = features.iloc[:, :10].fillna(features.median(numeric_only=True))
    scaled = StandardScaler().fit_transform(features)
    candidates = list(range(2, min(5, len(features) - 1) + 1))
    elbow_rows: list[dict[str, Any]] = []
    silhouette_rows: list[dict[str, Any]] = []
    for k in candidates:
        model = KMeans(n_clusters=k, n_init=20, random_state=42)
        labels = model.fit_predict(scaled)
        elbow_rows.append({"k": k, "inertia": float(model.inertia_)})
        silhouette_rows.append({"k": k, "silhouette": float(silhouette_score(scaled, labels))})
    best_k = int(max(silhouette_rows, key=lambda row: row["silhouette"])["k"])
    final_model = KMeans(n_clusters=best_k, n_init=20, random_state=42)
    labels = final_model.fit_predict(scaled)
    result = features.copy()
    result["date"] = result.index
    result["segment"] = [f"Segment {label + 1}" for label in labels]
    result = result.reset_index(drop=True).sort_values("date")
    profile = result.groupby("segment")[list(features.columns)].mean().reset_index()
    return {
        "available": True,
        "message": f"KMeans selected k={best_k} using the highest silhouette score.",
        "result": result,
        "profile": profile,
        "elbow": pd.DataFrame(elbow_rows),
        "silhouette": pd.DataFrame(silhouette_rows),
        "features": list(features.columns),
        "best_k": best_k,
    }

