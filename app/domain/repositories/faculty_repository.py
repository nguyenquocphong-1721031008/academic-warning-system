from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.faculty import Faculty


class FacultyRepository(ABC):
    @abstractmethod
    def get_by_id(self, faculty_id: str) -> Optional[Faculty]: ...

    @abstractmethod
    def get_all(self) -> List[Faculty]: ...

    @abstractmethod
    def create(self, faculty: Faculty) -> Faculty: ...

    @abstractmethod
    def update(self, faculty: Faculty) -> Faculty: ...

    @abstractmethod
    def delete(self, faculty_id: str) -> bool: ...
