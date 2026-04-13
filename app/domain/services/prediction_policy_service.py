from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.domain.value_objects.student_semester_context import compute_student_year


@dataclass(frozen=True)
class PolicyCheckResult:
    code: str
    passed: bool
    message_vi: str


def _d(x: Any) -> Decimal | None:
    if x is None:
        return None
    try:
        return Decimal(str(x))
    except Exception:
        return None


def semester_gpa_threshold(student_year: int) -> Decimal:
    return Decimal("0.80") if student_year <= 1 else Decimal("1.00")


def cumulative_gpa_threshold(student_year: int) -> Decimal:
    if student_year <= 1:
        return Decimal("1.20")
    if student_year == 2:
        return Decimal("1.40")
    if student_year == 3:
        return Decimal("1.60")
    return Decimal("1.80")


class PredictionPolicyService:
    @staticmethod
    def evaluate(
        *,
        enrollment_year: int,
        semester_academic_year: str | None,
        semester_gpa: float,
        cumulative_gpa: float,
        total_failed: int,
        total_subjects: int,
    ) -> tuple[int, list[PolicyCheckResult]]:
        sy = compute_student_year(enrollment_year, semester_academic_year or "")
        sg = _d(semester_gpa)
        cg = _d(cumulative_gpa)
        fr: Decimal | None = None
        if total_subjects > 0:
            fr = Decimal(total_failed) / Decimal(total_subjects)

        out: list[PolicyCheckResult] = []

        sem_thr = semester_gpa_threshold(sy)
        if sg is not None:
            ok = sg >= sem_thr
            out.append(
                PolicyCheckResult(
                    code="semester_gpa",
                    passed=ok,
                    message_vi=(
                        f"Năm thứ {sy}: TB học kỳ {sg} — "
                        f"{'đạt' if ok else 'dưới'} ngưỡng tối thiểu {sem_thr}."
                    ),
                )
            )

        cum_thr = cumulative_gpa_threshold(sy)
        if cg is not None:
            ok = cg >= cum_thr
            out.append(
                PolicyCheckResult(
                    code="cumulative_gpa",
                    passed=ok,
                    message_vi=(
                        f"Năm thứ {sy}: TBCTL {cg} — "
                        f"{'đạt' if ok else 'dưới'} ngưỡng tối thiểu {cum_thr}."
                    ),
                )
            )

        if fr is not None:
            ok = fr <= Decimal("0.5")
            pct = float(fr) * 100
            out.append(
                PolicyCheckResult(
                    code="fail_ratio_proxy",
                    passed=ok,
                    message_vi=(
                        f"Tỷ lệ môn rớt ~{pct:.0f}% ({total_failed}/{total_subjects}) — "
                        f"{'chấp nhận' if ok else 'vượt'} ngưỡng 50% (xấp xỉ theo môn, chưa theo tín chỉ)."
                    ),
                )
            )

        return sy, out
