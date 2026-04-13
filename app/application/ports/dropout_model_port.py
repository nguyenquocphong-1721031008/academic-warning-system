from __future__ import annotations

from typing import Any, Protocol


class DropoutModelPort(Protocol):
    def predict(
        self,
        semester_gpa: float,
        cumulative_gpa: float,
        total_failed: int,
        total_subjects: int,
        prev_semester_gpa: float = 0,
        prev_total_failed: int = 0,
        was_warning: int = 0,
    ) -> dict[str, Any]: ...
