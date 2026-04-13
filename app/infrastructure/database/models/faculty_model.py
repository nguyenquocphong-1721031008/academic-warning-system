from sqlalchemy import Column, String
from app.infrastructure.database.base import Base
import uuid


class FacultyModel(Base):
    __tablename__ = "faculties"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
