from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine

from app.infrastructure.config.settings import get_settings

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_NAME = "random_forest"


def _build_base_model(model_name: str, scale_pos_weight: float = 1.0):
    model_name = model_name.lower()

    if model_name == "random_forest":
        return RandomForestClassifier(
            n_estimators=700,
            max_depth=8,
            min_samples_split=6,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )

    if model_name == "logistic_regression":
        return LogisticRegression(
            solver="liblinear",
            class_weight="balanced",
            max_iter=3000,
            C=0.8,
            random_state=42,
        )

    if model_name == "xgboost":
        from xgboost import XGBClassifier

        return XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.04,
            subsample=0.85,
            colsample_bytree=0.85,
            eval_metric="logloss",
            random_state=42,
            scale_pos_weight=scale_pos_weight,
            n_jobs=-1,
        )

    raise ValueError(f"Unknown model: {model_name}")


def _artifacts_dir(model_name: str) -> Path:
    root = Path(get_settings().ml_artifacts_dir).resolve()
    d = root / model_name.lower()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _prepare_data():
    engine = create_engine(get_settings().database_url)

    query = """
    SELECT 
        sss.student_id,
        sss.semester_gpa,
        sss.total_failed,
        sss.total_subjects,
        sss.cumulative_gpa,
        LEAD(aw.warning_level) OVER (PARTITION BY sss.student_id ORDER BY sem.start_date) AS next_warning_level,
        aw.warning_level AS current_warning_level,
        sem.start_date
    FROM student_semester_stats sss
    JOIN semesters sem ON sss.semester_id = sem.id
    LEFT JOIN academic_warnings aw 
        ON sss.student_id = aw.student_id AND sss.semester_id = aw.semester_id
    """

    df = pd.read_sql(query, engine)
    df = df.sort_values(by=["student_id", "start_date"])
    df = df.dropna(subset=["next_warning_level"])

    df["warning"] = (df["next_warning_level"] == "warning").astype(int)

    df["gpa_diff"] = df["semester_gpa"] - df["cumulative_gpa"]
    df["fail_ratio"] = df["total_failed"] / df["total_subjects"].replace(0, 1)
    df["gpa_trend"] = df.groupby("student_id")["semester_gpa"].diff()
    df["fail_trend"] = df.groupby("student_id")["total_failed"].diff()
    df["was_warning"] = (df["current_warning_level"] == "warning").astype(int)

    df = df.fillna(0)

    feature_cols = [
        "semester_gpa",
        "cumulative_gpa",
        "gpa_diff",
        "total_failed",
        "total_subjects",
        "fail_ratio",
        "gpa_trend",
        "fail_trend",
        "was_warning",
    ]

    return df[feature_cols], df["warning"], feature_cols


def _get_scale_pos_weight(y):
    pos = y.sum()
    return (len(y) - pos) / pos if pos > 0 else 1.0


def _calculate_metrics(y_true, y_pred, y_proba):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "specificity": float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "pr_auc": float(average_precision_score(y_true, y_proba)),
        "brier_score": float(brier_score_loss(y_true, y_proba)),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
    }


def _build_pipeline(model_name: str, feature_cols: list[str], y_for_weight: pd.Series):
    base_model = _build_base_model(model_name, _get_scale_pos_weight(y_for_weight))
    preprocessor = ColumnTransformer([("num", StandardScaler(), feature_cols)])

    if model_name != "logistic_regression":
        base_model = CalibratedClassifierCV(
            estimator=base_model, cv=5, method="isotonic"
        )

    return ImbPipeline(
        [
            ("preprocessor", preprocessor),
            ("smote", SMOTE(random_state=42, k_neighbors=5)),
            ("classifier", base_model),
        ]
    )


def train(model_name: str = DEFAULT_MODEL_NAME):
    X, y, feature_cols = _prepare_data()
    pipeline = _build_pipeline(model_name, feature_cols, y)

    pipeline.fit(X, y)

    d = _artifacts_dir(model_name)
    model_path = d / "pipeline.joblib"
    joblib.dump(pipeline, model_path)

    print(f"Full pipeline trained & saved for {model_name}")
    return str(model_path)


