from sqlalchemy import Column, String, Date, Integer, ForeignKey, Enum as SQLEnum
from app.infrastructure.database.base import Base
import uuid


class StudentModel(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_code = Column(String, unique=True, nullable=False, index=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    gender = Column(SQLEnum("male", "female", name="gender_type"), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    class_id = Column(String, ForeignKey("classes.id"), nullable=False)
    status = Column(
        SQLEnum("studying", "dismissed", name="student_status_type"), default="studying"
    )
    enrollment_year = Column(Integer, nullable=False)
    created_at = Column(String, nullable=True)
