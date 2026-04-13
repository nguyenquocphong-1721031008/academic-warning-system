from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.academic_warning import AcademicWarning
from app.domain.entities.academic_warning_draft import AcademicWarningDraft


class AcademicWarningRepository(ABC):
    @abstractmethod
    def get_by_student_code(self, student_code: str) -> List[AcademicWarning]: ...

    @abstractmethod
    def get_by_student_id(self, student_id: str) -> List[AcademicWarning]: ...

    @abstractmethod
    def get_latest_by_student_code(
        self,
        student_code: str,
    ) -> Optional[AcademicWarning]: ...

    @abstractmethod
    def clear_all(self) -> None: ...

    @abstractmethod
    def bulk_insert(self, drafts: List[AcademicWarningDraft]) -> None: ...

    @abstractmethod
    def list_filtered(
        self,
        faculty_id: str | None,
        class_id: str | None,
        semester_id: str | None,
        page: int,
        size: int,
    ) -> list[dict]: ...

    @abstractmethod
    def count_filtered(
        self,
        faculty_id: str | None,
        class_id: str | None,
        semester_id: str | None,
    ) -> int: ...

    @abstractmethod
    def analytics_summary(self) -> dict: ...

    @abstractmethod
    def update_warning_status(
        self, warning_id: str, warning_status: str, warning_note: str | None
    ) -> bool: ...
