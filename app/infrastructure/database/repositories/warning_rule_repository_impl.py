from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal
from datetime import date, datetime
from app.domain.repositories.warning_rule_repository import WarningRuleRepository
from app.domain.entities.warning_rule import WarningRule


class WarningRuleRepositoryImpl(WarningRuleRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[WarningRule]:
        results = self.db.execute(
            text("""
                SELECT id, rule_set_id, rule_type, min_year, max_year,
                       threshold, comparison_operator, created_at
                FROM warning_rules
                ORDER BY rule_type
            """)
        ).fetchall()

        return [
            WarningRule(
                id=str(row[0]),
                rule_set_id=str(row[1]),
                rule_type=str(row[2]),
                min_year=int(row[3]) if row[3] else 1,
                max_year=int(row[4]) if row[4] else 10,
                threshold=Decimal(str(row[5])),
                comparison_operator=str(row[6]) if row[6] else "<",
                created_at=row[7] if isinstance(row[7], datetime) else None,
            )
            for row in results
        ]

    def get_active_rules(self) -> List[WarningRule]:
        today = date.today()
        results = self.db.execute(
            text("""
                SELECT r.id, r.rule_set_id, r.rule_type, r.min_year, r.max_year,
                       r.threshold, r.comparison_operator, r.created_at
                FROM warning_rules r
                JOIN warning_rule_sets s ON r.rule_set_id = s.id
                WHERE s.is_active = true
                  AND s.effective_from <= :today
                  AND (s.effective_to IS NULL OR s.effective_to >= :today)
            """),
            {"today": today},
        ).fetchall()

        return [
            WarningRule(
                id=str(row[0]),
                rule_set_id=str(row[1]),
                rule_type=str(row[2]),
                min_year=int(row[3]) if row[3] else 1,
                max_year=int(row[4]) if row[4] else 10,
                threshold=Decimal(str(row[5])),
                comparison_operator=str(row[6]) if row[6] else "<",
                created_at=row[7] if isinstance(row[7], datetime) else None,
            )
            for row in results
        ]

    def get_by_id(self, rule_id: str) -> Optional[WarningRule]:
        result = self.db.execute(
            text("""
                SELECT id, rule_set_id, rule_type, min_year, max_year,
                       threshold, comparison_operator, created_at
                FROM warning_rules
                WHERE id = :id
            """),
            {"id": rule_id},
        ).fetchone()

        if not result:
            return None

        return WarningRule(
            id=str(result[0]),
            rule_set_id=str(result[1]),
            rule_type=str(result[2]),
            min_year=int(result[3]) if result[3] else 1,
            max_year=int(result[4]) if result[4] else 10,
            threshold=Decimal(str(result[5])),
            comparison_operator=str(result[6]) if result[6] else "<",
            created_at=result[7] if isinstance(result[7], datetime) else None,
        )

    def get_by_rule_set_id(self, rule_set_id: str) -> List[WarningRule]:
        results = self.db.execute(
            text("""
                SELECT id, rule_set_id, rule_type, min_year, max_year,
                       threshold, comparison_operator, created_at
                FROM warning_rules
                WHERE rule_set_id = :rule_set_id
            """),
            {"rule_set_id": rule_set_id},
        ).fetchall()

        return [
            WarningRule(
                id=str(row[0]),
                rule_set_id=str(row[1]),
                rule_type=str(row[2]),
                min_year=int(row[3]) if row[3] else 1,
                max_year=int(row[4]) if row[4] else 10,
                threshold=Decimal(str(row[5])),
                comparison_operator=str(row[6]) if row[6] else "<",
                created_at=row[7] if isinstance(row[7], datetime) else None,
            )
            for row in results
        ]

    def create(self, rule: WarningRule) -> WarningRule:
        rule_id = self.db.execute(
            text("""
                INSERT INTO warning_rules (
                    id, rule_set_id, rule_type, min_year, max_year,
                    threshold, comparison_operator, created_at
                )
                VALUES (
                    :id, :rule_set_id, :rule_type, :min_year, :max_year,
                    :threshold, :comparison_operator, NOW()
                )
                RETURNING id
            """),
            {
                "id": rule.id,
                "rule_set_id": rule.rule_set_id,
                "rule_type": rule.rule_type,
                "min_year": rule.min_year,
                "max_year": rule.max_year,
                "threshold": rule.threshold,
                "comparison_operator": rule.comparison_operator,
            },
        ).scalar()

        self.db.commit()
        return self.get_by_id(rule_id)

    def update(self, rule: WarningRule) -> WarningRule:
        self.db.execute(
            text("""
                UPDATE warning_rules
                SET rule_type = :rule_type,
                    min_year = :min_year,
                    max_year = :max_year,
                    threshold = :threshold,
                    comparison_operator = :comparison_operator
                WHERE id = :id
            """),
            {
                "id": rule.id,
                "rule_type": rule.rule_type,
                "min_year": rule.min_year,
                "max_year": rule.max_year,
                "threshold": rule.threshold,
                "comparison_operator": rule.comparison_operator,
            },
        )

        self.db.commit()
        return self.get_by_id(rule.id)

    def delete(self, rule_id: str) -> bool:
        result = self.db.execute(
            text("DELETE FROM warning_rules WHERE id = :id"), {"id": rule_id}
        )

        self.db.commit()
        return result.rowcount > 0
