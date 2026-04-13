from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MlPredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_code: str = Field(
        ..., min_length=1, max_length=50, description="Mã sinh viên (MSSV)"
    )
    model: str = Field(
        default="random_forest",
        description="Model: random_forest | logistic_regression | xgboost",
        pattern="^(random_forest|logistic_regression|xgboost)$",
    )


class MlStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    loaded_models: list[dict] = Field(default_factory=list)
    artifacts_dir: str
