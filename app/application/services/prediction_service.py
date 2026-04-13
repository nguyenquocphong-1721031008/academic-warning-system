from __future__ import annotations

from app.application.dto.ml_prediction_dto import (
    MlWarningRiskPredictionDTO,
    TrendAnalysisDTO,
)
from app.application.ports.dropout_model_port import DropoutModelPort
from app.application.ports.prediction_stats_reader import PredictionStatsReader
from app.domain.services.prediction_policy_service import PredictionPolicyService
from app.domain.services.recommendation_service import RecommendationService
from app.domain.services.trend_analysis_service import TrendAnalysisService


class PredictionService:
    _NO_STATS_MSG_VI = (
        "Chưa có thống kê học kỳ đủ để dự đoán rủi ro bằng mô hình. "
        "Vui lòng tổng hợp/import điểm trước."
    )

    def __init__(
        self,
        stats_reader: PredictionStatsReader,
        dropout_model: DropoutModelPort,
    ) -> None:
        self._stats_reader = stats_reader
        self._dropout_model = dropout_model

    def predict_warning_risk(self, student_code: str) -> MlWarningRiskPredictionDTO:
        snap = self._stats_reader.load_warning_risk_snapshot(student_code)
        if snap is None:
            raise ValueError("student_not_found")

        if not snap.has_semester_stats:
            return MlWarningRiskPredictionDTO(
                student_code=snap.student_code,
                risk_score=None,
                risk_level="low",
                trend=None,
                prediction_message=self._NO_STATS_MSG_VI,
                trend_analysis=None,
                recommendations=[
                    "Bổ sung dữ liệu điểm và thống kê học kỳ để có phân tích xu hướng và khuyến nghị đầy đủ.",
                    "Tra cứu cảnh báo học vụ (rule-based) tại API /warnings nếu cần.",
                ],
            )

        assert (
            snap.semester_gpa is not None
            and snap.cumulative_gpa is not None
            and snap.total_failed is not None
            and snap.total_subjects is not None
        )

        prev_sg_model = (
            snap.prev_semester_gpa if snap.prev_semester_gpa is not None else 0.0
        )
        prev_tf_model = (
            snap.prev_total_failed if snap.prev_total_failed is not None else 0
        )
        was_warning = 1 if snap.warning_level == "warning" else 0

        model_out = self._dropout_model.predict(
            semester_gpa=snap.semester_gpa,
            cumulative_gpa=snap.cumulative_gpa,
            total_failed=snap.total_failed,
            total_subjects=snap.total_subjects,
            prev_semester_gpa=prev_sg_model,
            prev_total_failed=prev_tf_model,
            was_warning=was_warning,
        )

        trend_result = TrendAnalysisService.analyze(
            semester_gpa=snap.semester_gpa,
            cumulative_gpa=snap.cumulative_gpa,
            total_failed=snap.total_failed,
            prev_semester_gpa=snap.prev_semester_gpa,
            prev_total_failed=snap.prev_total_failed,
        )

        assert trend_result.trend is not None

        student_year, policy_checks = PredictionPolicyService.evaluate(
            enrollment_year=snap.enrollment_year,
            semester_academic_year=snap.semester_academic_year,
            semester_gpa=snap.semester_gpa,
            cumulative_gpa=snap.cumulative_gpa,
            total_failed=snap.total_failed,
            total_subjects=snap.total_subjects,
        )

        recommendations = RecommendationService.build_short(
            checks=policy_checks,
            ml_risk_level=str(model_out["risk_level"]),
            ml_message=str(model_out.get("message", "")),
            student_year=student_year,
        )

        trend_dto = TrendAnalysisDTO(
            code=trend_result.trend,
            summary_vi=trend_result.summary_vi,
            gpa_diff_semester_vs_cumulative=trend_result.gpa_diff_semester_vs_cumulative,
            bullets_vi=list(trend_result.explanation_bullets_vi),
        )

        return MlWarningRiskPredictionDTO(
            student_code=snap.student_code,
            risk_score=float(model_out["risk_score"]),
            risk_level=str(model_out["risk_level"]),
            trend=trend_result.trend,
            prediction_message=str(model_out.get("message", "")),
            trend_analysis=trend_dto,
            recommendations=recommendations,
        )
