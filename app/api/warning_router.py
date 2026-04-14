from typing import Annotated, Optional

import csv
import io
import logging
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_optional_user, is_internal_warning_viewer
from app.api.schemas.response import success_response
from app.application.services.warning_status_service import WarningStatusService
from app.application.warning_rule_engine import WarningRuleEngine
from app.domain.entities.user import User
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.repositories.academic_warning_repository_impl import (
    AcademicWarningRepositoryImpl,
)
from app.infrastructure.database.repositories.student_repository_impl import (
    StudentRepositoryImpl,
)
from app.infrastructure.database.repositories.student_stat_repository_impl import (
    StudentStatRepositoryImpl,
)
from app.infrastructure.database.repositories.warning_rule_repository_impl import (
    WarningRuleRepositoryImpl,
)
from app.infrastructure.database.session import get_db
from app.infrastructure.ml.registry import MlRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/warnings", tags=["warnings"])

StudentCodePath = Annotated[str, Path(description="Mã sinh viên (MSSV)")]


def _warning_service(db: Session) -> WarningStatusService:
    return WarningStatusService(
        student_repo=StudentRepositoryImpl(db),
        stat_repo=StudentStatRepositoryImpl(db),
        warning_repo=AcademicWarningRepositoryImpl(db),
        rule_engine=WarningRuleEngine(WarningRuleRepositoryImpl(db)),
        support_phone=get_settings().support_phone,
    )


def _effective_faculty_scope(
    current_user: Optional[User],
    requested_faculty_id: Optional[str],
) -> Optional[str]:
    if current_user is None:
        raise HTTPException(status_code=403, detail="Cần đăng nhập để truy cập dữ liệu nội bộ")
    if current_user.is_admin():
        return requested_faculty_id
    if current_user.is_faculty_manager():
        if not current_user.faculty_id:
            raise HTTPException(status_code=403, detail="Tài khoản quản lý khoa chưa được gán khoa")
        if requested_faculty_id and requested_faculty_id != current_user.faculty_id:
            raise HTTPException(status_code=403, detail="Chỉ được xem dữ liệu của khoa bạn")
        return current_user.faculty_id
    raise HTTPException(status_code=403, detail="Không có quyền truy cập dữ liệu nội bộ")


@router.get("")
def list_warnings(
    faculty_id: Optional[str] = None,
    class_id: Optional[str] = None,
    semester_id: Optional[str] = None,
    page: int = Query(1, ge=1, le=10000),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    if not is_internal_warning_viewer(current_user):
        raise HTTPException(
            status_code=403, detail="Chỉ nội bộ mới xem được danh sách cảnh báo"
        )

    effective_faculty_id = _effective_faculty_scope(current_user, faculty_id)
    repo = AcademicWarningRepositoryImpl(db)
    warnings = repo.list_filtered(effective_faculty_id, class_id, semester_id, page, size)
    total = repo.count_filtered(effective_faculty_id, class_id, semester_id)

    return success_response(
        data={
            "items": warnings,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "pages": (total + size - 1) // size if size > 0 else 1,
            },
        },
        message_vi="Danh sách cảnh báo học vụ",
        message_en="Warning list",
    )


