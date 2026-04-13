from app.domain.repositories.academic_warning_repository import (
    AcademicWarningRepository,
)
from app.domain.repositories.student_repository import StudentRepository
from app.domain.repositories.student_stat_repository import StudentStatRepository
from app.application.dto.parent_dto import (
    StudentStatusParentDTO,
    AcademicWarningParentDTO,
    PerformanceLevel,
)


class GetStudentWarningsByCodeUseCase:
    def __init__(
        self,
        student_repo: StudentRepository,
        warning_repo: AcademicWarningRepository,
        stat_repo: StudentStatRepository,
    ):
        self.student_repo = student_repo
        self.warning_repo = warning_repo
        self.stat_repo = stat_repo

    def execute(self, student_code: str) -> StudentStatusParentDTO:
        student = self.student_repo.get_by_code(student_code)
        if not student:
            return StudentStatusParentDTO(
                student_code=student_code,
                student_name="",
                status="",
                enrollment_year=0,
                performance_level=PerformanceLevel.AVERAGE,
                has_warnings=False,
                warnings=[],
                support_phone="0123456789",
            )

        stat = self.stat_repo.get_latest_stat(student.id)
        performance_level = PerformanceLevel.get_level(
            stat.cumulative_gpa if stat else None
        )

        academic_warnings = self.warning_repo.get_by_student_code(student_code)

        warning_dtos = [
            AcademicWarningParentDTO(
                semester_id=w.semester_id,
                warning_level=w.warning_level,
                warning_reason=w.warning_reason,
                created_at=w.created_at,
            )
            for w in academic_warnings
            if w.is_warning()
        ]

        has_warnings = any(w.is_warning() for w in academic_warnings)

        return StudentStatusParentDTO(
            student_code=student_code,
            student_name=student.full_name,
            status=student.status,
            enrollment_year=student.enrollment_year or 0,
            performance_level=performance_level,
            has_warnings=has_warnings,
            warnings=warning_dtos,
            support_phone="0123456789",
        )
