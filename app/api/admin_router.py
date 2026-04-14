from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth_router import get_current_admin
from app.infrastructure.config.settings import get_settings
from app.infrastructure.email_service import (
    EmailConfigError,
    EmailDeliveryError,
    send_email,
)
from app.api.schemas.response import success_response
from app.application.dto.faculty_dto import FacultyCreateDTO, FacultyUpdateDTO
from app.application.dto.user_dto import (
    UpdateUserStatusDTO,
    UserCreateDTO,
)
from app.application.dto.warning_rule_dto import (
    WarningRuleCreateDTO,
    WarningRuleSetCreateDTO,
    WarningRuleSetUpdateDTO,
    WarningRuleUpdateDTO,
)
from app.application.use_cases.admin.manage_faculties import (
    CreateFacultyUseCase,
    DeleteFacultyUseCase,
    GetFacultiesUseCase,
    UpdateFacultyUseCase,
)
from app.application.use_cases.admin.manage_users import (
    CreateUserUseCase,
    GetUsersUseCase,
    UpdateUserStatusUseCase,
)
from app.application.use_cases.admin.manage_warning_rules import (
    CreateWarningRuleSetUseCase,
    CreateWarningRuleUseCase,
    DeleteWarningRuleUseCase,
    ToggleWarningRuleSetUseCase,
    UpdateWarningRuleSetUseCase,
    UpdateWarningRuleUseCase,
)
from app.application.use_cases.admin.import_scores import ImportScoresUseCase
from app.application.use_cases.warnings.regenerate_academic_warnings import (
    RegenerateAcademicWarningsUseCase,
)
from app.domain.entities.user import User
from app.infrastructure.database.repositories.faculty_repository_impl import (
    FacultyRepositoryImpl,
)
from app.infrastructure.database.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from app.infrastructure.database.repositories.warning_rule_repository_impl import (
    WarningRuleRepositoryImpl,
)
from app.infrastructure.database.repositories.warning_rule_set_repository_impl import (
    WarningRuleSetRepositoryImpl,
)
from app.infrastructure.database.repositories.student_stat_repository_impl import (
    StudentStatRepositoryImpl,
)
from app.infrastructure.database.repositories.academic_warning_repository_impl import (
    AcademicWarningRepositoryImpl,
)
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

UserIdPath = Annotated[str, Path(description="User id (UUID)")]
FacultyIdPath = Annotated[str, Path(description="Faculty id (UUID)")]
RuleSetIdPath = Annotated[str, Path(description="Warning rule set id (UUID)")]
RuleIdPath = Annotated[str, Path(description="Warning rule id (UUID)")]


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    user_repo = UserRepositoryImpl(db)
    usecase = CreateUserUseCase(user_repo)
    out = usecase.execute(user_data)
    return success_response(
        data=out,
        message_vi="Đã tạo người dùng",
        message_en="User created",
    )


@router.get("/users")
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    user_repo = UserRepositoryImpl(db)
    usecase = GetUsersUseCase(user_repo)
    return success_response(
        data=usecase.execute(skip, limit),
        message_vi="Danh sách người dùng",
        message_en="User list",
    )


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: UserIdPath,
    payload: UpdateUserStatusDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    user_repo = UserRepositoryImpl(db)
    usecase = UpdateUserStatusUseCase(user_repo)
    usecase.execute(user_id, payload.is_active)
    return success_response(
        data=None,
        message_vi="Đã cập nhật trạng thái người dùng",
        message_en="User status updated",
    )


