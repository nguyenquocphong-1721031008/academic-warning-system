from __future__ import annotations

from datetime import datetime

from app.application.dto.warning_api_dto import (
    InternalWarningItemDTO,
    InternalWarningResponseDTO,
    ParentWarningResponseDTO,
    PublicWarningResponseDTO,
    ViolationItemDTO,
)
from app.application.warning_rule_engine import WarningRuleEngine
from app.domain.repositories.academic_warning_repository import (
    AcademicWarningRepository,
)
from app.domain.repositories.student_repository import StudentRepository
from app.domain.repositories.student_stat_repository import StudentStatRepository
from app.domain.services.warning_evaluation_service import WarningEvaluationResult


def _map_tier(
    ev: WarningEvaluationResult | None, *, has_stats: bool
) -> tuple[bool, str]:
    if not has_stats or ev is None:
        return False, "none"
    if ev.warning_level == "normal":
        return False, "none"
    n = len(ev.triggered_rule_ids)
    if n >= 4:
        return True, "critical"
    if n == 3:
        return True, "high"
    if n == 2:
        return True, "medium"
    return True, "low"


def _public_message_vi(has_warning: bool, tier: str, *, has_stats: bool) -> str:
    if not has_stats:
        return (
            "Hệ thống chưa đủ dữ liệu để đánh giá tự động. "
            "Vui lòng liên hệ hotline hỗ trợ nếu cần thông tin."
        )
    if not has_warning:
        return "Sinh viên không thuộc diện cảnh báo học vụ theo quy định hiện hành."
    return (
        "Sinh viên đang thuộc diện cảnh báo học vụ. "
        "Vui lòng liên hệ phòng hỗ trợ hoặc cố vấn học tập để được đồng hành."
    )


