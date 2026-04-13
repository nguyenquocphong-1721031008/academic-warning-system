from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
import pandas as pd
from sqlalchemy.orm import Session

from app.api.auth_router import get_current_admin
from app.api.schemas.response import success_response
from app.application.use_cases.admin.import_scores import ImportScoresUseCase
from app.domain.entities.user import User
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/scores", tags=["scores"])
_ALLOWED_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",  # some clients
}


@router.post("/import")
async def import_scores(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file Excel .xlsx")
    if file.content_type and file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Định dạng file không hợp lệ")

    max_bytes = int(get_settings().max_upload_mb) * 1024 * 1024
    size = None
    try:
        pos = file.file.tell()
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(pos)
    except Exception:
        size = None
    if size is not None and size > max_bytes:
        raise HTTPException(status_code=413, detail="File quá lớn")

    df = pd.read_excel(file.file, dtype={"Mã sinh viên": str, "Mã lớp học phần": str})
    df.columns = df.columns.str.strip().str.replace("\n", " ").str.replace("  ", " ")
    required_columns = [
        "Mã sinh viên",
        "Họ đệm",
        "Tên",
        "Tên môn học",
        "Mã lớp học phần",
        "Điểm 10",
        "Điểm 4",
        "Điểm chữ",
    ]
    for col in required_columns:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Thiếu cột trong Excel: {col}")
    usecase = ImportScoresUseCase(db)
    inserted = usecase.execute(df)
    return success_response(
        data={"inserted_rows": inserted},
        message_vi="Import điểm thành công",
        message_en="Scores imported successfully",
    )
