from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


TrendCode = Literal["decreasing", "increasing"]


@dataclass(frozen=True)
class TrendAnalysisResult:
    trend: TrendCode | None
    gpa_diff_semester_vs_cumulative: float
    summary_vi: str
    explanation_bullets_vi: list[str]


class TrendAnalysisService:
    @staticmethod
    def empty() -> TrendAnalysisResult:
        return TrendAnalysisResult(
            trend=None,
            gpa_diff_semester_vs_cumulative=0.0,
            summary_vi="",
            explanation_bullets_vi=[],
        )

    @staticmethod
    def analyze(
        *,
        semester_gpa: float,
        cumulative_gpa: float,
        total_failed: int,
        prev_semester_gpa: float | None,
        prev_total_failed: int | None,
    ) -> TrendAnalysisResult:
        gpa_diff = semester_gpa - cumulative_gpa
        if gpa_diff < 0:
            trend: TrendCode = "decreasing"
        else:
            trend = "increasing"

        bullets: list[str] = []

        if gpa_diff < 0:
            bullets.append(
                f"TB học kỳ ({semester_gpa:.2f}) thấp hơn TB tích lũy ({cumulative_gpa:.2f}) "
                f"— kỳ này kéo mặt bằng xuống (chênh {abs(gpa_diff):.2f})."
            )
        elif gpa_diff > 0:
            bullets.append(
                f"TB học kỳ ({semester_gpa:.2f}) cao hơn TB tích lũy ({cumulative_gpa:.2f}) "
                f"(+{gpa_diff:.2f})."
            )
        else:
            bullets.append(f"TB học kỳ bằng TB tích lũy ({cumulative_gpa:.2f}).")

        if prev_semester_gpa is not None and prev_semester_gpa > 0:
            d = semester_gpa - prev_semester_gpa
            if d < -0.05:
                bullets.append(
                    f"So với kỳ trước: TBHK giảm {abs(d):.2f} ({prev_semester_gpa:.2f} → {semester_gpa:.2f})."
                )
            elif d > 0.05:
                bullets.append(
                    f"So với kỳ trước: TBHK tăng {d:.2f} ({prev_semester_gpa:.2f} → {semester_gpa:.2f})."
                )
            else:
                bullets.append(
                    f"TBHK ổn định so với kỳ trước ({prev_semester_gpa:.2f} → {semester_gpa:.2f})."
                )

        if prev_total_failed is not None:
            df = total_failed - prev_total_failed
            if df > 0:
                bullets.append(
                    f"Môn rớt tăng +{df} so với kỳ trước ({total_failed} so với {prev_total_failed})."
                )
            elif df < 0:
                bullets.append(
                    f"Môn rớt giảm {abs(df)} so với kỳ trước ({total_failed} so với {prev_total_failed})."
                )
            else:
                bullets.append(f"Số môn rớt không đổi ({total_failed}).")

        summary = TrendAnalysisService._summary_vi(
            trend=trend,
            gpa_diff=gpa_diff,
            semester_gpa=semester_gpa,
            cumulative_gpa=cumulative_gpa,
        )

        return TrendAnalysisResult(
            trend=trend,
            gpa_diff_semester_vs_cumulative=gpa_diff,
            summary_vi=summary,
            explanation_bullets_vi=bullets,
        )

    @staticmethod
    def _summary_vi(
        *,
        trend: TrendCode,
        gpa_diff: float,
        semester_gpa: float,
        cumulative_gpa: float,
    ) -> str:
        if trend == "decreasing":
            return (
                f"TB học kỳ ({semester_gpa:.2f}) thấp hơn TB tích lũy ({cumulative_gpa:.2f}) "
                f"— xu hướng kéo điểm chung xuống (chênh {abs(gpa_diff):.2f})."
            )
        if abs(gpa_diff) < 1e-6:
            return f"TB học kỳ bằng TB tích lũy ({cumulative_gpa:.2f}) — mặt bằng điểm không đổi so với tích lũy."
        return (
            f"TB học kỳ ({semester_gpa:.2f}) cao hơn TB tích lũy ({cumulative_gpa:.2f}) "
            f"(+{gpa_diff:.2f}) — kỳ này nâng mặt bằng chung."
        )
