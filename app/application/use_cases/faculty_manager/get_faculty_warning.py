from typing import List, Optional
from app.infrastructure.database.repositories.academic_warning_repository_impl import (
    AcademicWarningRepositoryImpl,
)


class GetFacultyWarningsUseCase:
    def __init__(self, warning_repo: AcademicWarningRepositoryImpl):
        self.warning_repo = warning_repo

    def execute(self, faculty_id: Optional[str]) -> List[dict]:
        warnings = self.warning_repo.get_by_faculty(faculty_id)

        return [
            {
                "student_code": w["student_code"],
                "full_name": w["full_name"],
                "class_code": w["class_code"],
                "semester_name": w["semester_name"],
                "academic_year": w["academic_year"],
                "warning_level": w["warning_level"],
                "total_subjects": w["total_subjects"],
                "total_failed": w["total_failed"],
                "fail_ratio": w["fail_ratio"],
                "semester_gpa": w["semester_gpa"],
                "cumulative_gpa": w["cumulative_gpa"],
                "warning_reason": w["warning_reason"],
                "created_at": w["created_at"],
            }
            for w in warnings
            if w["warning_level"] != "normal"
        ]