def evaluate_cv(model_name: str = DEFAULT_MODEL_NAME, n_splits: int = 10):
    X, y, feature_cols = _prepare_data()
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    metrics_list = []

    for train_idx, val_idx in skf.split(X, y):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        pipeline = _build_pipeline(model_name, feature_cols, y_train)

        pipeline.fit(X_train, y_train)
        proba = pipeline.predict_proba(X_val)[:, 1]
        y_pred = (proba >= 0.5).astype(int)

        metrics_list.append(_calculate_metrics(y_val.values, y_pred, proba))

    avg = {k: np.mean([m[k] for m in metrics_list]) for k in metrics_list[0]}
    std = {
        k: np.std([m[k] for m in metrics_list])
        for k in metrics_list[0]
        if isinstance(metrics_list[0][k], (int, float))
    }

    print("=== CV Average (threshold 0.5) ===")
    for k, v in avg.items():
        print(f"{k}: {v:.4f} (±{std.get(k, 0):.4f})")


def tune_threshold(
    model_name: str = DEFAULT_MODEL_NAME,
    n_splits: int = 10,
    prioritize: str = "f1",
    target_recall: float | None = None,
):
    X, y, feature_cols = _prepare_data()
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    best_thresholds = []
    metrics_list = []
    thresholds = np.arange(0.01, 0.81, 0.01)

    for train_idx, val_idx in skf.split(X, y):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        pipeline = _build_pipeline(model_name, feature_cols, y_train)
        pipeline.fit(X_train, y_train)
        proba = pipeline.predict_proba(X_val)[:, 1]

        best_thr = 0.5
        best_score = -1e9
        best_metrics_fold = None

        for thr in thresholds:
            y_pred = (proba >= thr).astype(int)
            metrics = _calculate_metrics(y_val.values, y_pred, proba)

            if prioritize == "recall":
                score = metrics["recall"] + (0.05 * metrics["f1"])
            elif prioritize == "balanced":
                score = (0.7 * metrics["recall"]) + (0.3 * metrics["f1"])
            else:
                score = metrics["f1"]

            if target_recall is not None:
                if metrics["recall"] >= target_recall:
                    score += 10.0
                else:
                    score -= 10.0
            if score > best_score:
                best_score = score
                best_thr = thr
                best_metrics_fold = metrics.copy()

        best_thresholds.append(best_thr)
        metrics_list.append(best_metrics_fold)

    final_threshold = round(float(np.mean(best_thresholds)), 3)
    avg_metrics = {k: np.mean([m[k] for m in metrics_list]) for k in metrics_list[0]}

    print(f"=== Best Threshold (prioritize {prioritize}) ===")
    if target_recall is not None:
        print(f"Target recall: {target_recall}")
    print(f"Final threshold (mean from folds): {final_threshold}")
    for k, v in avg_metrics.items():
        print(f"{k}: {v:.4f}")

    d = _artifacts_dir(model_name)
    threshold_path = d / "threshold.json"
    meta_path = d / "meta.json"

    threshold_payload = {
        "threshold": final_threshold,
        "prioritize": prioritize,
        "target_recall": target_recall,
    }
    threshold_path.write_text(
        json.dumps(threshold_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    meta = {
        "model_name": model_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "feature_cols": list(feature_cols),
        "threshold": final_threshold,
        "target_recall": target_recall,
        "metrics": {k: float(v) for k, v in avg_metrics.items()},
    }
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "threshold": final_threshold,
        "target_recall": target_recall,
        "target_recall_achieved": avg_metrics.get("recall", 0.0)
        >= (target_recall if target_recall is not None else 0.0),
        **avg_metrics,
    }


if __name__ == "__main__":
    models = ["random_forest", "logistic_regression", "xgboost"]
    results = []

    for m in models:
        print(f"\n================ {m.upper()} ================")
        train(m)

        evaluate_cv(m, n_splits=10)

        best = tune_threshold(m, n_splits=10, prioritize="f1")
        best["model"] = m
        results.append(best)

    print("\n=========== COMPARISON ===========")
    df = pd.DataFrame(results)
    cols = ["model", "recall", "precision", "f1", "roc_auc", "pr_auc", "threshold"]
    print(df[cols].sort_values(by="f1", ascending=False).to_string(index=False))
