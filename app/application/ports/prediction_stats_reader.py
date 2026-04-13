from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class WarningRiskPredictionSnapshot:
    student_code: str
    enrollment_year: int
    semester_academic_year: Optional[str]
    student_id: str
    has_semester_stats: bool
    semester_gpa: Optional[float]
    cumulative_gpa: Optional[float]
    total_failed: Optional[int]
    total_subjects: Optional[int]
    warning_level: Optional[str]
    prev_semester_gpa: Optional[float]
    prev_total_failed: Optional[int]


class PredictionStatsReader(Protocol):
    def load_warning_risk_snapshot(
        self, student_code: str
    ) -> WarningRiskPredictionSnapshot | None: ...