@router.post("/faculties", status_code=status.HTTP_201_CREATED)
def create_faculty(
    faculty_data: FacultyCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    faculty_repo = FacultyRepositoryImpl(db)
    usecase = CreateFacultyUseCase(faculty_repo)
    return success_response(
        data=usecase.execute(faculty_data),
        message_vi="Đã tạo khoa",
        message_en="Faculty created",
    )


@router.get("/faculties")
def get_faculties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    faculty_repo = FacultyRepositoryImpl(db)
    usecase = GetFacultiesUseCase(faculty_repo)
    return success_response(
        data=usecase.execute(),
        message_vi="Danh sách khoa",
        message_en="Faculty list",
    )


@router.put("/faculties/{faculty_id}")
def update_faculty(
    faculty_id: FacultyIdPath,
    faculty_data: FacultyUpdateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    faculty_repo = FacultyRepositoryImpl(db)
    usecase = UpdateFacultyUseCase(faculty_repo)
    return success_response(
        data=usecase.execute(faculty_id, faculty_data),
        message_vi="Đã cập nhật khoa",
        message_en="Faculty updated",
    )


@router.delete("/faculties/{faculty_id}")
def delete_faculty(
    faculty_id: FacultyIdPath,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    faculty_repo = FacultyRepositoryImpl(db)
    usecase = DeleteFacultyUseCase(faculty_repo)
    usecase.execute(faculty_id)
    return success_response(
        data=None,
        message_vi="Đã xóa khoa",
        message_en="Faculty deleted",
    )


@router.post("/warning-rule-sets", status_code=status.HTTP_201_CREATED)
def create_warning_rule_set(
    rule_set_data: WarningRuleSetCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    repo = WarningRuleSetRepositoryImpl(db)
    usecase = CreateWarningRuleSetUseCase(repo)
    return success_response(
        data=usecase.execute(rule_set_data),
        message_vi="Đã tạo bộ quy tắc",
        message_en="Warning rule set created",
    )


@router.get("/warning-rule-sets")
def get_warning_rule_sets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    repo = WarningRuleSetRepositoryImpl(db)
    return success_response(
        data=repo.get_all(),
        message_vi="Danh sách bộ quy tắc",
        message_en="Warning rule sets",
    )


@router.put("/warning-rule-sets/{rule_set_id}")
def update_warning_rule_set(
    rule_set_id: RuleSetIdPath,
    rule_set_data: WarningRuleSetUpdateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    repo = WarningRuleSetRepositoryImpl(db)
    usecase = UpdateWarningRuleSetUseCase(repo)
    return success_response(
        data=usecase.execute(rule_set_id, rule_set_data),
        message_vi="Đã cập nhật bộ quy tắc",
        message_en="Warning rule set updated",
    )


@router.post("/warning-rule-sets/{rule_set_id}/toggle")
def toggle_warning_rule_set(
    rule_set_id: RuleSetIdPath,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    repo = WarningRuleSetRepositoryImpl(db)
    usecase = ToggleWarningRuleSetUseCase(repo)
    usecase.execute(rule_set_id, is_active)
    return success_response(
        data=None,
        message_vi="Đã cập nhật trạng thái bộ quy tắc",
        message_en="Rule set status updated",
    )


@router.post("/warning-rules", status_code=status.HTTP_201_CREATED)
def create_warning_rule(
    rule_data: WarningRuleCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    repo = WarningRuleRepositoryImpl(db)
    usecase = CreateWarningRuleUseCase(repo)
    return success_response(
        data=usecase.execute(rule_data),
        message_vi="Đã tạo quy tắc",
        message_en="Warning rule created",
    )


@router.get("/warning-rules")
def get_warning_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    repo = WarningRuleRepositoryImpl(db)
    return success_response(
        data=repo.get_all(),
        message_vi="Danh sách quy tắc",
        message_en="Warning rules",
    )


@router.get("/warning-rule-sets/{rule_set_id}/rules")
def get_rules_by_set(
    rule_set_id: RuleSetIdPath,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    repo = WarningRuleRepositoryImpl(db)
    return success_response(
        data=repo.get_by_rule_set_id(rule_set_id),
        message_vi="Quy tắc theo bộ",
        message_en="Rules by rule set",
    )


@router.put("/warning-rules/{rule_id}")
def update_warning_rule(
    rule_id: RuleIdPath,
    rule_data: WarningRuleUpdateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    repo = WarningRuleRepositoryImpl(db)
    usecase = UpdateWarningRuleUseCase(repo)
    return success_response(
        data=usecase.execute(rule_id, rule_data),
        message_vi="Đã cập nhật quy tắc",
        message_en="Warning rule updated",
    )


@router.delete("/warning-rules/{rule_id}")
def delete_warning_rule(
    rule_id: RuleIdPath,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    repo = WarningRuleRepositoryImpl(db)
    usecase = DeleteWarningRuleUseCase(repo)
    usecase.execute(rule_id)
    return success_response(
        data=None,
        message_vi="Đã xóa quy tắc",
        message_en="Warning rule deleted",
    )


@router.post("/warnings/regenerate")
def regenerate_warning_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    import_scores_usecase = ImportScoresUseCase(db)
    import_scores_usecase.recalculate_all_stats_and_warnings()

    usecase = RegenerateAcademicWarningsUseCase(
        WarningRuleRepositoryImpl(db),
        StudentStatRepositoryImpl(db),
        AcademicWarningRepositoryImpl(db),
    )
    usecase.execute()

    return success_response(
        data={},
        message_vi="Đã tái tạo dữ liệu cảnh báo",
        message_en="Warning data regenerated",
    )


class SendWarningEmailDTO(BaseModel):
    student_code: str
    email: EmailStr
    model: str = "random_forest"


@router.post("/send-warning-email")
def send_warning_email(
    payload: SendWarningEmailDTO,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    from app.application.services.prediction_service import PredictionService
    from app.infrastructure.database.repositories.prediction_stats_repository import (
        SqlAlchemyPredictionStatsRepository,
    )
    from app.infrastructure.database.repositories.student_repository_impl import (
        StudentRepositoryImpl,
    )
    from app.infrastructure.ml.predictor import WarningPredictor
    from app.infrastructure.ml.registry import MlRegistry

    student = StudentRepositoryImpl(db).get_by_code(payload.student_code)
    if student is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")

    registry: MlRegistry = request.app.state.ml_registry
    try:
        loaded = registry.get(payload.model)
    except KeyError:
        try:
            loaded = registry.load_one(payload.model)
        except FileNotFoundError:
            raise HTTPException(
                status_code=503,
                detail=f"Model artifact not found for '{payload.model}'",
            ) from None

    pred_svc = PredictionService(
        stats_reader=SqlAlchemyPredictionStatsRepository(),
        dropout_model=WarningPredictor(loaded=loaded),
    )
    try:
        ml = pred_svc.predict_warning_risk(payload.student_code)
    except SQLAlchemyError:
        class _FallbackMl:
            risk_level = "unknown"
            risk_score = None
            recommendations = [
                "Hiện chưa lấy được dữ liệu dự báo. Vui lòng liên hệ cố vấn học tập để được hỗ trợ."
            ]

        ml = _FallbackMl()

    gpa_display = 0.0 if ml.risk_score is None else float(ml.risk_score)
    subject = "Cảnh báo học vụ - Hãy cải thiện ngay"
    support_phone = get_settings().support_phone
    body = f"""
Xin chào {student.full_name},

Hệ thống ghi nhận kết quả học tập gần đây của bạn có dấu hiệu đáng lo ngại:

* Mã sinh viên: {student.student_code}
* Mức độ rủi ro: {ml.risk_level}
* Risk score: {gpa_display:.4f}

👉 Nếu không cải thiện, bạn có thể bị cảnh báo học vụ trong học kỳ tới.

📌 Gợi ý cho bạn:
* {"; ".join(ml.recommendations[:3]) if ml.recommendations else "Liên hệ cố vấn học tập để được hỗ trợ."}
Sđt hỗ trợ: {support_phone}

Trân trọng,
Hệ thống hỗ trợ học tập
""".strip()

    try:
        send_email(str(payload.email), subject, body)
        sent_ok = True
    except EmailConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        db.execute(
            text(
                """
                INSERT INTO notification_logs
                    (id, student_id, semester_id, warning_id, message, sent_via, sent_at, status, created_at)
                VALUES (gen_random_uuid(), :student_id, NULL, NULL, :message, :sent_via, NOW(), :status, NOW())
                """
            ),
            {
                "student_id": student.id,
                "message": body,
                "sent_via": "email",
                "status": "sent" if sent_ok else "failed",
            },
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()

    return success_response(
        data={
            "sent": sent_ok,
            "student_code": student.student_code,
            "risk_level": ml.risk_level,
            "risk_score": ml.risk_score,
            "model": payload.model,
        },
        message_vi="Đã gửi email cảnh báo",
        message_en="Warning email sent",
    )
