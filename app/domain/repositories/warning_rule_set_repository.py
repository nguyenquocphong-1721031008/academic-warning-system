from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.warning_rule_set import WarningRuleSet


class WarningRuleSetRepository(ABC):
    @abstractmethod
    def get_by_id(self, rule_set_id: str) -> Optional[WarningRuleSet]: ...

    @abstractmethod
    def get_all(self) -> List[WarningRuleSet]: ...

    @abstractmethod
    def get_active(self) -> List[WarningRuleSet]: ...

    @abstractmethod
    def create(self, rule_set: WarningRuleSet) -> WarningRuleSet: ...

    @abstractmethod
    def update(self, rule_set: WarningRuleSet) -> WarningRuleSet: ...

    @abstractmethod
    def delete(self, rule_set_id: str) -> bool: ...

    @abstractmethod
    def toggle_active(self, rule_set_id: str, is_active: bool) -> bool: ...
