from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.warning_rule import WarningRule


class WarningRuleRepository(ABC):
    @abstractmethod
    def get_active_rules(self) -> List[WarningRule]: ...

    def get_active_rule_set_id(self) -> Optional[str]:
        rules = self.get_active_rules()
        if not rules:
            return None
        return rules[0].rule_set_id

    @abstractmethod
    def get_by_id(self, rule_id: str) -> Optional[WarningRule]: ...

    @abstractmethod
    def get_by_rule_set_id(self, rule_set_id: str) -> List[WarningRule]: ...

    @abstractmethod
    def create(self, rule: WarningRule) -> WarningRule: ...

    @abstractmethod
    def update(self, rule: WarningRule) -> WarningRule: ...

    @abstractmethod
    def delete(self, rule_id: str) -> bool: ...