@router.get("/analytics")
def warnings_analytics(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not is_internal_warning_viewer(current_user):
        raise HTTPException(
            status_code=403, detail="Chỉ nội bộ mới xem được thống kê cảnh báo"
        )

    effective_faculty_id = _effective_faculty_scope(current_user, None)
    repo = AcademicWarningRepositoryImpl(db)
    summary = repo.analytics_summary(effective_faculty_id)
    return success_response(
        data=summary,
        message_vi="Thống kê cảnh báo học vụ",
        message_en="Warning analytics",
    )


@router.get("/export")
def export_warnings_csv(
    faculty_id: Optional[str] = None,
    class_id: Optional[str] = None,
    semester_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not is_internal_warning_viewer(current_user):
        raise HTTPException(
            status_code=403, detail="Chỉ nội bộ mới export được dữ liệu"
        )

    effective_faculty_id = _effective_faculty_scope(current_user, faculty_id)
    repo = AcademicWarningRepositoryImpl(db)
    rows = repo.list_filtered(
        effective_faculty_id,
        class_id,
        semester_id,
        page=1,
        size=200000,
    )

    output = io.StringIO(newline="")
    header = [
        "student_code",
        "full_name",
        "date_of_birth",
        "class_code",
        "faculty_id",
        "semester_name",
        "academic_year",
        "warning_level",
        "total_subjects",
        "total_failed",
        "fail_ratio",
        "semester_gpa",
        "cumulative_gpa",
        "warning_reason",
        "created_at",
    ]
    writer = csv.DictWriter(
        output,
        fieldnames=header,
        extrasaction="ignore",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({col: row.get(col, "") for col in header})

    csv_content = "\ufeff" + output.getvalue()
    bytes_buffer = io.BytesIO(csv_content.encode("utf-8"))
    bytes_buffer.seek(0)
    return StreamingResponse(
        bytes_buffer,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=warnings.csv"},
    )


@router.get("/export-xlsx")
def export_warnings_xlsx(
    faculty_id: Optional[str] = None,
    class_id: Optional[str] = None,
    semester_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not is_internal_warning_viewer(current_user):
        raise HTTPException(
            status_code=403, detail="Chỉ nội bộ mới export được dữ liệu"
        )

    effective_faculty_id = _effective_faculty_scope(current_user, faculty_id)
    repo = AcademicWarningRepositoryImpl(db)
    rows = repo.list_filtered(
        effective_faculty_id,
        class_id,
        semester_id,
        page=1,
        size=200000,
    )

    header = [
        "student_code",
        "full_name",
        "date_of_birth",
        "class_code",
        "faculty_id",
        "semester_name",
        "academic_year",
        "warning_level",
        "total_subjects",
        "total_failed",
        "fail_ratio",
        "semester_gpa",
        "cumulative_gpa",
        "warning_reason",
        "created_at",
    ]
    table_rows = [{col: row.get(col, "") for col in header} for row in rows]
    df = pd.DataFrame(table_rows, columns=header)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="warnings")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=warnings.xlsx"},
    )


@router.get("/analysis/{student_code}")
def analysis_student_warning(
    student_code: StudentCodePath,
    request: Request,
    db: Session = Depends(get_db),
    model: str = Query(
        "random_forest",
        description="Model type: random_forest | logistic_regression | xgboost",
        pattern="^(random_forest|logistic_regression|xgboost)$",
    ),
):
    warning_svc = _warning_service(db)
    internal = warning_svc.get_internal(student_code)
    if internal is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")

    from app.application.services.prediction_service import PredictionService
    from app.infrastructure.database.repositories.prediction_stats_repository import (
        SqlAlchemyPredictionStatsRepository,
    )
    from app.infrastructure.ml.predictor import WarningPredictor

    registry: MlRegistry = request.app.state.ml_registry
    try:
        loaded = registry.get(model)
    except KeyError:
        try:
            loaded = registry.load_one(model)
        except FileNotFoundError:
            raise HTTPException(
                status_code=503, detail=f"Model artifact not found for '{model}'"
            ) from None

    pred_svc = PredictionService(
        stats_reader=SqlAlchemyPredictionStatsRepository(),
        dropout_model=WarningPredictor(loaded=loaded),
    )

    try:
        ml = pred_svc.predict_warning_risk(student_code)
    except ValueError as exc:
        if str(exc) == "student_not_found":
            raise HTTPException(
                status_code=404, detail="Không tìm thấy sinh viên"
            ) from None
        raise HTTPException(status_code=400, detail=str(exc)) from None

    return success_response(
        data={
            "student_code": student_code,
            "warning": internal.model_dump(mode="json"),
            "ml_prediction": ml.model_dump(mode="json"),
        },
        message_vi="Phân tích cảnh báo học vụ và ML",
        message_en="Warning + ML analysis",
    )


@router.get("/{student_code}")
def get_student_warning_status(
    student_code: StudentCodePath,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
) -> dict:
    svc = _warning_service(db)

    if is_internal_warning_viewer(current_user):
        payload = svc.get_internal(student_code)
        if payload is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
        return success_response(
            data=payload.model_dump(mode="json"),
            message_vi="Tra cứu cảnh báo (chi tiết nội bộ)",
            message_en="Warning status (internal)",
        )

    payload = svc.get_public(student_code)
    if payload is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
    return success_response(
        data=payload.model_dump(mode="json"),
        message_vi="Tra cứu cảnh báo",
        message_en="Warning status",
    )


