from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class LoadedPipeline:
    model_name: str
    pipeline: Any
    threshold: float
    model_path: str


class WarningPredictor:
    """
    Pure inference wrapper (no I/O).
    - Pipeline loading/caching should happen outside (startup lifespan).
    """

    def __init__(self, loaded: LoadedPipeline):
        self._loaded = loaded

    def predict(
        self,
        semester_gpa,
        cumulative_gpa,
        total_failed,
        total_subjects,
        prev_semester_gpa=0,
        prev_total_failed=0,
        was_warning=0,
    ):
        gpa_diff = semester_gpa - cumulative_gpa
        fail_ratio = total_failed / total_subjects if total_subjects != 0 else 0

        gpa_trend = semester_gpa - prev_semester_gpa
        fail_trend = total_failed - prev_total_failed

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
        X = pd.DataFrame(
            [
                {
                    "semester_gpa": float(semester_gpa),
                    "cumulative_gpa": float(cumulative_gpa),
                    "gpa_diff": float(gpa_diff),
                    "total_failed": int(total_failed),
                    "total_subjects": int(total_subjects),
                    "fail_ratio": float(fail_ratio),
                    "gpa_trend": float(gpa_trend),
                    "fail_trend": float(fail_trend),
                    "was_warning": int(was_warning),
                }
            ],
            columns=feature_cols,
        )

        pipeline = self._loaded.pipeline
        if hasattr(pipeline, "predict_proba"):
            risk_score = float(pipeline.predict_proba(X)[0][1])
        else:
            raw_value = (
                float(pipeline.decision_function(X)[0])
                if hasattr(pipeline, "decision_function")
                else 0.0
            )
            risk_score = max(0.0, min(1.0, (raw_value + 1) / 2))

        thr = float(self._loaded.threshold)
        prediction = int(risk_score >= thr)

        if risk_score < 0.4:
            level = "low"
            message = "Học lực ổn định"
        elif risk_score < 0.7:
            level = "medium"
            message = "Có dấu hiệu giảm sút học lực"
        else:
            level = "high"
            message = "Nguy cơ cao bị cảnh báo học vụ"

        return {
            "prediction": prediction,
            "risk_score": risk_score,
            "risk_level": level,
            "message": message,
            "model_version": self._loaded.model_name,
            "model_path": self._loaded.model_path,
            "threshold": thr,
        }
