from __future__ import annotations

from app.domain.services.prediction_policy_service import (
    PolicyCheckResult,
    cumulative_gpa_threshold,
)


class RecommendationService:
    @staticmethod
    def build_short(
        *,
        checks: list[PolicyCheckResult],
        ml_risk_level: str,
        ml_message: str,
        student_year: int,
        max_items: int = 4,
    ) -> list[str]:
        out: list[str] = []

        for c in checks:
            if c.passed:
                continue
            if c.code == "semester_gpa":
                out.append(
                    "Ưu tiên nâng TB học kỳ: ôn đều, hỏi GV sớm nếu điểm thành phần thấp."
                )
            elif c.code == "cumulative_gpa":
                thr = cumulative_gpa_threshold(student_year)
                out.append(
                    f"Lên kế hoạch cải thiện TBCTL (mục tiêu ≥ {thr} cho năm thứ {student_year})."
                )
            elif c.code == "fail_ratio_proxy":
                out.append("Giảm tỷ lệ rớt: tránh dồn môn nặng; học lại/bổ trợ sớm.")

        if ml_risk_level == "high":
            out.append(f"Rủi ro ML: {ml_message}")
        elif ml_risk_level == "medium":
            out.append(f"Theo dõi sát kỳ sau: {ml_message}")

        if not any(not c.passed for c in checks) and ml_risk_level == "low":
            out.append("Chỉ số đang trong ngưỡng; duy trì tiến độ học tập.")

        seen: set[str] = set()
        uniq: list[str] = []
        for s in out:
            if s not in seen:
                seen.add(s)
                uniq.append(s)
        return uniq[:max_items]
