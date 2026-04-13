import logging
from datetime import datetime
import uuid

from app.application.dto.warning_rule_dto import (
    WarningRuleCreateDTO,
    WarningRuleResponseDTO,
    WarningRuleSetCreateDTO,
    WarningRuleSetResponseDTO,
    WarningRuleSetUpdateDTO,
    WarningRuleUpdateDTO,
)
from app.domain.entities.warning_rule import WarningRule
from app.domain.entities.warning_rule_set import WarningRuleSet
from app.domain.repositories.warning_rule_repository import WarningRuleRepository
from app.domain.repositories.warning_rule_set_repository import WarningRuleSetRepository

logger = logging.getLogger(__name__)


class CreateWarningRuleSetUseCase:
    def __init__(self, rule_set_repo: WarningRuleSetRepository):
        self.rule_set_repo = rule_set_repo

    def execute(
        self, rule_set_data: WarningRuleSetCreateDTO
    ) -> WarningRuleSetResponseDTO:
        rule_set = WarningRuleSet(
            id=str(uuid.uuid4()),
            name=rule_set_data.name,
            description=rule_set_data.description,
            effective_from=rule_set_data.effective_from,
            effective_to=rule_set_data.effective_to,
            is_active=rule_set_data.is_active,
            created_at=datetime.now(),
        )

        created = self.rule_set_repo.create(rule_set)

        return WarningRuleSetResponseDTO(
            id=created.id,
            name=created.name,
            description=created.description,
            effective_from=created.effective_from,
            effective_to=created.effective_to,
            is_active=created.is_active,
            created_at=created.created_at.isoformat(),
        )


class UpdateWarningRuleSetUseCase:
    def __init__(self, rule_set_repo: WarningRuleSetRepository):
        self.rule_set_repo = rule_set_repo

    def execute(
        self, rule_set_id: str, rule_set_data: WarningRuleSetUpdateDTO
    ) -> WarningRuleSetResponseDTO:
        rule_set = self.rule_set_repo.get_by_id(rule_set_id)
        if not rule_set:
            raise ValueError(f"Warning rule set {rule_set_id} not found")

        if rule_set_data.name is not None:
            rule_set.name = rule_set_data.name
        if rule_set_data.description is not None:
            rule_set.description = rule_set_data.description
        if rule_set_data.effective_from is not None:
            rule_set.effective_from = rule_set_data.effective_from
        if rule_set_data.effective_to is not None:
            rule_set.effective_to = rule_set_data.effective_to
        if rule_set_data.is_active is not None:
            rule_set.is_active = rule_set_data.is_active

        updated = self.rule_set_repo.update(rule_set)
        logger.info(
            "Warning rule set updated: %s (active=%s, effective_from=%s, effective_to=%s)",
            updated.id,
            updated.is_active,
            updated.effective_from,
            updated.effective_to,
        )

        return WarningRuleSetResponseDTO(
            id=updated.id,
            name=updated.name,
            description=updated.description,
            effective_from=updated.effective_from,
            effective_to=updated.effective_to,
            is_active=updated.is_active,
            created_at=updated.created_at.isoformat(),
        )


class ToggleWarningRuleSetUseCase:
    def __init__(self, rule_set_repo: WarningRuleSetRepository):
        self.rule_set_repo = rule_set_repo

    def execute(self, rule_set_id: str, is_active: bool) -> bool:
        return self.rule_set_repo.toggle_active(rule_set_id, is_active)


class CreateWarningRuleUseCase:
    def __init__(self, rule_repo: WarningRuleRepository):
        self.rule_repo = rule_repo

    def execute(self, rule_data: WarningRuleCreateDTO) -> WarningRuleResponseDTO:
        rule = WarningRule(
            id=str(uuid.uuid4()),
            rule_set_id=rule_data.rule_set_id,
            rule_type=rule_data.rule_type,
            min_year=rule_data.min_year,
            max_year=rule_data.max_year,
            threshold=rule_data.threshold,
            comparison_operator=rule_data.comparison_operator,
        )

        created = self.rule_repo.create(rule)
        logger.info(
            "Warning rule created: %s in rule_set %s rule_type=%s threshold=%s %s",
            created.id,
            created.rule_set_id,
            created.rule_type,
            created.threshold,
            created.comparison_operator,
        )

        return WarningRuleResponseDTO(
            id=created.id,
            rule_set_id=created.rule_set_id,
            rule_type=created.rule_type,
            min_year=created.min_year,
            max_year=created.max_year,
            threshold=created.threshold,
            comparison_operator=created.comparison_operator,
            created_at=datetime.now().isoformat(),
        )


class UpdateWarningRuleUseCase:
    def __init__(self, rule_repo: WarningRuleRepository):
        self.rule_repo = rule_repo

    def execute(
        self, rule_id: str, rule_data: WarningRuleUpdateDTO
    ) -> WarningRuleResponseDTO:
        rule = self.rule_repo.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"Warning rule {rule_id} not found")

        if rule_data.rule_type is not None:
            rule.rule_type = rule_data.rule_type
        if rule_data.min_year is not None:
            rule.min_year = rule_data.min_year
        if rule_data.max_year is not None:
            rule.max_year = rule_data.max_year
        if rule_data.threshold is not None:
            rule.threshold = rule_data.threshold
        if rule_data.comparison_operator is not None:
            rule.comparison_operator = rule_data.comparison_operator

        updated = self.rule_repo.update(rule)
        logger.info(
            "Warning rule updated: %s rule_type=%s threshold=%s %s",
            updated.id,
            updated.rule_type,
            updated.threshold,
            updated.comparison_operator,
        )

        return WarningRuleResponseDTO(
            id=updated.id,
            rule_set_id=updated.rule_set_id,
            rule_type=updated.rule_type,
            min_year=updated.min_year,
            max_year=updated.max_year,
            threshold=updated.threshold,
            comparison_operator=updated.comparison_operator,
            created_at=datetime.now().isoformat(),
        )


class DeleteWarningRuleUseCase:
    def __init__(self, rule_repo: WarningRuleRepository):
        self.rule_repo = rule_repo

    def execute(self, rule_id: str) -> bool:
        return self.rule_repo.delete(rule_id)
