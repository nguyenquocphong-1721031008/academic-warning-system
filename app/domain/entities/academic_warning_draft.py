from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class AcademicWarningDraft:
    student_id: str
    semester_id: str
    total_subjects: int
    total_failed: int
    fail_ratio: Decimal
    semester_gpa: Optional[Decimal]
    cumulative_gpa: Optional[Decimal]
    warning_level: str
    warning_reason: Optional[str]
    rule_set_id: Optional[str]
