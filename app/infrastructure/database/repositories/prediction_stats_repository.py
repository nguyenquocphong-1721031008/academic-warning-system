from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.prediction_stats_reader import (
    WarningRiskPredictionSnapshot,
    PredictionStatsReader,
)
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.student_code_norm import normalize_student_code


def _to_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


class SqlAlchemyPredictionStatsRepository(PredictionStatsReader):
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or SessionLocal

    def load_warning_risk_snapshot(
        self, student_code: str
    ) -> WarningRiskPredictionSnapshot | None:
        code = normalize_student_code(student_code)
        db = self._session_factory()
        try:
            row = (
                db.execute(
                    text("""
                    SELECT
                        s.student_code,
                        s.enrollment_year,
                        s.id AS student_id,
                        st.semester_id,
                        st.semester_gpa,
                        st.cumulative_gpa,
                        st.total_failed,
                        st.total_subjects,
                        st.academic_year,
                        st.start_date,
                        aw.warning_level
                    FROM students s
                    LEFT JOIN LATERAL (
                        SELECT
                            sss_i.semester_id,
                            sss_i.semester_gpa,
                            sss_i.cumulative_gpa,
                            sss_i.total_failed,
                            sss_i.total_subjects,
                            sem_i.academic_year,
                            sem_i.start_date
                        FROM student_semester_stats sss_i
                        INNER JOIN semesters sem_i ON sem_i.id = sss_i.semester_id
                        WHERE sss_i.student_id = s.id
                        ORDER BY sem_i.start_date DESC NULLS LAST
                        LIMIT 1
                    ) st ON true
                    LEFT JOIN academic_warnings aw
                        ON aw.student_id = s.id
                        AND aw.semester_id = st.semester_id
                    WHERE LOWER(BTRIM(s.student_code::text)) = LOWER(:student_code)
                """),
                    {"student_code": code},
                )
                .mappings()
                .first()
            )

            if not row:
                return None

            has_stats = row["semester_id"] is not None

            prev_sg: float | None = None
            prev_tf: int | None = None
            if has_stats and row["start_date"] is not None:
                start = _to_date(row["start_date"])
                prev = (
                    db.execute(
                        text("""
                        SELECT
                            sss.semester_gpa,
                            sss.total_failed
                        FROM student_semester_stats sss
                        JOIN semesters sem ON sem.id = sss.semester_id
                        WHERE sss.student_id = :student_id
                          AND sem.start_date < :current_start_date
                        ORDER BY sem.start_date DESC
                        LIMIT 1
                    """),
                        {"student_id": row["student_id"], "current_start_date": start},
                    )
                    .mappings()
                    .first()
                )

                if prev:
                    if prev["semester_gpa"] is not None:
                        prev_sg = float(prev["semester_gpa"])
                    if prev["total_failed"] is not None:
                        prev_tf = int(prev["total_failed"])

            return WarningRiskPredictionSnapshot(
                student_code=str(row["student_code"]),
                enrollment_year=int(row["enrollment_year"] or 0),
                semester_academic_year=row.get("academic_year"),
                student_id=str(row["student_id"]),
                has_semester_stats=has_stats,
                semester_gpa=float(row["semester_gpa"])
                if row["semester_gpa"] is not None
                else None,
                cumulative_gpa=float(row["cumulative_gpa"])
                if row["cumulative_gpa"] is not None
                else None,
                total_failed=int(row["total_failed"])
                if row["total_failed"] is not None
                else None,
                total_subjects=int(row["total_subjects"])
                if row["total_subjects"] is not None
                else None,
                warning_level=str(row["warning_level"])
                if row.get("warning_level")
                else None,
                prev_semester_gpa=prev_sg,
                prev_total_failed=prev_tf,
            )
        finally:
            db.close()
