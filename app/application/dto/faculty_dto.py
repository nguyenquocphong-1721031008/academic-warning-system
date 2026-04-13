from pydantic import BaseModel


class FacultyCreateDTO(BaseModel):
    name: str


class FacultyUpdateDTO(BaseModel):
    name: str


class FacultyResponseDTO(BaseModel):
    id: str
    name: str
