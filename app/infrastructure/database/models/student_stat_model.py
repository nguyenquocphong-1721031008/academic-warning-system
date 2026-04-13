from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, UniqueConstraint
from app.infrastructure.database.base import Base
import uuid


class StudentSemesterStatModel(Base):
    __tablename__ = "student_semester_stats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    semester_id = Column(String, ForeignKey("semesters.id"), nullable=False)
    total_subjects = Column(Integer, nullable=True)
    total_failed = Column(Integer, nullable=True)
    semester_gpa = Column(Numeric(3, 2), nullable=True)
    cumulative_gpa = Column(Numeric(3, 2), nullable=True)
    created_at = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("student_id", "semester_id", name="uq_student_semester"),
    )
