from __future__ import annotations
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ViolationMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    en: str = ""
    vi: str = ""


class ViolationType(str, Enum):
    validation = "validation"
    not_found = "notFound"
    duplicate = "duplicate"
    unauthorized = "unauthorized"
    forbidden = "forbidden"
    invalid_otp = "invalidOtp"
    business = "business"


class ResponseStatus(str, Enum):
    success = "success"
    fail = "fail"


class Violation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: ViolationMessage = Field(default_factory=ViolationMessage)
    type: ViolationType
    code: int
    field: Optional[str] = None


class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)
    message: ViolationMessage = Field(default_factory=ViolationMessage)
    data: Optional[T] = None
    status: ResponseStatus = ResponseStatus.success
    time_stamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), alias="timeStamp"
    )
    violations: list[Violation] = Field(default_factory=list)


def _dump(body: ApiResponse[Any]) -> dict[str, Any]:
    return body.model_dump(mode="json", by_alias=True)


def serialize_for_json(data: Any) -> Any:
    if data is None:
        return None
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    if isinstance(data, Enum):
        return data.value
    if isinstance(data, Decimal):
        return float(data)
    if isinstance(data, (datetime, date)):
        return data.isoformat() if hasattr(data, "isoformat") else str(data)
    if isinstance(data, UUID):
        return str(data)
    if isinstance(data, list):
        return [serialize_for_json(x) for x in data]
    if isinstance(data, dict):
        return {k: serialize_for_json(v) for k, v in data.items()}
    if hasattr(data, "__dict__") and (not isinstance(data, type)):
        return {
            k: serialize_for_json(v)
            for k, v in data.__dict__.items()
            if not k.startswith("_")
        }
    return data


class ResponseHelper:
    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def success(
        data: Any = None,
        message_vi: str = "Thành công",
        message_en: str = "Success",
        status_code: int = 200,
    ) -> tuple[dict[str, Any], int]:
        body = ApiResponse[Any](
            message=ViolationMessage(en=message_en, vi=message_vi),
            data=data,
            status=ResponseStatus.success,
            time_stamp=ResponseHelper.utc_now(),
            violations=[],
        )
        return (_dump(body), status_code)

    @staticmethod
    def fail(
        message_vi: str,
        message_en: str,
        status_code: int = 400,
        violations: Optional[list[Violation]] = None,
    ) -> tuple[dict[str, Any], int]:
        body = ApiResponse[Any](
            message=ViolationMessage(en=message_en, vi=message_vi),
            data=None,
            status=ResponseStatus.fail,
            time_stamp=ResponseHelper.utc_now(),
            violations=violations or [],
        )
        return (_dump(body), status_code)

    @staticmethod
    def validation_error(violations: list[Violation]) -> tuple[dict[str, Any], int]:
        return ResponseHelper.fail(
            "Dữ liệu không hợp lệ", "Validation failed", 400, violations
        )

    @staticmethod
    def not_found(resource_name: str) -> tuple[dict[str, Any], int]:
        violation = Violation(
            type=ViolationType.not_found,
            code=404,
            message=ViolationMessage(
                en=f"{resource_name} not found", vi=f"{resource_name} không tồn tại"
            ),
        )
        return ResponseHelper.fail(
            f"{resource_name} không tồn tại",
            f"{resource_name} not found",
            404,
            [violation],
        )

    @staticmethod
    def duplicate(field: str) -> tuple[dict[str, Any], int]:
        violation = Violation(
            type=ViolationType.duplicate,
            code=400,
            field=field,
            message=ViolationMessage(
                en=f"{field} already exists", vi=f"{field} đã tồn tại"
            ),
        )
        return ResponseHelper.fail(
            f"{field} đã tồn tại", f"{field} already exists", 400, [violation]
        )

    @staticmethod
    def unauthorized() -> tuple[dict[str, Any], int]:
        violation = Violation(
            type=ViolationType.unauthorized,
            code=401,
            message=ViolationMessage(en="Unauthorized", vi="Không có quyền truy cập"),
        )
        return ResponseHelper.fail(
            "Không có quyền truy cập", "Unauthorized", 401, [violation]
        )

    @staticmethod
    def forbidden() -> tuple[dict[str, Any], int]:
        violation = Violation(
            type=ViolationType.forbidden,
            code=403,
            message=ViolationMessage(en="Forbidden", vi="Bị từ chối truy cập"),
        )
        return ResponseHelper.fail("Bị từ chối truy cập", "Forbidden", 403, [violation])

    @staticmethod
    def business_error(message_vi: str, message_en: str) -> tuple[dict[str, Any], int]:
        violation = Violation(
            type=ViolationType.business,
            code=400,
            message=ViolationMessage(en=message_en, vi=message_vi),
        )
        return ResponseHelper.fail(message_vi, message_en, 400, [violation])


def success_response(
    data: Any = None, message_vi: str = "Thành công", message_en: str = "Success"
) -> dict[str, Any]:
    normalized = serialize_for_json(data)
    payload, _ = ResponseHelper.success(normalized, message_vi, message_en, 200)
    return payload


def fail_response(
    message_vi: str,
    message_en: str,
    violations: Optional[list[Violation]] = None,
    status_code: int = 400,
) -> dict[str, Any]:
    payload, _ = ResponseHelper.fail(message_vi, message_en, status_code, violations)
    return payload
