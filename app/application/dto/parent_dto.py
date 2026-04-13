from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PerformanceLevel(str, Enum):
    EXCELLENT = "excellent"
    VERY_GOOD = "very_good"
    GOOD = "good"
    AVERAGE = "average"
    WARNING = "warning"
    CRITICAL = "critical"

    @classmethod
    def get_level(cls, cumulative_gpa: Optional[Decimal]) -> "PerformanceLevel":
        if cumulative_gpa is None:
            return cls.AVERAGE
        g = float(cumulative_gpa)
        if g >= 3.5:
            return cls.EXCELLENT
        if g >= 3.0:
            return cls.VERY_GOOD
        if g >= 2.5:
            return cls.GOOD
        if g >= 2.0:
            return cls.AVERAGE
        if g >= 1.5:
            return cls.WARNING
        return cls.CRITICAL


class AcademicWarningParentDTO(BaseModel):
    semester_id: str
    warning_level: str
    warning_reason: Optional[str] = None
    created_at: datetime


class StudentStatusParentDTO(BaseModel):
    student_code: str
    student_name: str = ""
    status: str = ""
    enrollment_year: int = 0
    performance_level: PerformanceLevel = Field(default=PerformanceLevel.AVERAGE)
    has_warnings: bool = False
    warnings: List[AcademicWarningParentDTO] = Field(default_factory=list)
    support_phone: str = "0123456789"
