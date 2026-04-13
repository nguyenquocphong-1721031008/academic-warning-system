from __future__ import annotations

import os
from datetime import date, datetime, timezone

from sqlalchemy import create_engine, text

from app.infrastructure.config.settings import get_settings
from app.infrastructure.security.auth import get_password_hash


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)

    admin_username = os.getenv("SEED_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "admin123456")

    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM users WHERE username = :u LIMIT 1"),
            {"u": admin_username},
        ).scalar()
        if not exists:
            conn.execute(
                text(
                    """
                    INSERT INTO users (id, username, password_hash, role, faculty_id, created_at)
                    VALUES (gen_random_uuid(), :u, :p, 'admin', NULL, NOW())
                    """
                ),
                {"u": admin_username, "p": get_password_hash(admin_password)},
            )

        rs_exists = conn.execute(
            text("SELECT id FROM warning_rule_sets WHERE is_active = TRUE LIMIT 1")
        ).scalar()
        if not rs_exists:
            rs_id = conn.execute(
                text(
                    """
                    INSERT INTO warning_rule_sets
                        (id, name, description, effective_from, effective_to, is_active, created_at)
                    VALUES
                        (gen_random_uuid(), :n, :d, :from, NULL, TRUE, NOW())
                    RETURNING id
                    """
                ),
                {
                    "n": "Default rules",
                    "d": "Rule set mặc định cho cảnh báo học vụ",
                    "from": date.today().isoformat(),
                },
            ).scalar()

            rules = [
                ("fail_ratio", 1, 10, 0.50, ">="),
                ("semester_gpa", 1, 1, 0.80, "<"),
                ("semester_gpa", 2, 10, 1.00, "<"),
                ("cumulative_gpa", 1, 1, 1.20, "<"),
                ("cumulative_gpa", 2, 2, 1.40, "<"),
                ("cumulative_gpa", 3, 3, 1.60, "<"),
                ("cumulative_gpa", 4, 10, 1.80, "<"),
            ]
            for rule_type, min_year, max_year, threshold, op_ in rules:
                conn.execute(
                    text(
                        """
                        INSERT INTO warning_rules
                            (id, rule_set_id, rule_type, min_year, max_year, threshold, comparison_operator, created_at)
                        VALUES
                            (gen_random_uuid(), :rs, :rt, :miny, :maxy, :thr, :op, :created)
                        """
                    ),
                    {
                        "rs": rs_id,
                        "rt": rule_type,
                        "miny": min_year,
                        "maxy": max_year,
                        "thr": threshold,
                        "op": op_,
                        "created": datetime.now(timezone.utc).isoformat(),
                    },
                )

    print("Seed completed.")
    print(f"Admin user: {admin_username}")


if __name__ == "__main__":
    main()

