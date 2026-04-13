from typing import Optional
from datetime import date


class Student:
    def __init__(
        self,
        id: str,
        student_code: str,
        last_name: str,
        first_name: str,
        gender: str,
        date_of_birth: Optional[date] = None,
        class_id: str = None,
        status: str = "studying",
        enrollment_year: int = None,
        class_code: Optional[str] = None,
    ):
        self.id = id
        self.student_code = student_code
        self.last_name = last_name
        self.first_name = first_name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.class_id = class_id
        self.status = status
        self.enrollment_year = enrollment_year
        self.class_code = class_code

    @property
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}"
