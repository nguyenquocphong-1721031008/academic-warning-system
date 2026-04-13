from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime
from app.domain.repositories.warning_rule_set_repository import WarningRuleSetRepository
from app.domain.entities.warning_rule_set import WarningRuleSet


class WarningRuleSetRepositoryImpl(WarningRuleSetRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, rule_set_id: str) -> Optional[WarningRuleSet]:
        result = self.db.execute(
            text("""
                SELECT id, name, description, effective_from, effective_to, is_active, created_at
                FROM warning_rule_sets
                WHERE id = :id
            """),
            {"id": rule_set_id},
        ).fetchone()

        if not result:
            return None

        return WarningRuleSet(
            id=str(result[0]),
            name=str(result[1]),
            description=str(result[2]) if result[2] else None,
            effective_from=result[3]
            if isinstance(result[3], date)
            else date.fromisoformat(str(result[3])),
            effective_to=result[4]
            if result[4] and isinstance(result[4], date)
            else (date.fromisoformat(str(result[4])) if result[4] else None),
            is_active=bool(result[5])
            if isinstance(result[5], bool)
            else (str(result[5]).lower() == "true"),
            created_at=result[6] if result[6] else datetime.now(),
        )

    def get_all(self) -> List[WarningRuleSet]:
        results = self.db.execute(
            text("""
                SELECT id, name, description, effective_from, effective_to, is_active, created_at
                FROM warning_rule_sets
                ORDER BY created_at DESC
            """)
        ).fetchall()

        rule_sets = []
        for row in results:
            rule_sets.append(
                WarningRuleSet(
                    id=str(row[0]),
                    name=str(row[1]),
                    description=str(row[2]) if row[2] else None,
                    effective_from=row[3]
                    if isinstance(row[3], date)
                    else date.fromisoformat(str(row[3])),
                    effective_to=row[4]
                    if row[4] and isinstance(row[4], date)
                    else (date.fromisoformat(str(row[4])) if row[4] else None),
                    is_active=bool(row[5])
                    if isinstance(row[5], bool)
                    else (str(row[5]).lower() == "true"),
                    created_at=row[6] if row[6] else datetime.now(),
                )
            )
        return rule_sets

    def get_active(self) -> List[WarningRuleSet]:
        results = self.db.execute(
            text("""
                SELECT id, name, description, effective_from, effective_to, is_active, created_at
                FROM warning_rule_sets
                WHERE is_active = true
                ORDER BY created_at DESC
            """)
        ).fetchall()

        rule_sets = []
        for row in results:
            rule_sets.append(
                WarningRuleSet(
                    id=str(row[0]),
                    name=str(row[1]),
                    description=str(row[2]) if row[2] else None,
                    effective_from=row[3]
                    if isinstance(row[3], date)
                    else date.fromisoformat(str(row[3])),
                    effective_to=row[4]
                    if row[4] and isinstance(row[4], date)
                    else (date.fromisoformat(str(row[4])) if row[4] else None),
                    is_active=True,
                    created_at=row[6] if row[6] else datetime.now(),
                )
            )
        return rule_sets

    def create(self, rule_set: WarningRuleSet) -> WarningRuleSet:
        rule_set_id = self.db.execute(
            text("""
                INSERT INTO warning_rule_sets (id, name, description, effective_from, effective_to, is_active, created_at)
                VALUES (:id, :name, :description, :effective_from, :effective_to, :is_active, :created_at)
                RETURNING id
            """),
            {
                "id": rule_set.id,
                "name": rule_set.name,
                "description": rule_set.description,
                "effective_from": rule_set.effective_from,
                "effective_to": rule_set.effective_to,
                "is_active": rule_set.is_active,
                "created_at": rule_set.created_at,
            },
        ).scalar()

        self.db.commit()
        return self.get_by_id(rule_set_id)

    def update(self, rule_set: WarningRuleSet) -> WarningRuleSet:
        self.db.execute(
            text("""
                UPDATE warning_rule_sets
                SET name = :name, description = :description, 
                    effective_from = :effective_from, effective_to = :effective_to,
                    is_active = :is_active
                WHERE id = :id
            """),
            {
                "id": rule_set.id,
                "name": rule_set.name,
                "description": rule_set.description,
                "effective_from": rule_set.effective_from,
                "effective_to": rule_set.effective_to,
                "is_active": rule_set.is_active,
            },
        )
        self.db.commit()
        return self.get_by_id(rule_set.id)

    def delete(self, rule_set_id: str) -> bool:
        result = self.db.execute(
            text("DELETE FROM warning_rule_sets WHERE id = :id"), {"id": rule_set_id}
        )
        self.db.commit()
        return result.rowcount > 0

    def toggle_active(self, rule_set_id: str, is_active: bool) -> bool:
        result = self.db.execute(
            text("""
                UPDATE warning_rule_sets
                SET is_active = :is_active
                WHERE id = :id
            """),
            {"id": rule_set_id, "is_active": is_active},
        )
        self.db.commit()
        return result.rowcount > 0
