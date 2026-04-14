from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.student import Student


class StudentRepository(ABC):
    @abstractmethod
    def get_by_code(self, student_code: str) -> Optional[Student]: ...

    @abstractmethod
    def get_by_id(self, student_id: str) -> Optional[Student]: ...

    @abstractmethod
    def get_by_faculty(
        self,
        faculty_id: Optional[str],
        skip: int,
        limit: int,
        enrollment_year: Optional[int] = None,
        semester_id: Optional[str] = None,
    ) -> list[Student]: ...

    @abstractmethod
    def list_enrollment_years(self, faculty_id: Optional[str] = None) -> list[int]: ...

    @abstractmethod
    def list_semesters(self, faculty_id: Optional[str] = None) -> list[dict]: ...

    @abstractmethod
    def list_faculties(self) -> list[dict]: ...

    @abstractmethod
    def list_majors(self, faculty_id: Optional[str] = None) -> list[dict]: ...

    @abstractmethod
    def list_students_filtered(
        self,
        skip: int,
        limit: int,
        enrollment_year: Optional[int] = None,
        faculty_id: Optional[str] = None,
        major_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> list[dict]: ...

    @abstractmethod
    def count_students_filtered(
        self,
        enrollment_year: Optional[int] = None,
        faculty_id: Optional[str] = None,
        major_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> int: ...
