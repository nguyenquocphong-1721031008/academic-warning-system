from typing import Optional
from decimal import Decimal
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel


class RuleType(str, Enum):
    SEMESTER_GPA = "semester_gpa"
    CUMULATIVE_GPA = "cumulative_gpa"
    FAIL_RATIO = "fail_ratio"
    FAILED_SUBJECTS = "failed_subjects"


class ComparisonOperator(str, Enum):
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="


class WarningRuleSetCreateDTO(BaseModel):
    name: str
    description: Optional[str] = None
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool = True


class WarningRuleSetUpdateDTO(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None


class WarningRuleCreateDTO(BaseModel):
    rule_set_id: str
    rule_type: RuleType
    min_year: int = 1
    max_year: int = 10
    threshold: Decimal
    comparison_operator: ComparisonOperator = ComparisonOperator.LT


class WarningRuleUpdateDTO(BaseModel):
    rule_type: Optional[RuleType] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    threshold: Optional[Decimal] = None
    comparison_operator: Optional[ComparisonOperator] = None


class WarningRuleSetResponseDTO(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WarningRuleResponseDTO(BaseModel):
    id: str
    rule_set_id: str
    rule_type: RuleType
    min_year: int
    max_year: int
    threshold: Decimal
    comparison_operator: ComparisonOperator
    created_at: datetime

    class Config:
        from_attributes = True
