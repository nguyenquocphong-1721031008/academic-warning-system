from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.student import Student


class StudentRepository(ABC):
    @abstractmethod
    def get_by_code(self, student_code: str) -> Optional[Student]: ...

    @abstractmethod
    def get_by_id(self, student_id: str) -> Optional[Student]: ...
