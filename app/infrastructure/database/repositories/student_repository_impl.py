from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.repositories.student_repository import StudentRepository
from app.domain.entities.student import Student
from app.infrastructure.database.student_code_norm import normalize_student_code


class StudentRepositoryImpl(StudentRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, student_code: str) -> Optional[Student]:
        code = normalize_student_code(student_code)
        if not code:
            return None
        result = self.db.execute(
            text("""
                SELECT 
                    s.id, 
                    s.student_code, 
                    s.last_name, 
                    s.first_name, 
                    s.gender, 
                    s.date_of_birth, 
                    s.class_id, 
                    s.status, 
                    s.enrollment_year,
                    c.class_code
                FROM students s
                LEFT JOIN classes c ON s.class_id = c.id
                WHERE LOWER(BTRIM(s.student_code::text)) = LOWER(:code)
            """),
            {"code": code},
        ).fetchone()

        if not result:
            return None

        return Student(
            id=str(result[0]),
            student_code=str(result[1]),
            last_name=str(result[2]),
            first_name=str(result[3]),
            gender=str(result[4]),
            date_of_birth=result[5],
            class_id=str(result[6]) if result[6] else None,
            status=str(result[7]) if result[7] else "studying",
            enrollment_year=int(result[8]) if result[8] else None,
            class_code=str(result[9]) if result[9] else None,
        )

    def get_by_id(self, student_id: str) -> Optional[Student]:
        result = self.db.execute(
            text("""
                SELECT 
                    s.id, 
                    s.student_code, 
                    s.last_name, 
                    s.first_name, 
                    s.gender, 
                    s.date_of_birth, 
                    s.class_id, 
                    s.status, 
                    s.enrollment_year,
                    c.class_code
                FROM students s
                LEFT JOIN classes c ON s.class_id = c.id
                WHERE s.id = :id
            """),
            {"id": student_id},
        ).fetchone()

        if not result:
            return None

        return Student(
            id=str(result[0]),
            student_code=str(result[1]),
            last_name=str(result[2]),
            first_name=str(result[3]),
            gender=str(result[4]),
            date_of_birth=result[5],
            class_id=str(result[6]) if result[6] else None,
            status=str(result[7]) if result[7] else "studying",
            enrollment_year=int(result[8]) if result[8] else None,
            class_code=str(result[9]) if result[9] else None,
        )

    def get_by_faculty(
        self,
        faculty_id: Optional[str],
        skip: int,
        limit: int,
        enrollment_year: Optional[int] = None,
        semester_id: Optional[str] = None,
    ) -> List[Student]:
        where_clauses = []
        params = {"limit": limit, "skip": skip}

        if faculty_id is not None:
            where_clauses.append("m.faculty_id = :faculty_id")
            params["faculty_id"] = faculty_id
        if enrollment_year is not None:
            where_clauses.append("s.enrollment_year = :enrollment_year")
            params["enrollment_year"] = enrollment_year
        if semester_id is not None:
            where_clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM student_scores sc
                    JOIN course_sections cs ON cs.id = sc.section_id
                    WHERE sc.student_id = s.id
                      AND cs.semester_id = :semester_id
                )
                """
            )
            params["semester_id"] = semester_id

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        results = self.db.execute(
            text(f"""
                SELECT
                    s.id,
                    s.student_code,
                    s.last_name,
                    s.first_name,
                    s.gender,
                    s.date_of_birth,
                    s.class_id,
                    s.status,
                    s.enrollment_year,
                    c.class_code
                FROM students s
                JOIN classes c ON s.class_id = c.id
                JOIN majors m ON c.major_id = m.id
                {where_sql}
                ORDER BY s.student_code
                LIMIT :limit OFFSET :skip
            """),
            params,
        ).fetchall()

        return [
            Student(
                id=str(row[0]),
                student_code=str(row[1]),
                last_name=str(row[2]),
                first_name=str(row[3]),
                gender=str(row[4]),
                date_of_birth=row[5],
                class_id=str(row[6]) if row[6] else None,
                status=str(row[7]) if row[7] else "studying",
                enrollment_year=int(row[8]) if row[8] else None,
                class_code=str(row[9]) if row[9] else None,
            )
            for row in results
        ]

    def list_enrollment_years(self, faculty_id: Optional[str] = None) -> List[int]:
        if faculty_id is None:
            results = self.db.execute(
                text("""
                    SELECT DISTINCT s.enrollment_year
                    FROM students s
                    WHERE s.enrollment_year IS NOT NULL
                    ORDER BY s.enrollment_year DESC
                """)
            ).fetchall()
        else:
            results = self.db.execute(
                text("""
                    SELECT DISTINCT s.enrollment_year
                    FROM students s
                    JOIN classes c ON s.class_id = c.id
                    JOIN majors m ON c.major_id = m.id
                    WHERE s.enrollment_year IS NOT NULL
                      AND m.faculty_id = :faculty_id
                    ORDER BY s.enrollment_year DESC
                """),
                {"faculty_id": faculty_id},
            ).fetchall()

        return [int(row[0]) for row in results if row[0] is not None]

    def list_semesters(self, faculty_id: Optional[str] = None) -> List[dict]:
        if faculty_id is None:
            results = self.db.execute(
                text("""
                    SELECT DISTINCT sem.id, sem.semester_name, sem.academic_year
                    FROM semesters sem
                    JOIN course_sections cs ON cs.semester_id = sem.id
                    JOIN student_scores sc ON sc.section_id = cs.id
                    ORDER BY sem.academic_year DESC, sem.semester_name DESC
                """)
            ).fetchall()
        else:
            results = self.db.execute(
                text("""
                    SELECT DISTINCT sem.id, sem.semester_name, sem.academic_year
                    FROM semesters sem
                    JOIN course_sections cs ON cs.semester_id = sem.id
                    JOIN student_scores sc ON sc.section_id = cs.id
                    JOIN students s ON s.id = sc.student_id
                    JOIN classes c ON s.class_id = c.id
                    JOIN majors m ON c.major_id = m.id
                    WHERE m.faculty_id = :faculty_id
                    ORDER BY sem.academic_year DESC, sem.semester_name DESC
                """),
                {"faculty_id": faculty_id},
            ).fetchall()

        return [
            {
                "id": str(row[0]),
                "semester_name": str(row[1]),
                "academic_year": str(row[2]),
            }
            for row in results
        ]

    def list_faculties(self) -> List[dict]:
        results = self.db.execute(
            text("""
                SELECT id, name
                FROM faculties
                ORDER BY name
            """)
        ).fetchall()
        return [{"id": str(row[0]), "name": str(row[1])} for row in results]

    def list_majors(self, faculty_id: Optional[str] = None) -> List[dict]:
        if faculty_id is None:
            results = self.db.execute(
                text("""
                    SELECT m.id, m.name, m.faculty_id, f.name
                    FROM majors m
                    JOIN faculties f ON f.id = m.faculty_id
                    ORDER BY f.name, m.name
                """)
            ).fetchall()
        else:
            results = self.db.execute(
                text("""
                    SELECT m.id, m.name, m.faculty_id, f.name
                    FROM majors m
                    JOIN faculties f ON f.id = m.faculty_id
                    WHERE m.faculty_id = :faculty_id
                    ORDER BY m.name
                """),
                {"faculty_id": faculty_id},
            ).fetchall()
        return [
            {
                "id": str(row[0]),
                "name": str(row[1]),
                "faculty_id": str(row[2]),
                "faculty_name": str(row[3]),
            }
            for row in results
        ]

    def list_students_filtered(
        self,
        skip: int,
        limit: int,
        enrollment_year: Optional[int] = None,
        faculty_id: Optional[str] = None,
        major_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> List[dict]:
        where_clauses = []
        params = {"limit": limit, "skip": skip}

        if enrollment_year is not None:
            where_clauses.append("s.enrollment_year = :enrollment_year")
            params["enrollment_year"] = enrollment_year
        if faculty_id is not None:
            where_clauses.append("f.id = :faculty_id")
            params["faculty_id"] = faculty_id
        if major_id is not None:
            where_clauses.append("m.id = :major_id")
            params["major_id"] = major_id

        if status_filter == "studying":
            where_clauses.append(
                "COALESCE(aw_latest.warning_level, 'normal') = 'normal' "
                "AND COALESCE(mp_latest.predicted_warning, FALSE) = FALSE"
            )
        elif status_filter == "warning":
            where_clauses.append("COALESCE(aw_latest.warning_level, 'normal') = 'warning'")
        elif status_filter == "near_warning_ml":
            where_clauses.append(
                "COALESCE(aw_latest.warning_level, 'normal') = 'normal' "
                "AND (COALESCE(mp_latest.predicted_warning, FALSE) = TRUE "
                "OR COALESCE(mp_latest.probability, 0) >= 0.65)"
            )

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        results = self.db.execute(
            text(f"""
                SELECT
                    s.id,
                    s.student_code,
                    s.last_name || ' ' || s.first_name AS full_name,
                    s.enrollment_year,
                    c.class_code,
                    m.id AS major_id,
                    m.name AS major_name,
                    f.id AS faculty_id,
                    f.name AS faculty_name,
                    COALESCE(aw_latest.warning_level, 'normal') AS warning_level,
                    COALESCE(mp_latest.predicted_warning, FALSE) AS predicted_warning,
                    mp_latest.probability
                FROM students s
                JOIN classes c ON c.id = s.class_id
                JOIN majors m ON m.id = c.major_id
                JOIN faculties f ON f.id = m.faculty_id
                LEFT JOIN LATERAL (
                    SELECT aw.warning_level
                    FROM academic_warnings aw
                    WHERE aw.student_id = s.id
                    ORDER BY aw.created_at DESC
                    LIMIT 1
                ) aw_latest ON TRUE
                LEFT JOIN LATERAL (
                    SELECT mp.predicted_warning, mp.probability
                    FROM ml_predictions mp
                    WHERE mp.student_id = s.id
                    ORDER BY mp.created_at DESC
                    LIMIT 1
                ) mp_latest ON TRUE
                {where_sql}
                ORDER BY s.student_code
                LIMIT :limit OFFSET :skip
            """),
            params,
        ).fetchall()

        return [
            {
                "student_id": str(row[0]),
                "student_code": str(row[1]),
                "full_name": str(row[2]),
                "enrollment_year": int(row[3]) if row[3] is not None else None,
                "class_code": str(row[4]) if row[4] else None,
                "major_id": str(row[5]) if row[5] else None,
                "major_name": str(row[6]) if row[6] else None,
                "faculty_id": str(row[7]) if row[7] else None,
                "faculty_name": str(row[8]) if row[8] else None,
                "warning_level": str(row[9]) if row[9] else "normal",
                "predicted_warning": bool(row[10]),
                "ml_probability": float(row[11]) if row[11] is not None else None,
            }
            for row in results
        ]

    def count_students_filtered(
        self,
        enrollment_year: Optional[int] = None,
        faculty_id: Optional[str] = None,
        major_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> int:
        where_clauses = []
        params: dict = {}

        if enrollment_year is not None:
            where_clauses.append("s.enrollment_year = :enrollment_year")
            params["enrollment_year"] = enrollment_year
        if faculty_id is not None:
            where_clauses.append("f.id = :faculty_id")
            params["faculty_id"] = faculty_id
        if major_id is not None:
            where_clauses.append("m.id = :major_id")
            params["major_id"] = major_id

        if status_filter == "studying":
            where_clauses.append(
                "COALESCE(aw_latest.warning_level, 'normal') = 'normal' "
                "AND COALESCE(mp_latest.predicted_warning, FALSE) = FALSE"
            )
        elif status_filter == "warning":
            where_clauses.append("COALESCE(aw_latest.warning_level, 'normal') = 'warning'")
        elif status_filter == "near_warning_ml":
            where_clauses.append(
                "COALESCE(aw_latest.warning_level, 'normal') = 'normal' "
                "AND (COALESCE(mp_latest.predicted_warning, FALSE) = TRUE "
                "OR COALESCE(mp_latest.probability, 0) >= 0.65)"
            )

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        result = self.db.execute(
            text(f"""
                SELECT COUNT(*)
                FROM students s
                JOIN classes c ON c.id = s.class_id
                JOIN majors m ON m.id = c.major_id
                JOIN faculties f ON f.id = m.faculty_id
                LEFT JOIN LATERAL (
                    SELECT aw.warning_level
                    FROM academic_warnings aw
                    WHERE aw.student_id = s.id
                    ORDER BY aw.created_at DESC
                    LIMIT 1
                ) aw_latest ON TRUE
                LEFT JOIN LATERAL (
                    SELECT mp.predicted_warning, mp.probability
                    FROM ml_predictions mp
                    WHERE mp.student_id = s.id
                    ORDER BY mp.created_at DESC
                    LIMIT 1
                ) mp_latest ON TRUE
                {where_sql}
            """),
            params,
        ).scalar()

        return int(result or 0)
