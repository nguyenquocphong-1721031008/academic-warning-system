from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]: ...

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]: ...

    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def update(self, user: User) -> User: ...

    @abstractmethod
    def delete(self, user_id: str) -> bool: ...

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]: ...

    @abstractmethod
    def update_password(self, user_id: str, new_password_hash: str) -> bool: ...
