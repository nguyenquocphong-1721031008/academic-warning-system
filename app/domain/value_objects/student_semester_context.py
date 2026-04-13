from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


def parse_academic_year_start(academic_year: str) -> int:
    if not academic_year:
        return 0
    parts = academic_year.replace(" ", "").split("-")
    if not parts or not parts[0].isdigit():
        return 0
    return int(parts[0])


def compute_student_year(enrollment_year: int, semester_academic_year: str) -> int:
    start = parse_academic_year_start(semester_academic_year)
    if start == 0 or enrollment_year <= 0:
        return 1
    year = start - enrollment_year + 1
    return max(1, min(10, year))


@dataclass(frozen=True)
class SemesterStatsContext:
    total_subjects: int
    total_failed: int
    semester_gpa: Optional[Decimal]
    cumulative_gpa: Optional[Decimal]
    student_year: int

    @property
    def fail_ratio(self) -> Optional[Decimal]:
        if self.total_subjects <= 0:
            return None
        return Decimal(self.total_failed) / Decimal(self.total_subjects)
