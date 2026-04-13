from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.semester_stat_row import SemesterStatRegenerationRow
from app.domain.entities.student_semester_stat import StudentSemesterStat


class StudentStatRepository(ABC):
    @abstractmethod
    def get_latest_stat(self, student_id: str) -> Optional[StudentSemesterStat]: ...

    @abstractmethod
    def get_by_student_and_semester(
        self,
        student_id: str,
        semester_id: str,
    ) -> Optional[StudentSemesterStat]: ...

    @abstractmethod
    def list_for_warning_regeneration(self) -> List[SemesterStatRegenerationRow]: ...

    @abstractmethod
    def get_latest_regeneration_row_for_student(
        self,
        student_id: str,
    ) -> Optional[SemesterStatRegenerationRow]: ...
