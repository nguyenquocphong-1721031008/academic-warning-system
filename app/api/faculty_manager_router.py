from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.auth_router import get_current_admin_or_faculty_manager
from app.api.schemas.response import success_response
from app.application.use_cases.faculty_manager.get_faculty_students import (
    GetFacultyStudentsUseCase,
)
from app.application.use_cases.faculty_manager.get_faculty_warning import (
    GetFacultyWarningsUseCase,
)
from app.domain.entities.user import User
from app.infrastructure.database.repositories.academic_warning_repository_impl import (
    AcademicWarningRepositoryImpl,
)
from app.infrastructure.database.repositories.student_repository_impl import (
    StudentRepositoryImpl,
)
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/faculty-manager", tags=["faculty-manager"])


@router.get("/students")
def get_faculty_students(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_or_faculty_manager),
    db: Session = Depends(get_db),
):
    if not current_user.is_faculty_manager() and (not current_user.is_admin()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty Manager access required",
        )
    student_repo = StudentRepositoryImpl(db)
    warning_repo = AcademicWarningRepositoryImpl(db)
    usecase = GetFacultyStudentsUseCase(student_repo, warning_repo)
    faculty_id = None if current_user.is_admin() else current_user.faculty_id
    return success_response(
        data=usecase.execute(faculty_id, skip, limit),
        message_vi="Danh sách sinh viên",
        message_en="Student list",
    )


@router.get("/warnings")
def get_faculty_warnings(
    current_user: User = Depends(get_current_admin_or_faculty_manager),
    db: Session = Depends(get_db),
):
    if not current_user.is_faculty_manager() and (not current_user.is_admin()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty Manager access required",
        )
    warning_repo = AcademicWarningRepositoryImpl(db)
    usecase = GetFacultyWarningsUseCase(warning_repo)
    faculty_id = None if current_user.is_admin() else current_user.faculty_id
    return success_response(
        data=usecase.execute(faculty_id),
        message_vi="Danh sách cảnh báo khoa",
        message_en="Faculty warnings",
    )
