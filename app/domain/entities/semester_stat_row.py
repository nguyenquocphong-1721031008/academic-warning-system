from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class SemesterStatRegenerationRow:
    student_id: str
    semester_id: str
    total_subjects: int
    total_failed: int
    semester_gpa: Optional[Decimal]
    cumulative_gpa: Optional[Decimal]
    enrollment_year: int
    semester_academic_year: str
