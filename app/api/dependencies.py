from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.domain.entities.user import User
from app.infrastructure.database.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from app.infrastructure.database.session import get_db
from app.infrastructure.security.auth import decode_access_token

optional_bearer = HTTPBearer(auto_error=False)


def get_optional_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(optional_bearer),
    ],
    db: Session = Depends(get_db),
) -> Optional[User]:
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    user_repo = UserRepositoryImpl(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def is_internal_warning_viewer(user: Optional[User]) -> bool:
    return user is not None and (user.is_admin() or user.is_faculty_manager())
