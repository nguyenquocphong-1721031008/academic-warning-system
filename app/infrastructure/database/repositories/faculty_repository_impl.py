from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.repositories.faculty_repository import FacultyRepository
from app.domain.entities.faculty import Faculty


class FacultyRepositoryImpl(FacultyRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, faculty_id: str) -> Optional[Faculty]:
        result = self.db.execute(
            text("SELECT id, name FROM faculties WHERE id = :id"), {"id": faculty_id}
        ).fetchone()

        if not result:
            return None

        return Faculty(id=str(result[0]), name=str(result[1]))

    def get_all(self) -> List[Faculty]:
        results = self.db.execute(
            text("SELECT id, name FROM faculties ORDER BY name")
        ).fetchall()

        return [Faculty(id=str(row[0]), name=str(row[1])) for row in results]

    def create(self, faculty: Faculty) -> Faculty:
        faculty_id = self.db.execute(
            text("""
                INSERT INTO faculties (id, name)
                VALUES (:id, :name)
                RETURNING id
            """),
            {"id": faculty.id, "name": faculty.name},
        ).scalar()

        self.db.commit()
        return self.get_by_id(faculty_id)

    def update(self, faculty: Faculty) -> Faculty:
        self.db.execute(
            text("UPDATE faculties SET name = :name WHERE id = :id"),
            {"id": faculty.id, "name": faculty.name},
        )
        self.db.commit()
        return self.get_by_id(faculty.id)

    def delete(self, faculty_id: str) -> bool:
        result = self.db.execute(
            text("DELETE FROM faculties WHERE id = :id"), {"id": faculty_id}
        )
        self.db.commit()
        return result.rowcount > 0
