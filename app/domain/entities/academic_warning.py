from typing import Optional
from decimal import Decimal
from datetime import datetime


class AcademicWarning:
    def __init__(
        self,
        id: str,
        student_id: str,
        semester_id: str,
        semester_name: str,
        academic_year: str,
        warning_level: str,
        total_subjects: Optional[int] = None,
        total_failed: Optional[int] = None,
        fail_ratio: Optional[Decimal] = None,
        semester_gpa: Optional[Decimal] = None,
        cumulative_gpa: Optional[Decimal] = None,
        warning_reason: Optional[str] = None,
        rule_set_id: Optional[str] = None,
        warning_status: str = "open",
        warning_note: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.student_id = student_id
        self.semester_id = semester_id
        self.semester_name = semester_name
        self.academic_year = academic_year
        self.warning_level = warning_level
        self.total_subjects = total_subjects
        self.total_failed = total_failed
        self.fail_ratio = fail_ratio
        self.semester_gpa = semester_gpa
        self.cumulative_gpa = cumulative_gpa
        self.warning_reason = warning_reason
        self.rule_set_id = rule_set_id
        self.warning_status = warning_status
        self.warning_note = warning_note
        self.created_at = created_at or datetime.now()

    def is_warning(self) -> bool:
        return self.warning_level == "warning"
