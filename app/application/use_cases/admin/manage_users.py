from typing import List
from app.domain.repositories.user_repository import UserRepository
from app.domain.entities.user import User
from app.infrastructure.security.auth import get_password_hash
from app.application.dto.user_dto import UserCreateDTO, UserUpdateDTO, UserResponseDTO
from datetime import datetime
import uuid


class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_data: UserCreateDTO) -> UserResponseDTO:
        existing_user = self.user_repo.get_by_username(user_data.username)
        if existing_user:
            raise ValueError(f"Username {user_data.username} already exists")

        student_id = None
        faculty_id = None

        if user_data.role == "student":
            student_id = getattr(user_data, "student_id", None)

        elif user_data.role == "faculty_manager":
            faculty_id = user_data.faculty_id

        user = User(
            id=str(uuid.uuid4()),
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            role=user_data.role,
            faculty_id=faculty_id,
            student_id=student_id,
            created_at=datetime.now(),
        )

        created_user = self.user_repo.create(user)

        return UserResponseDTO(
            id=created_user.id,
            username=created_user.username,
            role=created_user.role,
            faculty_id=created_user.faculty_id,
            student_id=created_user.student_id,
            is_active=created_user.is_active,
        )


class UpdateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: str, user_data: UserUpdateDTO) -> UserResponseDTO:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        if user_data.username is not None:
            existing = self.user_repo.get_by_username(user_data.username)
            if existing and existing.id != user_id:
                raise ValueError(f"Username {user_data.username} already exists")
            user.username = user_data.username

        if user_data.role is not None:
            user.role = user_data.role

        if user_data.role == "student":
            if hasattr(user_data, "student_id"):
                user.student_id = user_data.student_id
            user.faculty_id = None

        elif user_data.role == "faculty_manager":
            if user_data.faculty_id is not None:
                user.faculty_id = user_data.faculty_id
            user.student_id = None

        updated_user = self.user_repo.update(user)

        return UserResponseDTO(
            id=updated_user.id,
            username=updated_user.username,
            role=updated_user.role,
            faculty_id=updated_user.faculty_id,
            student_id=updated_user.student_id,
            is_active=updated_user.is_active,
        )


class DeleteUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: str) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        return self.user_repo.delete(user_id)


class GetUsersUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, skip: int = 0, limit: int = 100) -> List[UserResponseDTO]:
        users = self.user_repo.get_all(skip=skip, limit=limit)

        return [
            UserResponseDTO(
                id=user.id,
                username=user.username,
                role=user.role,
                faculty_id=user.faculty_id,
                student_id=user.student_id,
                is_active=user.is_active,
            )
            for user in users
        ]


class ResetPasswordUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: str, new_password: str) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        new_password_hash = get_password_hash(new_password)
        return self.user_repo.update_password(user_id, new_password_hash)


class UpdateUserStatusUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: str, is_active: bool) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return self.user_repo.update_status(user_id, is_active)
