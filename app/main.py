from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.admin_router import router as admin_router
from app.api.auth_router import router as auth_router
from app.api.faculty_manager_router import router as faculty_manager_router
from app.api.ml_router import router as ml_router
from app.api.schemas.response import (
    ResponseHelper,
    Violation,
    ViolationMessage,
    ViolationType,
    fail_response,
    success_response,
)
from app.api.score_router import router as score_router
from app.api.warning_router import router as warning_router
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import engine
from app.infrastructure.ml.registry import MlRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = MlRegistry()
    try:
        registry.load_all_from_artifacts_dir()
    except Exception as exc:
        logger = logging.getLogger(__name__)
        logger.warning("ML registry load failed: %s", exc)
    app.state.ml_registry = registry
    yield


app = FastAPI(
    title="Academic Warning System API",
    description="Hệ thống quản lý cảnh báo học tập — Clean Architecture",
    version="1.0.0",
    lifespan=lifespan,
)

_settings = get_settings()
if (
    _settings.app_env.lower() in {"prod", "production"}
    and _settings.secret_key == "your-secret-key-change-in-production"
):
    raise RuntimeError("SECRET_KEY must be set in production environment")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_settings.cors_allow_origins),
    allow_credentials=bool(_settings.cors_allow_credentials),
    allow_methods=list(_settings.cors_allow_methods),
    allow_headers=list(_settings.cors_allow_headers),
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(_settings.trusted_hosts))


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
    )
    if _settings.app_env.lower() in {"prod", "production"}:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_PATH, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(LOG_PATH, "academic_warning.log"),
    filemode="a",
)

api_prefix = "/api"

app.include_router(auth_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)
app.include_router(faculty_manager_router, prefix=api_prefix)
app.include_router(score_router, prefix=api_prefix)
app.include_router(warning_router, prefix=api_prefix)
app.include_router(ml_router, prefix=api_prefix)

logger = logging.getLogger(__name__)

try:
    with engine.begin() as conn:
        conn.execute(
            text("""
            ALTER TABLE academic_warnings
            ADD COLUMN IF NOT EXISTS warning_status VARCHAR(20) DEFAULT 'open' NOT NULL
        """)
        )
        conn.execute(
            text("""
            ALTER TABLE academic_warnings
            ADD COLUMN IF NOT EXISTS warning_note TEXT
        """)
        )
        conn.execute(
            text("""
            UPDATE academic_warnings
            SET warning_status = 'open'
            WHERE warning_status IS NULL
        """)
        )
        conn.execute(
            text("""
            UPDATE academic_warnings
            SET warning_note = ''
            WHERE warning_note IS NULL
        """)
        )
except Exception as exc:
    logger.warning(
        "Could not ensure warning_status/warning_note columns in academic_warnings: %s",
        exc,
    )


def _validation_violations_from_errors(errors: list[dict]) -> list[Violation]:
    violations: list[Violation] = []
    for err in errors:
        loc = err.get("loc") or ()
        field = ".".join(str(x) for x in loc if x != "body") or None
        msg = str(err.get("msg", "Invalid"))
        violations.append(
            Violation(
                type=ViolationType.validation,
                code=400,
                field=field,
                message=ViolationMessage(en=msg, vi=msg),
            )
        )
    return violations


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    violations = _validation_violations_from_errors(exc.errors())
    content, status_code = ResponseHelper.validation_error(violations)
    return JSONResponse(status_code=status_code, content=content)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    violations = _validation_violations_from_errors(exc.errors())
    content, status_code = ResponseHelper.validation_error(violations)
    return JSONResponse(status_code=status_code, content=content)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    msg = detail if isinstance(detail, str) else str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=fail_response(message_vi=msg, message_en=msg),
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(
    request: Request, exc: FileNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content=fail_response(
            message_vi="Thiếu tài nguyên hệ thống (model/file)",
            message_en="Required system artifact is missing",
        ),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=fail_response(
            message_vi=str(exc) or "Dữ liệu không hợp lệ",
            message_en=str(exc) or "Invalid input",
        ),
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.exception("Database error %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content=fail_response(
            message_vi="Lỗi truy cập cơ sở dữ liệu",
            message_en="Database temporarily unavailable",
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled error %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content=fail_response(
            message_vi="Lỗi máy chủ nội bộ",
            message_en="Internal server error",
        ),
    )


@app.get("/health")
def health():
    return success_response(
        data={"status": "ok"},
        message_vi="Dịch vụ hoạt động",
        message_en="Service is healthy",
    )
