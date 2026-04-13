from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TrendAnalysisDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        ...,
        description="Mã xu hướng: decreasing | increasing (TBHK so với TB tích lũy)",
    )
    summary_vi: str = Field(..., description="Tóm tắt một dòng (Tiếng Việt)")
    gpa_diff_semester_vs_cumulative: float = Field(
        ...,
        description="TB học kỳ trừ TB tích lũy (âm = kỳ này thấp hơn mặt bằng tích lũy)",
    )
    bullets_vi: list[str] = Field(
        default_factory=list,
        description="Chi tiết ngắn: so sánh kỳ trước, môn rớt, ...",
    )


class MlWarningRiskPredictionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_code: str
    risk_score: float | None = Field(
        None,
        description="0–1 khi có đủ dữ liệu học kỳ; null nếu chưa chạy được mô hình",
    )
    risk_level: str = Field(
        ...,
        description="low | medium | high (ML); khi thiếu dữ liệu dùng low + risk_score null",
    )
    trend: str | None = Field(
        None,
        description="Lặp nhanh mã xu hướng (decreasing|increasing); null nếu thiếu dữ liệu",
    )
    prediction_message: str = Field(..., description="Thông điệp từ mô hình ML")

    trend_analysis: TrendAnalysisDTO | None = Field(
        None,
        description="Phân tích xu hướng học tập (rule-based, không phải output ML)",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Gợi ý hành động (quy định + ML), câu ngắn",
    )
