from typing import List
from app.domain.repositories.faculty_repository import FacultyRepository
from app.domain.entities.faculty import Faculty
from app.application.dto.faculty_dto import (
    FacultyCreateDTO,
    FacultyUpdateDTO,
    FacultyResponseDTO,
)
import uuid


class CreateFacultyUseCase:
    def __init__(self, faculty_repo: FacultyRepository):
        self.faculty_repo = faculty_repo

    def execute(self, faculty_data: FacultyCreateDTO) -> FacultyResponseDTO:
        faculty = Faculty(id=str(uuid.uuid4()), name=faculty_data.name)

        created_faculty = self.faculty_repo.create(faculty)

        return FacultyResponseDTO(id=created_faculty.id, name=created_faculty.name)


class UpdateFacultyUseCase:
    def __init__(self, faculty_repo: FacultyRepository):
        self.faculty_repo = faculty_repo

    def execute(
        self, faculty_id: str, faculty_data: FacultyUpdateDTO
    ) -> FacultyResponseDTO:
        faculty = self.faculty_repo.get_by_id(faculty_id)
        if not faculty:
            raise ValueError(f"Faculty {faculty_id} not found")

        faculty.name = faculty_data.name
        updated_faculty = self.faculty_repo.update(faculty)

        return FacultyResponseDTO(id=updated_faculty.id, name=updated_faculty.name)


class DeleteFacultyUseCase:
    def __init__(self, faculty_repo: FacultyRepository):
        self.faculty_repo = faculty_repo

    def execute(self, faculty_id: str) -> bool:
        faculty = self.faculty_repo.get_by_id(faculty_id)
        if not faculty:
            raise ValueError(f"Faculty {faculty_id} not found")

        return self.faculty_repo.delete(faculty_id)


class GetFacultiesUseCase:
    def __init__(self, faculty_repo: FacultyRepository):
        self.faculty_repo = faculty_repo

    def execute(self) -> List[FacultyResponseDTO]:
        faculties = self.faculty_repo.get_all()

        return [FacultyResponseDTO(id=f.id, name=f.name) for f in faculties]
