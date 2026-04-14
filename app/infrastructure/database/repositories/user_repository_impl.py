from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.domain.repositories.user_repository import UserRepository
from app.domain.entities.user import User


class UserRepositoryImpl(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> Optional[User]:
        result = self.db.execute(
            text("""
                SELECT id, username, password_hash, role, faculty_id, created_at, is_active
                FROM users
                WHERE username = :username
            """),
            {"username": username},
        ).fetchone()

        if not result:
            return None

        return User(
            id=str(result[0]),
            username=str(result[1]),
            password_hash=str(result[2]),
            role=str(result[3]),
            faculty_id=str(result[4]) if result[4] else None,
            created_at=result[5] if result[5] else datetime.now(),
            is_active=bool(result[6]),
        )

    def get_by_id(self, user_id: str) -> Optional[User]:
        result = self.db.execute(
            text("""
                SELECT id, username, password_hash, role, faculty_id, created_at, is_active
                FROM users
                WHERE id = :id
            """),
            {"id": user_id},
        ).fetchone()

        if not result:
            return None

        return User(
            id=str(result[0]),
            username=str(result[1]),
            password_hash=str(result[2]),
            role=str(result[3]),
            faculty_id=str(result[4]) if result[4] else None,
            created_at=result[5] if result[5] else datetime.now(),
            is_active=bool(result[6]),
        )

    def create(self, user: User) -> User:
        user_id = self.db.execute(
            text("""
                INSERT INTO users (id, username, password_hash, role, faculty_id, created_at, is_active)
                VALUES (:id, :username, :password_hash, :role, :faculty_id, :created_at, :is_active)
                RETURNING id
            """),
            {
                "id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "role": user.role,
                "faculty_id": user.faculty_id,
                "created_at": user.created_at,
                "is_active": user.is_active,
            },
        ).scalar()

        self.db.commit()
        return self.get_by_id(user_id)

    def update(self, user: User) -> User:
        self.db.execute(
            text("""
                UPDATE users
                SET username = :username,
                    role = :role,
                    faculty_id = :faculty_id
                WHERE id = :id
            """),
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "faculty_id": user.faculty_id,
            },
        )
        self.db.commit()
        return self.get_by_id(user.id)

    def delete(self, user_id: str) -> bool:
        return self.update_status(user_id, False)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        results = self.db.execute(
            text("""
                SELECT id, username, password_hash, role, faculty_id, created_at, is_active
                FROM users
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
            """),
            {"limit": limit, "skip": skip},
        ).fetchall()

        return [
            User(
                id=str(row[0]),
                username=str(row[1]),
                password_hash=str(row[2]),
                role=str(row[3]),
                faculty_id=str(row[4]) if row[4] else None,
                created_at=row[5] if row[5] else datetime.now(),
                is_active=bool(row[6]),
            )
            for row in results
        ]

    def update_password(self, user_id: str, new_password_hash: str) -> bool:
        result = self.db.execute(
            text("""
                UPDATE users
                SET password_hash = :password_hash
                WHERE id = :id
            """),
            {"id": user_id, "password_hash": new_password_hash},
        )
        self.db.commit()
        return result.rowcount > 0

    def update_status(self, user_id: str, is_active: bool) -> bool:
        result = self.db.execute(
            text("""
                UPDATE users
                SET is_active = :is_active
                WHERE id = :id
            """),
            {"id": user_id, "is_active": is_active},
        )
        self.db.commit()
        return result.rowcount > 0
