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
    enrollment_year: int | None = None,
    semester_id: str | None = None,
    faculty_id: str | None = None,
    major_id: str | None = None,
    status_filter: str | None = None,
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
    effective_faculty_id = (
        current_user.faculty_id if current_user.is_faculty_manager() else faculty_id
    )
    if status_filter not in {None, "studying", "warning", "near_warning_ml"}:
        raise HTTPException(status_code=400, detail="status_filter không hợp lệ")
    if status_filter == "near_warning_ml" and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin được phép lọc theo trạng thái ML",
        )

    if major_id is not None or status_filter is not None:
        items = student_repo.list_students_filtered(
            skip=skip,
            limit=limit,
            enrollment_year=enrollment_year,
            faculty_id=effective_faculty_id,
            major_id=major_id,
            status_filter=status_filter,
        )
        total = student_repo.count_students_filtered(
            enrollment_year=enrollment_year,
            faculty_id=effective_faculty_id,
            major_id=major_id,
            status_filter=status_filter,
        )
    else:
        items = usecase.execute(
            effective_faculty_id,
            skip,
            limit,
            enrollment_year=enrollment_year,
            semester_id=semester_id,
        )
        total = len(items)

    page = (skip // limit) + 1 if limit > 0 else 1
    return success_response(
        data={
            "items": items,
            "pagination": {
                "page": page,
                "size": limit,
                "total": total,
                "pages": (total + limit - 1) // limit if limit > 0 else 1,
            },
        },
        message_vi="Danh sách sinh viên",
        message_en="Student list",
    )


@router.get("/students/filter-options")
def get_student_filter_options(
    current_user: User = Depends(get_current_admin_or_faculty_manager),
    db: Session = Depends(get_db),
):
    if not current_user.is_faculty_manager() and (not current_user.is_admin()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty Manager access required",
        )
    student_repo = StudentRepositoryImpl(db)
    faculty_id = None if current_user.is_admin() else current_user.faculty_id
    enrollment_years = student_repo.list_enrollment_years(faculty_id)
    semesters = student_repo.list_semesters(faculty_id)
    faculties = student_repo.list_faculties() if current_user.is_admin() else []
    majors = student_repo.list_majors(faculty_id)
    return success_response(
        data={
            "enrollment_years": enrollment_years,
            "semesters": semesters,
            "faculties": faculties,
            "majors": majors,
            "statuses": (
                [
                    {"id": "studying", "name_vi": "Đang học", "name_en": "Studying"},
                    {"id": "warning", "name_vi": "Cảnh báo", "name_en": "Warning"},
                ]
                if not current_user.is_admin()
                else [
                    {"id": "studying", "name_vi": "Đang học", "name_en": "Studying"},
                    {"id": "warning", "name_vi": "Cảnh báo", "name_en": "Warning"},
                    {
                        "id": "near_warning_ml",
                        "name_vi": "Sắp cảnh báo (ML)",
                        "name_en": "Near warning (ML)",
                    },
                ]
            ),
        },
        message_vi="Tùy chọn lọc sinh viên",
        message_en="Student filter options",
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
