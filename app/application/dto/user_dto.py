from typing import Optional
from pydantic import BaseModel


class UserCreateDTO(BaseModel):
    username: str
    password: str
    role: str
    faculty_id: Optional[str] = None


class UserUpdateDTO(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    faculty_id: Optional[str] = None


class UserResponseDTO(BaseModel):
    id: str
    username: str
    role: str
    faculty_id: Optional[str] = None


class ResetPasswordDTO(BaseModel):
    new_password: str
