import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.api.auth_router import get_current_admin
from app.api.dependencies import get_optional_user, is_internal_warning_viewer
from app.api.rate_limit import SlidingWindowLimiter, client_ip
from app.api.schemas.ml import MlPredictRequest
from app.api.schemas.response import success_response
from app.application.services.prediction_service import PredictionService
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.repositories.prediction_stats_repository import (
    SqlAlchemyPredictionStatsRepository,
)
from app.infrastructure.ml.predictor import WarningPredictor
from app.infrastructure.ml.registry import MlRegistry
from app.infrastructure.ml.train_model import (
    train as train_model,
    tune_threshold,
)

router = APIRouter(prefix="/ml", tags=["ml"])

_limiter = SlidingWindowLimiter(
    limit=get_settings().ml_predict_rate_limit_per_minute, window_seconds=60
)


def _to_builtin(value):
    return value.item() if hasattr(value, "item") else value


class MlTrainDTO(BaseModel):
    model_type: str = "random_forest"


class MlTrainAllDTO(BaseModel):
    models: list[str] = ["random_forest", "logistic_regression", "xgboost"]


@router.get("/status")
def ml_status(request: Request):
    registry: MlRegistry = request.app.state.ml_registry
    settings = get_settings()
    loaded = []
    for name, p in sorted(registry.pipelines.items()):
        model_metrics = None
        meta_path = Path(p.model_path).parent / "meta.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                model_metrics = meta.get("metrics")
            except Exception:
                model_metrics = None
        loaded.append(
            {
                "model": name,
                "threshold": p.threshold,
                "model_path": p.model_path,
                "metrics": model_metrics,
            }
        )
    return success_response(
        data={"artifacts_dir": settings.ml_artifacts_dir, "loaded_models": loaded},
        message_vi="Trạng thái mô hình ML",
        message_en="ML model status",
    )


@router.post("/predict")
def ml_predict(
    payload: MlPredictRequest,
    request: Request,
    current_user=Depends(get_optional_user),
):
    if not is_internal_warning_viewer(current_user):
        raise HTTPException(
            status_code=403, detail="Chỉ nội bộ mới dùng được dự báo ML"
        )

    _limiter.hit(f"{client_ip(request)}:ml_predict")

    registry: MlRegistry = request.app.state.ml_registry
    try:
        loaded = registry.get(payload.model)
    except KeyError:
        try:
            loaded = registry.load_one(payload.model)
        except FileNotFoundError:
            raise HTTPException(
                status_code=503,
                detail=f"Model artifact not found for '{payload.model}'",
            ) from None

    predictor = WarningPredictor(loaded=loaded)
    svc = PredictionService(
        stats_reader=SqlAlchemyPredictionStatsRepository(),
        dropout_model=predictor,
    )

    try:
        out = svc.predict_warning_risk(payload.student_code)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503, detail="ML model artifact unavailable"
        ) from None
    except ValueError as exc:
        if str(exc) != "student_not_found":
            raise HTTPException(status_code=400, detail=str(exc)) from None
        raise HTTPException(
            status_code=404, detail="Không tìm thấy sinh viên"
        ) from None

    return success_response(
        data=out.model_dump(mode="json"),
        message_vi="Dự báo nguy cơ cảnh báo học vụ (ML)",
        message_en="Academic warning risk prediction (ML)",
    )


@router.post("/train")
def train_warning_risk_model(
    train_data: MlTrainDTO,
    _admin=Depends(get_current_admin),
):
    try:
        model_file = train_model(train_data.model_type)
        tuned = tune_threshold(
            train_data.model_type,
            n_splits=10,
            prioritize="f1",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    return success_response(
        data={
            "model_file": model_file,
            "model_type": train_data.model_type,
            "threshold": tuned.get("threshold"),
            "metrics": {
                k: _to_builtin(v) for k, v in tuned.items() if k != "threshold"
            },
        },
        message_vi=f"Đã huấn luyện model cảnh báo học vụ: {train_data.model_type}",
        message_en=f"Trained academic-warning model: {train_data.model_type}",
    )


@router.post("/train-all")
def train_all_warning_risk_models(
    train_data: MlTrainAllDTO,
    _admin=Depends(get_current_admin),
):
    allowed = {"random_forest", "logistic_regression", "xgboost"}
    invalid = [m for m in train_data.models if m not in allowed]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unsupported model(s): {invalid}")

    results = []
    for model_name in train_data.models:
        try:
            model_file = train_model(model_name)
            tuned = tune_threshold(
                model_name,
                n_splits=10,
                prioritize="f1",
            )
            results.append(
                {
                    "model_file": model_file,
                    "model_type": model_name,
                    "threshold": tuned.get("threshold"),
                    "metrics": {
                        k: _to_builtin(v)
                        for k, v in tuned.items()
                        if k != "threshold"
                    },
                }
            )
        except Exception as exc:
            results.append(
                {
                    "model_type": model_name,
                    "error": str(exc),
                }
            )

    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    return success_response(
        data={
            "results": results,
            "summary": {
                "requested": len(train_data.models),
                "successful": len(successful),
                "failed": len(failed),
            },
        },
        message_vi="Đã huấn luyện tất cả model cảnh báo học vụ",
        message_en="Trained all academic-warning models",
    )
