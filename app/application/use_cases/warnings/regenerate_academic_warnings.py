from __future__ import annotations

from decimal import Decimal
from typing import List

from app.domain.entities.academic_warning_draft import AcademicWarningDraft
from app.domain.repositories.academic_warning_repository import (
    AcademicWarningRepository,
)
from app.domain.repositories.student_stat_repository import StudentStatRepository
from app.domain.repositories.warning_rule_repository import WarningRuleRepository
from app.domain.services.warning_evaluation_service import WarningEvaluationService
from app.domain.value_objects.student_semester_context import (
    SemesterStatsContext,
    compute_student_year,
)


class RegenerateAcademicWarningsUseCase:
    def __init__(
        self,
        rule_repo: WarningRuleRepository,
        stat_repo: StudentStatRepository,
        warning_repo: AcademicWarningRepository,
    ):
        self._rule_repo = rule_repo
        self._stat_repo = stat_repo
        self._warning_repo = warning_repo

    def execute(self) -> None:
        rules = self._rule_repo.get_active_rules()
        rows = self._stat_repo.list_for_warning_regeneration()
        self._warning_repo.clear_all()

        rule_set_id = self._rule_repo.get_active_rule_set_id()
        drafts: List[AcademicWarningDraft] = []

        for r in rows:
            student_year = compute_student_year(
                r.enrollment_year, r.semester_academic_year
            )
            ctx = SemesterStatsContext(
                total_subjects=r.total_subjects,
                total_failed=r.total_failed,
                semester_gpa=r.semester_gpa,
                cumulative_gpa=r.cumulative_gpa,
                student_year=student_year,
            )
            fail_ratio = ctx.fail_ratio
            if fail_ratio is None:
                fail_ratio = Decimal(0)

            if not rules:
                level = "normal"
                reason = None
            else:
                ev = WarningEvaluationService.evaluate(ctx, rules)
                level = ev.warning_level
                reason = ev.reason_summary if ev.warning_level == "warning" else None

            drafts.append(
                AcademicWarningDraft(
                    student_id=r.student_id,
                    semester_id=r.semester_id,
                    total_subjects=r.total_subjects,
                    total_failed=r.total_failed,
                    fail_ratio=fail_ratio,
                    semester_gpa=r.semester_gpa,
                    cumulative_gpa=r.cumulative_gpa,
                    warning_level=level,
                    warning_reason=reason,
                    rule_set_id=rule_set_id,
                )
            )

        self._warning_repo.bulk_insert(drafts)
