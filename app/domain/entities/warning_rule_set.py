from typing import Optional
from datetime import date, datetime


class WarningRuleSet:
    def __init__(
        self,
        id: str,
        name: str,
        effective_from: date,
        description: Optional[str] = None,
        effective_to: Optional[date] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.effective_from = effective_from
        self.effective_to = effective_to
        self.is_active = is_active
        self.created_at = created_at or datetime.now()

    def is_effective(self, check_date: Optional[date] = None) -> bool:
        if not self.is_active:
            return False

        if check_date is None:
            check_date = date.today()

        if check_date < self.effective_from:
            return False

        if self.effective_to and check_date > self.effective_to:
            return False

        return True
