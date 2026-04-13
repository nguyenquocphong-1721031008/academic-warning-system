from __future__ import annotations

from app.domain.entities.semester_stat_row import SemesterStatRegenerationRow
from app.domain.repositories.warning_rule_repository import WarningRuleRepository
from app.domain.services.warning_evaluation_service import (
    WarningEvaluationResult,
    WarningEvaluationService,
)
from app.domain.value_objects.student_semester_context import (
    SemesterStatsContext,
    compute_student_year,
)


class WarningRuleEngine:
    def __init__(self, rule_repo: WarningRuleRepository) -> None:
        self._rule_repo = rule_repo

    def evaluate_row(
        self,
        row: SemesterStatRegenerationRow,
    ) -> WarningEvaluationResult:
        rules = self._rule_repo.get_active_rules()
        student_year = compute_student_year(
            row.enrollment_year, row.semester_academic_year
        )
        ctx = SemesterStatsContext(
            total_subjects=row.total_subjects,
            total_failed=row.total_failed,
            semester_gpa=row.semester_gpa,
            cumulative_gpa=row.cumulative_gpa,
            student_year=student_year,
        )
        if not rules:
            return WarningEvaluationResult(
                warning_level="normal",
                triggered_rule_ids=tuple(),
                reason_summary="",
                triggered_reasons=tuple(),
            )
        return WarningEvaluationService.evaluate(ctx, rules)
