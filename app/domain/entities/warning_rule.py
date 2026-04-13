from typing import Optional
from decimal import Decimal
from datetime import datetime


class WarningRule:
    def __init__(
        self,
        id: str,
        rule_set_id: str,
        rule_type: str,
        threshold: Decimal,
        comparison_operator: str,
        min_year: int = 1,
        max_year: int = 10,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.rule_set_id = rule_set_id
        self.rule_type = rule_type
        self.min_year = min_year
        self.max_year = max_year
        self.threshold = threshold
        self.comparison_operator = comparison_operator
        self.created_at = created_at

    def matches_year(self, year: int) -> bool:
        return self.min_year <= year <= self.max_year

    def evaluate(self, value: Optional[Decimal]) -> bool:
        if value is None:
            return False

        if self.comparison_operator == "<":
            return value < self.threshold
        elif self.comparison_operator == "<=":
            return value <= self.threshold
        elif self.comparison_operator == ">":
            return value > self.threshold
        elif self.comparison_operator == ">=":
            return value >= self.threshold
        elif self.comparison_operator == "=":
            return value == self.threshold

        return False
