from typing import List, Literal, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field


class AcademicWarningDTO(BaseModel):
    id: str = Field(..., description="ID cảnh báo")
    semester_id: str = Field(..., description="ID học kỳ")
    semester_name: str = Field(..., description="Tên học kỳ (HK1, HK2, ...)")
    academic_year: str = Field(..., description="Năm học (ví dụ: 2018-2019)")
    warning_level: str = Field(..., description="Mức cảnh báo: normal / warning")
    warning_status: Optional[str] = Field(
        "open", description="Trạng thái cảnh báo: open / closed / review"
    )
    warning_note: Optional[str] = Field(None, description="Ghi chú cảnh báo")
    total_subjects: int = Field(..., description="Tổng số môn học")
    total_failed: int = Field(..., description="Số môn trượt")
    fail_ratio: Decimal = Field(..., description="Tỷ lệ trượt (0.00 - 1.00)")
    semester_gpa: Optional[Decimal] = Field(None, description="Điểm trung bình học kỳ")
    cumulative_gpa: Optional[Decimal] = Field(
        None, description="Điểm trung bình tích lũy"
    )
    created_at: datetime = Field(..., description="Thời gian tạo cảnh báo")


class UpdateWarningStatusDTO(BaseModel):
    warning_status: Literal["open", "closed", "review"] = Field(
        ...,
        description="Trạng thái cảnh báo",
    )
    warning_note: Optional[str] = Field(None, description="Ghi chú cảnh báo")


class StudentWarningResponseDTO(BaseModel):
    student_code: str = Field(..., description="Mã sinh viên")
    full_name: Optional[str] = Field(
        None, description="Họ và tên đầy đủ (null khi không tìm thấy SV)"
    )
    class_code: Optional[str] = Field(None, description="Mã lớp")
    has_warnings: bool = Field(..., description="Có cảnh báo hay không")
    warnings: List[AcademicWarningDTO] = Field(
        default_factory=list, description="Danh sách cảnh báo"
    )
    message: Optional[str] = Field(None, description="Thông báo bổ sung nếu cần")
