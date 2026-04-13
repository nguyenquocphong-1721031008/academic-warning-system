from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal

from app.domain.entities.semester_stat_row import SemesterStatRegenerationRow
from app.domain.entities.student_semester_stat import StudentSemesterStat
from app.domain.repositories.student_stat_repository import StudentStatRepository


class StudentStatRepositoryImpl(StudentStatRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_latest_stat(self, student_id: str) -> Optional[StudentSemesterStat]:
        result = self.db.execute(
            text("""
                SELECT id, student_id, semester_id, total_subjects, total_failed,
                       semester_gpa, cumulative_gpa
                FROM student_semester_stats
                WHERE student_id = :student_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"student_id": student_id},
        ).fetchone()

        if not result:
            return None

        return StudentSemesterStat(
            id=str(result[0]),
            student_id=str(result[1]),
            semester_id=str(result[2]),
            total_subjects=int(result[3]) if result[3] else 0,
            total_failed=int(result[4]) if result[4] else 0,
            semester_gpa=Decimal(str(result[5])) if result[5] else None,
            cumulative_gpa=Decimal(str(result[6])) if result[6] else None,
        )

    def get_by_student_and_semester(
        self, student_id: str, semester_id: str
    ) -> Optional[StudentSemesterStat]:
        result = self.db.execute(
            text("""
                SELECT id, student_id, semester_id, total_subjects, total_failed,
                       semester_gpa, cumulative_gpa
                FROM student_semester_stats
                WHERE student_id = :student_id AND semester_id = :semester_id
            """),
            {"student_id": student_id, "semester_id": semester_id},
        ).fetchone()

        if not result:
            return None

        return StudentSemesterStat(
            id=str(result[0]),
            student_id=str(result[1]),
            semester_id=str(result[2]),
            total_subjects=int(result[3]) if result[3] else 0,
            total_failed=int(result[4]) if result[4] else 0,
            semester_gpa=Decimal(str(result[5])) if result[5] is not None else None,
            cumulative_gpa=Decimal(str(result[6])) if result[6] is not None else None,
        )

    def list_for_warning_regeneration(self) -> List[SemesterStatRegenerationRow]:
        results = self.db.execute(
            text("""
                SELECT
                    sss.student_id,
                    sss.semester_id,
                    sss.total_subjects,
                    sss.total_failed,
                    sss.semester_gpa,
                    sss.cumulative_gpa,
                    s.enrollment_year,
                    sem.academic_year
                FROM student_semester_stats sss
                JOIN students s ON sss.student_id = s.id
                JOIN semesters sem ON sss.semester_id = sem.id
                WHERE COALESCE(sss.total_subjects, 0) > 0
            """)
        ).fetchall()

        rows: List[SemesterStatRegenerationRow] = []
        for row in results:
            rows.append(
                SemesterStatRegenerationRow(
                    student_id=str(row[0]),
                    semester_id=str(row[1]),
                    total_subjects=int(row[2]) if row[2] is not None else 0,
                    total_failed=int(row[3]) if row[3] is not None else 0,
                    semester_gpa=Decimal(str(row[4])) if row[4] is not None else None,
                    cumulative_gpa=Decimal(str(row[5])) if row[5] is not None else None,
                    enrollment_year=int(row[6]) if row[6] is not None else 0,
                    semester_academic_year=str(row[7]) if row[7] else "",
                )
            )
        return rows

    def get_latest_regeneration_row_for_student(
        self,
        student_id: str,
    ) -> Optional[SemesterStatRegenerationRow]:
        result = self.db.execute(
            text("""
                SELECT
                    sss.student_id,
                    sss.semester_id,
                    sss.total_subjects,
                    sss.total_failed,
                    sss.semester_gpa,
                    sss.cumulative_gpa,
                    s.enrollment_year,
                    sem.academic_year
                FROM student_semester_stats sss
                JOIN students s ON sss.student_id = s.id
                JOIN semesters sem ON sss.semester_id = sem.id
                WHERE sss.student_id = :student_id
                ORDER BY sem.start_date DESC NULLS LAST
                LIMIT 1
            """),
            {"student_id": student_id},
        ).fetchone()

        if not result:
            return None

        return SemesterStatRegenerationRow(
            student_id=str(result[0]),
            semester_id=str(result[1]),
            total_subjects=int(result[2]) if result[2] is not None else 0,
            total_failed=int(result[3]) if result[3] is not None else 0,
            semester_gpa=Decimal(str(result[4])) if result[4] is not None else None,
            cumulative_gpa=Decimal(str(result[5])) if result[5] is not None else None,
            enrollment_year=int(result[6]) if result[6] is not None else 0,
            semester_academic_year=str(result[7]) if result[7] else "",
        )
