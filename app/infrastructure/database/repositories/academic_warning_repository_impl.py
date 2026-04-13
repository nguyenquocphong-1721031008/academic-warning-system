from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.entities.academic_warning import AcademicWarning
from app.domain.entities.academic_warning_draft import AcademicWarningDraft
from app.domain.repositories.academic_warning_repository import (
    AcademicWarningRepository,
)
from app.infrastructure.database.student_code_norm import normalize_student_code


class AcademicWarningRepositoryImpl(AcademicWarningRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_faculty(self, faculty_id: Optional[str]) -> List[Dict]:
        if faculty_id is None:
            results = self.db.execute(
                text("""
                    SELECT 
                        s.student_code,
                        s.last_name || ' ' || s.first_name AS full_name,
                        c.class_code,
                        sem.semester_name,
                        sem.academic_year,
                        aw.warning_level,
                        COALESCE(aw.total_subjects, 0),
                        COALESCE(aw.total_failed, 0),
                        COALESCE(aw.fail_ratio, 0),
                        COALESCE(aw.semester_gpa, 0),
                        COALESCE(aw.cumulative_gpa, 0),
                        aw.warning_reason,
                        COALESCE(aw.created_at, now()) as created_at
                    FROM academic_warnings aw
                    JOIN students s ON aw.student_id = s.id
                    JOIN classes c ON s.class_id = c.id
                    JOIN semesters sem ON aw.semester_id = sem.id
                    ORDER BY aw.created_at DESC
                """)
            ).fetchall()
        else:
            results = self.db.execute(
                text("""
                    SELECT 
                        s.student_code,
                        s.last_name || ' ' || s.first_name AS full_name,
                        c.class_code,
                        sem.semester_name,
                        sem.academic_year,
                        aw.warning_level,
                        COALESCE(aw.total_subjects, 0),
                        COALESCE(aw.total_failed, 0),
                        COALESCE(aw.fail_ratio, 0),
                        COALESCE(aw.semester_gpa, 0),
                        COALESCE(aw.cumulative_gpa, 0),
                        aw.warning_reason,
                        COALESCE(aw.created_at, now()) as created_at
                    FROM academic_warnings aw
                    JOIN students s ON aw.student_id = s.id
                    JOIN classes c ON s.class_id = c.id
                    JOIN majors m ON c.major_id = m.id
                    JOIN semesters sem ON aw.semester_id = sem.id
                    WHERE m.faculty_id = :faculty_id
                    ORDER BY aw.created_at DESC
                """),
                {"faculty_id": faculty_id},
            ).fetchall()

        return [self._map_faculty_warning(row) for row in results]

    def get_by_student_id(self, student_id: str) -> List[AcademicWarning]:
        results = self.db.execute(
            text("""
                SELECT 
                    aw.id, aw.student_id, aw.semester_id,
                    sem.semester_name, sem.academic_year,
                    aw.warning_level,
                    COALESCE(aw.total_subjects, 0),
                    COALESCE(aw.total_failed, 0),
                    COALESCE(aw.fail_ratio, 0),
                    COALESCE(aw.semester_gpa, 0),
                    COALESCE(aw.cumulative_gpa, 0),
                    aw.warning_reason,
                    COALESCE(aw.warning_status, 'open') AS warning_status,
                    aw.warning_note,
                    aw.rule_set_id,
                    aw.created_at
                FROM academic_warnings aw
                JOIN semesters sem ON aw.semester_id = sem.id
                WHERE aw.student_id = :student_id
                ORDER BY aw.created_at DESC
            """),
            {"student_id": student_id},
        ).fetchall()

        return [self._map(row) for row in results]

    def get_by_student_code(self, student_code: str) -> List[AcademicWarning]:
        code = normalize_student_code(student_code)
        results = self.db.execute(
            text("""
                SELECT 
                    aw.id, aw.student_id, aw.semester_id,
                    sem.semester_name, sem.academic_year,
                    aw.warning_level,
                    COALESCE(aw.total_subjects, 0),
                    COALESCE(aw.total_failed, 0),
                    COALESCE(aw.fail_ratio, 0),
                    COALESCE(aw.semester_gpa, 0),
                    COALESCE(aw.cumulative_gpa, 0),
                    aw.warning_reason,
                    COALESCE(aw.warning_status, 'open') AS warning_status,
                    aw.warning_note,
                    aw.rule_set_id,
                    aw.created_at
                FROM academic_warnings aw
                JOIN semesters sem ON aw.semester_id = sem.id
                JOIN students s ON aw.student_id = s.id
                WHERE LOWER(BTRIM(s.student_code::text)) = LOWER(:student_code)
                ORDER BY aw.created_at DESC
            """),
            {"student_code": code},
        ).fetchall()

        return [self._map(row) for row in results]

    def get_latest_by_student_code(
        self,
        student_code: str,
    ) -> Optional[AcademicWarning]:
        code = normalize_student_code(student_code)
        result = self.db.execute(
            text("""
                SELECT
                    aw.id, aw.student_id, aw.semester_id,
                    sem.semester_name, sem.academic_year,
                    aw.warning_level,
                    COALESCE(aw.total_subjects, 0),
                    COALESCE(aw.total_failed, 0),
                    COALESCE(aw.fail_ratio, 0),
                    COALESCE(aw.semester_gpa, 0),
                    COALESCE(aw.cumulative_gpa, 0),
                    aw.warning_reason,
                    COALESCE(aw.warning_status, 'open') AS warning_status,
                    aw.warning_note,
                    aw.rule_set_id,
                    aw.created_at
                FROM academic_warnings aw
                JOIN semesters sem ON aw.semester_id = sem.id
                JOIN students s ON aw.student_id = s.id
                WHERE LOWER(BTRIM(s.student_code::text)) = LOWER(:student_code)
                ORDER BY aw.created_at DESC
                LIMIT 1
            """),
            {"student_code": code},
        ).fetchone()

        if not result:
            return None

        return self._map(result)

    def get_latest_by_student_id(self, student_id: str) -> Optional[AcademicWarning]:
        result = self.db.execute(
            text("""
                SELECT 
                    aw.id, aw.student_id, aw.semester_id,
                    sem.semester_name, sem.academic_year,
                    aw.warning_level,
                    COALESCE(aw.total_subjects, 0),
                    COALESCE(aw.total_failed, 0),
                    COALESCE(aw.fail_ratio, 0),
                    COALESCE(aw.semester_gpa, 0),
                    COALESCE(aw.cumulative_gpa, 0),
                    aw.warning_reason,
                    COALESCE(aw.warning_status, 'open') AS warning_status,
                    aw.warning_note,
                    aw.rule_set_id,
                    aw.created_at
                FROM academic_warnings aw
                JOIN semesters sem ON aw.semester_id = sem.id
                WHERE aw.student_id = :student_id
                ORDER BY aw.created_at DESC
                LIMIT 1
            """),
            {"student_id": student_id},
        ).fetchone()

        if not result:
            return None

        return self._map(result)

    def clear_all(self) -> None:
        self.db.execute(text("DELETE FROM academic_warnings"))
        self.db.commit()

    def update_warning_status(
        self, warning_id: str, warning_status: str, warning_note: str | None
    ) -> bool:
        result = self.db.execute(
            text("""
                UPDATE academic_warnings
                SET warning_status = :warning_status,
                    warning_note = :warning_note
                WHERE id = :warning_id
            """),
            {
                "warning_id": warning_id,
                "warning_status": warning_status,
                "warning_note": warning_note,
            },
        )
        self.db.commit()
        return result.rowcount > 0

    def list_filtered(
        self,
        faculty_id: str | None,
        class_id: str | None,
        semester_id: str | None,
        page: int,
        size: int,
    ) -> list[dict]:
        where_clauses = []
        params = {}

        if faculty_id:
            where_clauses.append("m.faculty_id = :faculty_id")
            params["faculty_id"] = faculty_id
        if class_id:
            where_clauses.append("c.id = :class_id")
            params["class_id"] = class_id
        if semester_id:
            where_clauses.append("aw.semester_id = :semester_id")
            params["semester_id"] = semester_id

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        offset = (page - 1) * size if page > 0 else 0
        params["size"] = size
        params["offset"] = offset

        results = self.db.execute(
            text(f"""
                SELECT
                    aw.id,
                    aw.student_id,
                    aw.semester_id,
                    sem.semester_name,
                    sem.academic_year,
                    aw.warning_level,
                    COALESCE(aw.total_subjects, 0),
                    COALESCE(aw.total_failed, 0),
                    COALESCE(aw.fail_ratio, 0),
                    COALESCE(aw.semester_gpa, 0),
                    COALESCE(aw.cumulative_gpa, 0),
                    aw.warning_reason,
                    COALESCE(aw.warning_status, 'open') AS warning_status,
                    aw.warning_note,
                    aw.rule_set_id,
                    aw.created_at,
                    s.student_code,
                    s.last_name || ' ' || s.first_name AS full_name,
                    c.class_code,
                    m.faculty_id
                FROM academic_warnings aw
                JOIN students s ON aw.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                JOIN majors m ON c.major_id = m.id
                JOIN semesters sem ON aw.semester_id = sem.id
                {where_sql}
                ORDER BY aw.created_at DESC
                LIMIT :size OFFSET :offset
            """),
            params,
        ).fetchall()

        return [
            {
                "id": str(row[0]),
                "student_id": str(row[1]),
                "semester_id": str(row[2]),
                "semester_name": str(row[3]),
                "academic_year": str(row[4]),
                "warning_level": str(row[5]),
                "total_subjects": int(row[6]),
                "total_failed": int(row[7]),
                "fail_ratio": float(row[8]),
                "semester_gpa": float(row[9]) if row[9] is not None else None,
                "cumulative_gpa": float(row[10]) if row[10] is not None else None,
                "warning_reason": str(row[11]) if row[11] else None,
                "warning_status": str(row[12]) if row[12] else "open",
                "warning_note": str(row[13]) if row[13] else None,
                "rule_set_id": str(row[14]) if row[14] else None,
                "created_at": row[15].isoformat() if row[15] else None,
                "student_code": str(row[16]),
                "full_name": str(row[17]),
                "class_code": str(row[18]) if row[18] else None,
                "faculty_id": str(row[19]) if row[19] else None,
            }
            for row in results
        ]

    def count_filtered(
        self,
        faculty_id: str | None,
        class_id: str | None,
        semester_id: str | None,
    ) -> int:
        where_clauses = []
        params = {}
        if faculty_id:
            where_clauses.append("m.faculty_id = :faculty_id")
            params["faculty_id"] = faculty_id
        if class_id:
            where_clauses.append("c.id = :class_id")
            params["class_id"] = class_id
        if semester_id:
            where_clauses.append("aw.semester_id = :semester_id")
            params["semester_id"] = semester_id

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        result = self.db.execute(
            text(f"""
                SELECT COUNT(*)
                FROM academic_warnings aw
                JOIN students s ON aw.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                JOIN majors m ON c.major_id = m.id
                {where_sql}
            """),
            params,
        ).scalar()

        return int(result or 0)

    def analytics_summary(self, faculty_id: str | None = None) -> dict:
        semester_where = "WHERE aw.warning_level = 'warning'"
        faculty_where = "WHERE aw.warning_level = 'warning'"
        class_where = "WHERE aw.warning_level = 'warning'"
        params: dict[str, str] = {}
        if faculty_id:
            semester_where += " AND m.faculty_id = :faculty_id"
            faculty_where += " AND f.id = :faculty_id"
            class_where += " AND m.faculty_id = :faculty_id"
            params["faculty_id"] = faculty_id

        semester = [
            {
                "semester_id": str(row[0]),
                "semester_name": str(row[1]),
                "academic_year": str(row[2]),
                "warnings": int(row[3]),
            }
            for row in self.db.execute(
                text(f"""
                SELECT sem.id, sem.semester_name, sem.academic_year, COUNT(*)
                FROM academic_warnings aw
                JOIN semesters sem ON aw.semester_id = sem.id
                JOIN students s ON aw.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                JOIN majors m ON c.major_id = m.id
                {semester_where}
                GROUP BY sem.id, sem.semester_name, sem.academic_year
                ORDER BY sem.academic_year, sem.semester_name
            """),
                params,
            ).fetchall()
        ]

        faculty = [
            {
                "faculty_id": str(row[0]),
                "faculty_name": str(row[1]),
                "warnings": int(row[2]),
            }
            for row in self.db.execute(
                text(f"""
                SELECT f.id, f.name, COUNT(*)
                FROM academic_warnings aw
                JOIN students s ON aw.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                JOIN majors m ON c.major_id = m.id
                JOIN faculties f ON m.faculty_id = f.id
                {faculty_where}
                GROUP BY f.id, f.name
                ORDER BY f.name
            """),
                params,
            ).fetchall()
        ]

        class_ = [
            {
                "class_id": str(row[0]),
                "class_code": str(row[1]),
                "warnings": int(row[2]),
            }
            for row in self.db.execute(
                text(f"""
                SELECT c.id, c.class_code, COUNT(*)
                FROM academic_warnings aw
                JOIN students s ON aw.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                JOIN majors m ON c.major_id = m.id
                {class_where}
                GROUP BY c.id, c.class_code
                ORDER BY c.class_code
            """),
                params,
            ).fetchall()
        ]

        return {"by_semester": semester, "by_faculty": faculty, "by_class": class_}

    def bulk_insert(self, drafts: List[AcademicWarningDraft]) -> None:
        if not drafts:
            return
        stmt = text("""
            INSERT INTO academic_warnings (
                student_id, semester_id,
                total_subjects, total_failed, fail_ratio,
                semester_gpa, cumulative_gpa,
                warning_level, warning_reason, rule_set_id, created_at
            )
            VALUES (
                :student_id, :semester_id,
                :total_subjects, :total_failed, :fail_ratio,
                :semester_gpa, :cumulative_gpa,
                :warning_level, :warning_reason, :rule_set_id, NOW()
            )
        """)
        for d in drafts:
            self.db.execute(
                stmt,
                {
                    "student_id": d.student_id,
                    "semester_id": d.semester_id,
                    "total_subjects": d.total_subjects,
                    "total_failed": d.total_failed,
                    "fail_ratio": float(d.fail_ratio),
                    "semester_gpa": float(d.semester_gpa)
                    if d.semester_gpa is not None
                    else None,
                    "cumulative_gpa": float(d.cumulative_gpa)
                    if d.cumulative_gpa is not None
                    else None,
                    "warning_level": d.warning_level,
                    "warning_reason": d.warning_reason,
                    "rule_set_id": d.rule_set_id,
                },
            )
        self.db.commit()

    def _map(self, row) -> AcademicWarning:
        return AcademicWarning(
            id=str(row[0]),
            student_id=str(row[1]),
            semester_id=str(row[2]),
            semester_name=str(row[3]),
            academic_year=str(row[4]),
            warning_level=str(row[5]),
            total_subjects=int(row[6]),
            total_failed=int(row[7]),
            fail_ratio=row[8],
            semester_gpa=row[9],
            cumulative_gpa=row[10],
            warning_reason=str(row[11]) if row[11] else None,
            warning_status=str(row[12]) if row[12] else "open",
            warning_note=str(row[13]) if row[13] else None,
            rule_set_id=str(row[14]) if row[14] else None,
            created_at=row[15],
        )

    def _map_faculty_warning(self, row) -> Dict:
        total_failed = int(row[7])
        fail_ratio = float(row[8])
        semester_gpa = float(row[9])
        cumulative_gpa = float(row[10])
        db_reason = row[11]

        if db_reason:
            reason = str(db_reason)
        else:
            reason = self._generate_warning_reason(
                total_failed, fail_ratio, semester_gpa, cumulative_gpa
            )

        return {
            "student_code": str(row[0]),
            "full_name": str(row[1]),
            "class_code": str(row[2]),
            "semester_name": str(row[3]),
            "academic_year": str(row[4]),
            "warning_level": str(row[5]),
            "total_subjects": int(row[6]),
            "total_failed": total_failed,
            "fail_ratio": fail_ratio,
            "semester_gpa": semester_gpa,
            "cumulative_gpa": cumulative_gpa,
            "warning_reason": reason,
            "created_at": str(row[12]) if row[12] is not None else "",
        }

    def _generate_warning_reason(
        self,
        total_failed: int,
        fail_ratio: float,
        semester_gpa: float,
        cumulative_gpa: float,
    ) -> str:
        parts = []

        if total_failed >= 5:
            parts.append(f"Rớt {total_failed} môn quá nhiều")
        elif total_failed >= 3:
            parts.append(f"Rớt {total_failed} môn")

        if fail_ratio >= 0.75:
            parts.append("Tỷ lệ rớt môn quá cao")
        elif fail_ratio >= 0.5:
            parts.append("Tỷ lệ rớt môn cao")

        if semester_gpa < 1.0 and semester_gpa > 0:
            parts.append("GPA học kỳ rất kém")
        elif semester_gpa < 2.0 and semester_gpa > 0:
            parts.append("GPA học kỳ thấp")

        if cumulative_gpa < 1.5 and cumulative_gpa > 0:
            parts.append("GPA tích lũy rất thấp")

        if not parts:
            parts.append("Không đạt tiêu chuẩn học tập")

        return " - ".join(parts)
