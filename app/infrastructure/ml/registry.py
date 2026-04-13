from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from app.infrastructure.config.settings import get_settings
from app.infrastructure.ml.predictor import LoadedPipeline


class MlRegistry:
    """
    In-memory registry of loaded ML pipelines.
    Designed to be created once at app startup and stored in app.state.
    """

    def __init__(self) -> None:
        self._pipelines: dict[str, LoadedPipeline] = {}

    @property
    def pipelines(self) -> dict[str, LoadedPipeline]:
        return dict(self._pipelines)

    def get(self, model_name: str) -> LoadedPipeline:
        key = (model_name or "").lower()
        if key not in self._pipelines:
            raise KeyError(f"model_not_loaded:{key}")
        return self._pipelines[key]

    def load_all_from_artifacts_dir(self) -> None:
        settings = get_settings()
        root = Path(settings.ml_artifacts_dir).resolve()
        if not root.exists():
            return

        for sub in root.iterdir():
            if not sub.is_dir():
                continue
            self._pipelines[sub.name.lower()] = _load_one(sub.name.lower(), sub)

    def load_one(self, model_name: str) -> LoadedPipeline:
        settings = get_settings()
        root = Path(settings.ml_artifacts_dir).resolve()
        sub = root / model_name.lower()
        loaded = _load_one(model_name.lower(), sub)
        self._pipelines[model_name.lower()] = loaded
        return loaded


def _load_one(model_name: str, model_dir: Path) -> LoadedPipeline:
    pipeline_path = model_dir / "pipeline.joblib"
    thr_path = model_dir / "threshold.json"

    if not pipeline_path.exists():
        raise FileNotFoundError(f"Missing pipeline artifact: {pipeline_path}")

    pipeline: Any = joblib.load(pipeline_path)

    threshold = 0.5
    if thr_path.exists():
        payload = json.loads(thr_path.read_text(encoding="utf-8"))
        threshold = float(payload.get("threshold", 0.5))

    return LoadedPipeline(
        model_name=model_name,
        pipeline=pipeline,
        threshold=threshold,
        model_path=str(pipeline_path),
    )
