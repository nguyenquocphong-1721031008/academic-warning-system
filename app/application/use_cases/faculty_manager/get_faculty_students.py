from typing import List
from app.domain.repositories.student_repository import StudentRepository
from app.domain.repositories.academic_warning_repository import (
    AcademicWarningRepository,
)


class GetFacultyStudentsUseCase:
    def __init__(
        self, student_repo: StudentRepository, warning_repo: AcademicWarningRepository
    ):
        self.student_repo = student_repo
        self.warning_repo = warning_repo

    def execute(self, faculty_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        students = self.student_repo.get_by_faculty(faculty_id, skip, limit)

        result = []

        for s in students:
            warnings = self.warning_repo.get_by_student_id(s.id)

            result.append(
                {
                    "student_code": s.student_code,
                    "full_name": f"{s.last_name} {s.first_name}",
                    "class_code": s.class_code,
                    "has_warning": any(w.warning_level != "normal" for w in warnings),
                }
            )

        return result
