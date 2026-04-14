from typing import Optional
from datetime import datetime


class User:
    def __init__(
        self,
        id: str,
        username: str,
        password_hash: str,
        role: str,
        faculty_id: Optional[str] = None,
        student_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        is_active: bool = True,
    ):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.faculty_id = faculty_id
        self.student_id = student_id
        self.created_at = created_at or datetime.now()
        self.is_active = is_active

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_faculty_manager(self) -> bool:
        return self.role == "faculty_manager"

    def is_student(self) -> bool:
        return self.role == "student"

    def can_access_faculty(self, faculty_id: str) -> bool:
        if self.is_admin():
            return True
        if self.is_faculty_manager():
            return self.faculty_id == faculty_id
        return False
