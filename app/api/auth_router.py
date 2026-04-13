from datetime import datetime, timedelta, timezone
import secrets

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.rate_limit import SlidingWindowLimiter, client_ip
from app.api.schemas.response import success_response
from app.domain.entities.user import User
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from app.infrastructure.database.session import get_db
from app.infrastructure.security.auth import (
    create_access_token,
    decode_access_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
_settings = get_settings()
_login_ip_limiter = SlidingWindowLimiter(
    limit=_settings.auth_login_ip_rate_limit_per_minute,
    window_seconds=60,
)
_login_user_limiter = SlidingWindowLimiter(
    limit=_settings.auth_login_user_rate_limit_per_minute,
    window_seconds=60,
)


class LoginRequest(BaseModel):
    username: str
    password: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user_repo = UserRepositoryImpl(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


def get_current_admin_or_faculty_manager(
    current_user: User = Depends(get_current_user),
) -> User:
    if not (current_user.is_admin() or current_user.is_faculty_manager()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Faculty Manager access required",
        )
    return current_user


class RefreshTokenRequest(BaseModel):
    refresh_token: str


def _create_refresh_token(db: Session, user_id: str) -> str:
    settings = get_settings()
    token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    db.execute(
        text("""
            INSERT INTO refresh_tokens (id, user_id, token, is_revoked, expires_at, created_at)
            VALUES (gen_random_uuid(), :user_id, :token, FALSE, :expires_at, NOW())
        """),
        {
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at,
        },
    )
    db.commit()
    return token


def _get_refresh_token(db: Session, token: str):
    return db.execute(
        text("""
            SELECT id, user_id, token, is_revoked, expires_at
            FROM refresh_tokens
            WHERE token = :token
        """),
        {"token": token},
    ).fetchone()


def _revoke_refresh_token(db: Session, token: str) -> bool:
    result = db.execute(
        text("""
            UPDATE refresh_tokens
            SET is_revoked = TRUE
            WHERE token = :token
        """),
        {"token": token},
    )
    db.commit()
    return result.rowcount > 0


@router.post("/login")
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    normalized_username = login_data.username.strip().lower()
    _login_ip_limiter.hit(f"auth_login:ip:{client_ip(request)}")
    _login_user_limiter.hit(f"auth_login:user:{normalized_username}")

    user_repo = UserRepositoryImpl(db)
    user = user_repo.get_by_username(login_data.username)
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "faculty_id": str(user.faculty_id) if user.faculty_id else None,
        }
    )
    refresh_token = _create_refresh_token(db, str(user.id))

    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "role": user.role,
                "faculty_id": str(user.faculty_id) if user.faculty_id else None,
            },
        },
        message_vi="Đăng nhập thành công",
        message_en="Login successful",
    )


@router.post("/refresh")
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    token_data = _get_refresh_token(db, payload.refresh_token)
    if not token_data or token_data[3] or token_data[4] < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = str(token_data[1])
    user_repo = UserRepositoryImpl(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "faculty_id": str(user.faculty_id) if user.faculty_id else None,
        }
    )

    _revoke_refresh_token(db, payload.refresh_token)
    new_refresh_token = _create_refresh_token(db, user_id)

    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        },
        message_vi="Refresh token thành công",
        message_en="Refresh successful",
    )


@router.post("/logout")
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    revoked = _revoke_refresh_token(db, payload.refresh_token)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token not found"
        )

    return success_response(
        data={},
        message_vi="Đăng xuất thành công",
        message_en="Logout successful",
    )


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return success_response(
        data={
            "id": str(current_user.id),
            "username": current_user.username,
            "role": current_user.role,
            "faculty_id": str(current_user.faculty_id)
            if current_user.faculty_id
            else None,
        },
        message_vi="OK",
        message_en="OK",
    )
