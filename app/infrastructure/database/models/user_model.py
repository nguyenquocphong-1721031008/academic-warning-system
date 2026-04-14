from sqlalchemy import Boolean, Column, String, ForeignKey, Enum as SQLEnum
from app.infrastructure.database.base import Base
import uuid


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    role = Column(
        SQLEnum("admin", "faculty_manager", name="user_role_type"), nullable=False
    )

    faculty_id = Column(
        String, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True
    )

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(String, nullable=True)
