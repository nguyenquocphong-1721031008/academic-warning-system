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
        self, faculty_id: Optional[str], skip: int, limit: int
    ) -> List[Student]:
        if faculty_id is None:
            results = self.db.execute(
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
                    JOIN classes c ON s.class_id = c.id
                    ORDER BY s.student_code
                    LIMIT :limit OFFSET :skip
                """),
                {"limit": limit, "skip": skip},
            ).fetchall()
        else:
            results = self.db.execute(
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
                    JOIN classes c ON s.class_id = c.id
                    JOIN majors m ON c.major_id = m.id
                    WHERE m.faculty_id = :faculty_id
                    ORDER BY s.student_code
                    LIMIT :limit OFFSET :skip
                """),
                {"faculty_id": faculty_id, "limit": limit, "skip": skip},
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
