from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Tuple

from app.domain.entities.warning_rule import WarningRule
from app.domain.value_objects.student_semester_context import SemesterStatsContext


@dataclass(frozen=True)
class WarningEvaluationResult:
    warning_level: str
    triggered_rule_ids: Tuple[str, ...]
    reason_summary: str
    triggered_reasons: Tuple[str, ...]


class WarningEvaluationService:
    RULE_LABEL_VI = {
        "fail_ratio": "Tỷ lệ môn rớt",
        "semester_gpa": "TBCTL học kỳ",
        "cumulative_gpa": "TBCTL tích lũy",
    }

    @classmethod
    def evaluate(
        cls, context: SemesterStatsContext, rules: List[WarningRule]
    ) -> WarningEvaluationResult:
        triggered: List[WarningRule] = []

        for rule in rules:
            if not rule.matches_year(context.student_year):
                continue
            value = cls._metric_value(rule.rule_type, context)
            if value is None:
                continue
            if rule.evaluate(value):
                triggered.append(rule)

        if not triggered:
            return WarningEvaluationResult(
                warning_level="normal",
                triggered_rule_ids=tuple(),
                reason_summary="",
                triggered_reasons=tuple(),
            )

        parts = [cls._reason_fragment(r) for r in triggered]
        summary = "; ".join(parts)
        return WarningEvaluationResult(
            warning_level="warning",
            triggered_rule_ids=tuple(r.id for r in triggered),
            reason_summary=summary,
            triggered_reasons=tuple(parts),
        )

    @staticmethod
    def _metric_value(
        rule_type: str, context: SemesterStatsContext
    ) -> Optional[Decimal]:
        if rule_type == "fail_ratio":
            return context.fail_ratio
        if rule_type == "semester_gpa":
            return context.semester_gpa
        if rule_type == "cumulative_gpa":
            return context.cumulative_gpa
        return None

    @classmethod
    def _reason_fragment(cls, rule: WarningRule) -> str:
        label = cls.RULE_LABEL_VI.get(rule.rule_type, rule.rule_type)
        return (
            f"{label} (năm SV {rule.min_year}-{rule.max_year}): "
            f"{rule.comparison_operator} {rule.threshold}"
        )
