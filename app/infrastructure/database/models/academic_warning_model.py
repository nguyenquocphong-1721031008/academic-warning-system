from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    ForeignKey,
    Enum as SQLEnum,
    UniqueConstraint,
)
from app.infrastructure.database.base import Base
import uuid


class AcademicWarningModel(Base):
    __tablename__ = "academic_warnings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(
        String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    semester_id = Column(String, ForeignKey("semesters.id"), nullable=False)
    total_subjects = Column(Integer, nullable=True)
    total_failed = Column(Integer, nullable=True)
    fail_ratio = Column(Numeric(5, 2), nullable=True)
    semester_gpa = Column(Numeric(3, 2), nullable=True)
    cumulative_gpa = Column(Numeric(3, 2), nullable=True)
    warning_level = Column(
        SQLEnum("normal", "warning", name="warning_level_type"), default="normal"
    )
    warning_reason = Column(String, nullable=True)
    warning_status = Column(
        SQLEnum("open", "closed", "review", name="warning_status_type"), default="open"
    )
    warning_note = Column(String, nullable=True)
    rule_set_id = Column(String, ForeignKey("warning_rule_sets.id"), nullable=True)
    created_at = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "student_id", "semester_id", name="uq_student_semester_warning"
        ),
    )
