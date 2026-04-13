from typing import Optional
from decimal import Decimal


class StudentSemesterStat:
    def __init__(
        self,
        id: str,
        student_id: str,
        semester_id: str,
        total_subjects: int,
        total_failed: int,
        semester_gpa: Optional[Decimal] = None,
        cumulative_gpa: Optional[Decimal] = None,
    ):
        self.id = id
        self.student_id = student_id
        self.semester_id = semester_id
        self.total_subjects = total_subjects
        self.total_failed = total_failed
        self.semester_gpa = semester_gpa
        self.cumulative_gpa = cumulative_gpa

    def fail_ratio(self) -> Decimal:
        if self.total_subjects == 0:
            return Decimal("0")
        return Decimal(self.total_failed) / Decimal(self.total_subjects)