class WarningStatusService:
    def __init__(
        self,
        student_repo: StudentRepository,
        stat_repo: StudentStatRepository,
        warning_repo: AcademicWarningRepository,
        rule_engine: WarningRuleEngine,
        support_phone: str,
    ) -> None:
        self._student_repo = student_repo
        self._stat_repo = stat_repo
        self._warning_repo = warning_repo
        self._rule_engine = rule_engine
        self._support_phone = support_phone

    def get_public(self, student_code: str) -> PublicWarningResponseDTO | None:
        internal_eval = self._evaluate(student_code)
        if internal_eval is None:
            return None
        has_w, tier = self._tier_from_eval(internal_eval)
        has_stats: bool = internal_eval["has_stats"]
        return PublicWarningResponseDTO(
            student_code=internal_eval["student_code"],
            has_warning=has_w,
            warning_level=tier,  # type: ignore[arg-type]
            message_vi=_public_message_vi(has_w, tier, has_stats=has_stats),
            support_phone=self._support_phone,
        )

    def get_parent(self, student_code: str) -> ParentWarningResponseDTO | None:
        student = self._student_repo.get_by_code(student_code)
        if not student:
            return None

        row = self._stat_repo.get_latest_regeneration_row_for_student(student.id)
        internal_eval = self._evaluate(student_code)
        if internal_eval is None:
            return None
        has_w, tier = self._tier_from_eval(internal_eval)
        performance_level = self._performance_level(row)

        warnings = self._warning_repo.get_by_student_code(student_code)
        warning_items = [
            InternalWarningItemDTO(
                id=w.id,
                semester_id=w.semester_id,
                semester_name=w.semester_name,
                academic_year=w.academic_year,
                warning_level=w.warning_level,
                warning_status=w.warning_status,
                warning_note=w.warning_note,
                total_subjects=w.total_subjects,
                total_failed=w.total_failed,
                fail_ratio=float(w.fail_ratio) if w.fail_ratio is not None else None,
                semester_gpa=float(w.semester_gpa)
                if w.semester_gpa is not None
                else None,
                cumulative_gpa=float(w.cumulative_gpa)
                if w.cumulative_gpa is not None
                else None,
                created_at=w.created_at.isoformat()
                if w.created_at is not None
                else None,
            )
            for w in warnings
            if w.warning_level != "normal"
        ]

        return ParentWarningResponseDTO(
            student_code=student.student_code,
            student_name=student.full_name,
            status=student.status,
            enrollment_year=student.enrollment_year or 0,
            performance_level=performance_level,
            has_warnings=len(warning_items) > 0,
            support_phone=self._support_phone,
            warnings=warning_items,
        )

    @staticmethod
    def _performance_level(row) -> str:
        if row is None or row.semester_gpa is None:
            return "unknown"

        gpa = float(row.cumulative_gpa or row.semester_gpa)
        if gpa >= 3.5:
            return "excellent"
        if gpa >= 3.0:
            return "very_good"
        if gpa >= 2.5:
            return "good"
        if gpa >= 2.0:
            return "average"
        if gpa >= 1.5:
            return "warning"
        return "critical"

    def get_internal(self, student_code: str) -> InternalWarningResponseDTO | None:
        internal_eval = self._evaluate(student_code)
        if internal_eval is None:
            return None
        has_w, tier = self._tier_from_eval(internal_eval)
        ev: WarningEvaluationResult | None = internal_eval["evaluation"]

        violations = [
            ViolationItemDTO(message_vi=r) for r in (ev.triggered_reasons if ev else ())
        ]

        academic = self._warning_repo.get_by_student_code(student_code)
        warning_items: list[InternalWarningItemDTO] = []
        for w in academic:
            if w.warning_level == "normal":
                continue
            warning_items.append(
                InternalWarningItemDTO(
                    id=w.id,
                    semester_id=w.semester_id,
                    semester_name=w.semester_name,
                    academic_year=w.academic_year,
                    warning_level=w.warning_level,
                    warning_status=w.warning_status,
                    warning_note=w.warning_note,
                    total_subjects=w.total_subjects,
                    total_failed=w.total_failed,
                    fail_ratio=float(w.fail_ratio)
                    if w.fail_ratio is not None
                    else None,
                    semester_gpa=float(w.semester_gpa)
                    if w.semester_gpa is not None
                    else None,
                    cumulative_gpa=float(w.cumulative_gpa)
                    if w.cumulative_gpa is not None
                    else None,
                    created_at=_iso(w.created_at),
                )
            )

        row = internal_eval["latest_row"]
        sg = float(row.semester_gpa) if row and row.semester_gpa is not None else None
        cg = (
            float(row.cumulative_gpa)
            if row and row.cumulative_gpa is not None
            else None
        )

        return InternalWarningResponseDTO(
            student_code=internal_eval["student_code"],
            full_name=internal_eval["full_name"],
            class_code=internal_eval["class_code"],
            semester_gpa=sg,
            cumulative_gpa=cg,
            warnings=warning_items,
            violations=violations,
            warning_level=tier,  # type: ignore[arg-type]
        )

    def _tier_from_eval(self, internal_eval: dict) -> tuple[bool, str]:
        has_stats: bool = internal_eval["has_stats"]
        ev: WarningEvaluationResult | None = internal_eval["evaluation"]
        return _map_tier(ev, has_stats=has_stats)

    def _evaluate(self, student_code: str) -> dict | None:
        student = self._student_repo.get_by_code(student_code)
        if not student:
            return None

        row = self._stat_repo.get_latest_regeneration_row_for_student(student.id)
        ev: WarningEvaluationResult | None = None
        has_stats = row is not None and (row.total_subjects or 0) > 0
        if row is not None and has_stats:
            ev = self._rule_engine.evaluate_row(row)

        return {
            "student_code": student.student_code,
            "full_name": student.full_name,
            "class_code": student.class_code,
            "latest_row": row,
            "evaluation": ev,
            "has_stats": has_stats,
        }


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)
