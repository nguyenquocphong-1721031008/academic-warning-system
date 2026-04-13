from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, Enum as SQLEnum
from app.infrastructure.database.base import Base
import uuid


class WarningRuleSetModel(Base):
    __tablename__ = "warning_rule_sets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    effective_from = Column(String, nullable=False)
    effective_to = Column(String, nullable=True)
    is_active = Column(String, default="true")
    created_at = Column(String, nullable=True)


class WarningRuleModel(Base):
    __tablename__ = "warning_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_set_id = Column(
        String, ForeignKey("warning_rule_sets.id", ondelete="CASCADE"), nullable=False
    )
    rule_type = Column(
        SQLEnum("fail_ratio", "semester_gpa", "cumulative_gpa", name="rule_type_enum"),
        nullable=False,
    )
    min_year = Column(Integer, default=1)
    max_year = Column(Integer, default=10)
    threshold = Column(Numeric(4, 2), nullable=False)
    comparison_operator = Column(
        SQLEnum("<", "<=", ">", ">=", "=", name="comparison_operator_enum"), default="<"
    )
    created_at = Column(String, nullable=True)
