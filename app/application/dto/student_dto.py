from typing import Optional
from datetime import date
from pydantic import BaseModel


class StudentDTO(BaseModel):
    id: str
    student_code: str
    last_name: str
    first_name: str
    full_name: str
    gender: str
    date_of_birth: Optional[date] = None
    class_id: Optional[str] = None
    status: str
    enrollment_year: Optional[int] = None
