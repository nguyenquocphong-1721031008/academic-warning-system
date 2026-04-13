from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

PublicWarningLevel = Literal["none", "low", "medium", "high", "critical"]
InternalWarningLevel = Literal["none", "low", "medium", "high", "critical"]


class PublicWarningResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_code: str
    has_warning: bool
    warning_level: PublicWarningLevel
    message_vi: str
    support_phone: str


class InternalWarningItemDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    semester_id: str
    semester_name: str
    academic_year: str
    warning_level: str
    warning_status: Optional[str] = "open"
    warning_note: Optional[str] = None
    total_subjects: int
    total_failed: int
    fail_ratio: Optional[float] = None
    semester_gpa: Optional[float] = None
    cumulative_gpa: Optional[float] = None
    created_at: Optional[str] = None


class ViolationItemDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_vi: str


class ParentWarningResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_code: str
    student_name: str
    status: str
    enrollment_year: int
    performance_level: str
    has_warnings: bool
    support_phone: str
    warnings: List[InternalWarningItemDTO] = Field(default_factory=list)


class InternalWarningResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_code: str
    full_name: str
    class_code: Optional[str] = None
    semester_gpa: Optional[float] = None
    cumulative_gpa: Optional[float] = None
    warnings: List[InternalWarningItemDTO] = Field(default_factory=list)
    violations: List[ViolationItemDTO] = Field(default_factory=list)
    warning_level: InternalWarningLevel
