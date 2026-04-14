from sqlalchemy import text
import logging
import pandas as pd
import re
from datetime import date, datetime
from uuid import UUID
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ImportScoresUseCase:
    def __init__(self, db):
        self.db = db

    def execute(self, df: pd.DataFrame) -> int:
        df.columns = (
            df.columns.str.strip()
            .str.replace(r"\n", " ", regex=True)
            .str.replace(r"\s+", " ", regex=True)
            .str.lower()
        )

        rename_map = {
            "mã sinh viên": "student_code",
            "họ đệm": "last_name",
            "tên": "first_name",
            "họ và tên": "full_name",
            "full name": "full_name",
            "tên lớp": "class_code",
            "giới tính": "gender",
            "ngày sinh": "date_of_birth",
            "ngay sinh": "date_of_birth",
            "date of birth": "date_of_birth",
            "tên môn học": "subject_name",
            "số tín chỉ": "credits",
            "mã lớp học phần": "section_code",
            "khoa": "faculty_name",
            "ngành": "major_name",
            "điểm 10": "score10",
            "điểm 4": "score4",
            "điểm chữ": "letter",
            "học kỳ": "semester_name",
            "tên đợt": "semester_name",
            "năm học": "academic_year",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        df = self._normalize_import_columns(df)

        caches = self._load_caches()

        inserted_count = 0
        scores_batch = []
        imported_enrollment_year_by_student: dict[str, int] = {}

        for row in df.itertuples(index=False):
            if pd.isna(row.student_code) or not str(row.student_code).strip():
                continue

            data = self._normalize_row(row)
            if not data:
                continue

            ay_id = self._get_or_create_academic_year(
                data["academic_year"], caches["academic_years"]
            )
            faculty_id = self._get_or_create_faculty(
                data["faculty_name"], caches["faculties"]
            )
            major_id = self._get_or_create_major(
                data["major_name"], faculty_id, caches["majors"]
            )
            class_id = self._get_or_create_class(
                data["class_code"], major_id, ay_id, caches["classes"]
            )
            student_id = self._get_or_create_student(
                data["student_code"],
                data["last_name"],
                data["first_name"],
                data["gender"],
                data["date_of_birth"],
                class_id,
                data["enrollment_year"],
                caches["students"],
            )
            existing_year = imported_enrollment_year_by_student.get(student_id)
            if existing_year is None:
                imported_enrollment_year_by_student[student_id] = data["enrollment_year"]
            else:
                imported_enrollment_year_by_student[student_id] = min(
                    existing_year,
                    data["enrollment_year"],
                )
            subject_id = self._get_or_create_subject(
                data["subject_name"], data["credits"], faculty_id, caches["subjects"]
            )
            semester_id = self._get_or_create_semester(
                data["semester_name"], data["academic_year"], ay_id, caches["semesters"]
            )
            section_id = self._get_or_create_section(
                subject_id, semester_id, data["section_code"], caches["sections"]
            )

            scores_batch.append(
                {
                    "student_id": student_id,
                    "section_id": section_id,
                    "score_10": data["score10"],
                    "score_4": data["score4"],
                    "letter_grade": data["letter_grade"],
                }
            )

            inserted_count += 1

            if len(scores_batch) >= 100:
                self._bulk_insert_scores(scores_batch)
                scores_batch = []

        if scores_batch:
            self._bulk_insert_scores(scores_batch)

        if imported_enrollment_year_by_student:
            self._sync_enrollment_year_from_import(
                imported_enrollment_year_by_student
            )

        if inserted_count > 0:
            self.db.commit()
            self.recalculate_all_stats_and_warnings()
            logger.info(
                "Imported scores and recalculated stats/warnings: %s rows",
                inserted_count,
            )

        return inserted_count

    def _normalize_import_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized_map = {}
        for col in df.columns:
            clean = re.sub(r"[^a-z0-9]+", "", str(col).lower())
            if clean in {"namhoc", "academicyear", "year"}:
                normalized_map[col] = "academic_year"
            elif clean in {"tendot", "hocky", "semester", "semestername"}:
                normalized_map[col] = "semester_name"
            elif clean in {"ngaysinh", "dateofbirth", "dob"}:
                normalized_map[col] = "date_of_birth"
        if normalized_map:
            df = df.rename(columns=normalized_map)
        return df

    def _normalize_row(self, row) -> Dict[str, Any]:
        try:
            student_code = str(row.student_code).strip()
            if not student_code:
                return {}

            last_name = str(getattr(row, "last_name", "")).strip()
            first_name = str(getattr(row, "first_name", "")).strip()
            full_name = str(getattr(row, "full_name", "")).strip()
            if full_name and (not last_name or not first_name):
                parts = full_name.split()
                if len(parts) == 1:
                    first_name = parts[0]
                    last_name = ""
                else:
                    first_name = parts[-1]
                    last_name = " ".join(parts[:-1])
            class_code = str(getattr(row, "class_code", "")).strip()
            date_of_birth = self._parse_date_of_birth(getattr(row, "date_of_birth", None))

            gender_raw = str(getattr(row, "gender", "")).lower().strip()
            gender = "female" if "nữ" in gender_raw else "male"

            subject_name = str(getattr(row, "subject_name", "")).strip()
            if not subject_name:
                return {}

            credits = (
                int(getattr(row, "credits", 3))
                if pd.notna(getattr(row, "credits", None))
                else 3
            )

            section_code_raw = str(getattr(row, "section_code", "")).strip()
            if not section_code_raw:
                return {}
            section_code = section_code_raw.split(".")[0]

            faculty_name = (
                str(getattr(row, "faculty_name", "")).strip()
                or "Khoa Kinh tế - Quản trị"
            )
            major_name = str(getattr(row, "major_name", "")).strip() or "Kế toán"

            semester_raw = str(getattr(row, "semester_name", "")).strip()
            academic_year_raw = str(getattr(row, "academic_year", "")).strip()
            academic_year = academic_year_raw.replace(" ", "").replace("_", "").strip()
            if not academic_year:
                semester_year_match = re.search(r"(20\d{2})\s*-\s*(20\d{2})", semester_raw)
                if semester_year_match:
                    academic_year = (
                        f"{semester_year_match.group(1)}-{semester_year_match.group(2)}"
                    )
            if len(academic_year) == 8 and academic_year.isdigit():
                academic_year = academic_year[:4] + "-" + academic_year[4:]
            if not academic_year:
                current_year = datetime.now().year
                academic_year = f"{current_year}-{current_year + 1}"

            if "_NH" in semester_raw:
                semester_name = semester_raw.split("_NH")[0].replace(" ", "").strip()
            elif "NH" in semester_raw:
                semester_name = semester_raw.split("NH")[0].replace(" ", "").strip()
            else:
                semester_name = semester_raw.replace(" ", "").strip()

            if semester_name.startswith("HK"):
                semester_name = semester_name[:3]
            else:
                semester_name = "HK1"

            score10 = pd.to_numeric(getattr(row, "score10", None), errors="coerce")
            score10 = float(score10) if pd.notna(score10) else None

            score4 = pd.to_numeric(getattr(row, "score4", None), errors="coerce")
            score4 = float(score4) if pd.notna(score4) else None

            letter = str(getattr(row, "letter", "")).strip() or None

            enrollment_year = self._extract_enrollment_year(
                class_code=class_code,
                student_code=student_code,
                academic_year=academic_year,
            )

            return {
                "student_code": student_code,
                "last_name": last_name,
                "first_name": first_name,
                "gender": gender,
                "class_code": class_code,
                "date_of_birth": date_of_birth,
                "enrollment_year": enrollment_year,
                "subject_name": subject_name,
                "credits": credits,
                "section_code": section_code,
                "faculty_name": faculty_name,
                "major_name": major_name,
                "academic_year": academic_year,
                "semester_name": semester_name,
                "score10": score10,
                "score4": score4,
                "letter_grade": letter,
            }
        except Exception:
            return {}

    def _extract_enrollment_year(
        self, class_code: str, student_code: str, academic_year: str
    ) -> int:
        class_match = re.search(r"^\D*(\d{2})", class_code.strip())
        if class_match:
            yy = int(class_match.group(1))
            if 18 <= yy <= 40:
                return 2000 + yy

        if "-" in academic_year:
            start_year = academic_year.split("-")[0].strip()
            if start_year.isdigit():
                return int(start_year)

        return datetime.now().year

    def _parse_date_of_birth(self, value: Any) -> date | None:
        if value is None or pd.isna(value):
            return None
        parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
        if pd.isna(parsed):
            return None
        return parsed.date()

    def _sync_enrollment_year_from_import(
        self, imported_enrollment_year_by_student: dict[str, int]
    ) -> None:
        if not imported_enrollment_year_by_student:
            return
        for student_id, enrollment_year in imported_enrollment_year_by_student.items():
            self.db.execute(
                text("""
                    UPDATE students
                    SET enrollment_year = :enrollment_year
                    WHERE id = :student_id
                """),
                {
                    "student_id": student_id,
                    "enrollment_year": enrollment_year,
                },
            )

    def _load_caches(self) -> Dict:
        return {
            "academic_years": {
                r.year_name: r.id
                for r in self.db.execute(
                    text("SELECT id, year_name FROM academic_years")
                )
            },
            "faculties": {
                r.name: r.id
                for r in self.db.execute(text("SELECT id, name FROM faculties"))
            },
            "majors": {
                (r.name, r.faculty_id): r.id
                for r in self.db.execute(
                    text("SELECT id, name, faculty_id FROM majors")
                )
            },
            "classes": {
                r.class_code: r.id
                for r in self.db.execute(text("SELECT id, class_code FROM classes"))
            },
            "students": {
                r.student_code: r.id
                for r in self.db.execute(text("SELECT id, student_code FROM students"))
            },
            "subjects": {
                r.name: r.id
                for r in self.db.execute(text("SELECT id, name FROM subjects"))
            },
            "semesters": {
                (r.semester_name, r.academic_year_id): r.id
                for r in self.db.execute(
                    text("SELECT id, semester_name, academic_year_id FROM semesters")
                )
            },
            "sections": {
                (r.subject_id, r.semester_id, r.section_code): r.id
                for r in self.db.execute(
                    text(
                        "SELECT id, subject_id, semester_id, section_code FROM course_sections"
                    )
                )
            },
        }

    def _get_or_create_academic_year(self, name: str, cache: Dict) -> UUID:
        cleaned_name = name.replace(" ", "").strip()
        if cleaned_name in cache:
            return cache[cleaned_name]
        id_ = self.db.execute(
            text("""
                INSERT INTO academic_years (year_name)
                VALUES (:n)
                ON CONFLICT (year_name) DO UPDATE SET year_name = EXCLUDED.year_name
                RETURNING id
            """),
            {"n": cleaned_name},
        ).scalar()
        cache[cleaned_name] = id_
        return id_

    def _get_or_create_faculty(self, name: str, cache: Dict) -> UUID:
        if name in cache:
            return cache[name]
        id_ = self.db.execute(
            text("""
                INSERT INTO faculties (name)
                VALUES (:n)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """),
            {"n": name},
        ).scalar()
        cache[name] = id_
        return id_

    def _get_or_create_major(self, name: str, faculty_id: UUID, cache: Dict) -> UUID:
        key = (name, faculty_id)
        if key in cache:
            return cache[key]
        id_ = self.db.execute(
            text("""
                INSERT INTO majors (name, faculty_id)
                VALUES (:n, :f)
                ON CONFLICT (name, faculty_id) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """),
            {"n": name, "f": faculty_id},
        ).scalar()
        cache[key] = id_
        return id_

    def _get_or_create_class(
        self, code: str, major_id: UUID, ay_id: UUID, cache: Dict
    ) -> UUID:
        if code in cache:
            return cache[code]
        id_ = self.db.execute(
            text("""
                INSERT INTO classes (class_code, major_id, academic_year_id)
                VALUES (:c, :m, :y)
                ON CONFLICT (class_code) DO UPDATE
                SET major_id = EXCLUDED.major_id, academic_year_id = EXCLUDED.academic_year_id
                RETURNING id
            """),
            {"c": code, "m": major_id, "y": ay_id},
        ).scalar()
        cache[code] = id_
        return id_

    def _get_or_create_student(
        self,
        code: str,
        last: str,
        first: str,
        gender: str,
        date_of_birth: date | None,
        class_id: UUID,
        enroll_year: int,
        cache: Dict,
    ) -> UUID:
        id_ = self.db.execute(
            text("""
                INSERT INTO students (
                    student_code, last_name, first_name, gender, date_of_birth, class_id, enrollment_year
                )
                VALUES (:code, :last, :first, :gender, :date_of_birth, :class_id, :year)
                ON CONFLICT (student_code) DO UPDATE
                SET last_name = EXCLUDED.last_name,
                    first_name = EXCLUDED.first_name,
                    gender = EXCLUDED.gender,
                    date_of_birth = COALESCE(EXCLUDED.date_of_birth, students.date_of_birth),
                    class_id = EXCLUDED.class_id,
                    enrollment_year = EXCLUDED.enrollment_year
                RETURNING id
            """),
            {
                "code": code,
                "last": last,
                "first": first,
                "gender": gender,
                "date_of_birth": date_of_birth,
                "class_id": class_id,
                "year": enroll_year,
            },
        ).scalar()
        cache[code] = id_
        return id_

    def _get_or_create_subject(
        self, name: str, credits: int, faculty_id: UUID, cache: Dict
    ) -> UUID:
        if name in cache:
            return cache[name]
        id_ = self.db.execute(
            text("""
                INSERT INTO subjects (name, credits, faculty_id)
                VALUES (:n, :c, :f)
                ON CONFLICT (name, faculty_id) DO UPDATE
                SET credits = EXCLUDED.credits
                RETURNING id
            """),
            {"n": name, "c": credits, "f": faculty_id},
        ).scalar()
        cache[name] = id_
        return id_

    def _get_or_create_semester(
        self, sem_name: str, ay_name: str, ay_id: UUID, cache: Dict
    ) -> UUID:
        key = (sem_name, ay_id)
        if key in cache:
            return cache[key]
        id_ = self.db.execute(
            text("""
                INSERT INTO semesters (semester_name, academic_year, academic_year_id)
                VALUES (:s, :a, :y)
                ON CONFLICT (semester_name, academic_year_id) DO UPDATE
                SET academic_year = EXCLUDED.academic_year
                RETURNING id
            """),
            {"s": sem_name, "a": ay_name, "y": ay_id},
        ).scalar()
        cache[key] = id_
        return id_

    def _get_or_create_section(
        self, subject_id: UUID, semester_id: UUID, section_code: str, cache: Dict
    ) -> UUID:
        key = (subject_id, semester_id, section_code)
        if key in cache:
            return cache[key]
        id_ = self.db.execute(
            text("""
                INSERT INTO course_sections (subject_id, semester_id, section_code)
                VALUES (:s, :sem, :c)
                ON CONFLICT (subject_id, semester_id, section_code) DO UPDATE
                SET section_code = EXCLUDED.section_code
                RETURNING id
            """),
            {"s": subject_id, "sem": semester_id, "c": section_code},
        ).scalar()
        cache[key] = id_
        return id_

    def _bulk_insert_scores(self, batch: list):
        if not batch:
            return

        self.db.execute(
            text("""
                INSERT INTO student_scores
                (student_id, section_id, score_10, score_4, letter_grade)
                VALUES (:student_id, :section_id, :score_10, :score_4, :letter_grade)
                ON CONFLICT (student_id, section_id) DO UPDATE
                SET score_10 = EXCLUDED.score_10,
                    score_4 = EXCLUDED.score_4,
                    letter_grade = EXCLUDED.letter_grade
            """),
            batch,
        )

        self.db.execute(
            text("""
                INSERT INTO enrollments (student_id, section_id, registered_at)
                SELECT :student_id, :section_id, NOW()
                ON CONFLICT (student_id, section_id) DO NOTHING
            """),
            batch,
        )

    def recalculate_all_stats_and_warnings(self):
        self.calculate_student_stats()
        self.calculate_cumulative_gpa()
        self._regenerate_warnings_from_db_rules()

    def calculate_student_stats(self):
        self.db.execute(text("TRUNCATE student_semester_stats"))

        self.db.execute(
            text("""
            INSERT INTO student_semester_stats
            (student_id, semester_id, total_subjects, total_failed, semester_gpa)
            SELECT
                sc.student_id,
                cs.semester_id,
                COUNT(*) AS total_subjects,
                COALESCE(SUM(CASE WHEN sc.score_4 <= 1 THEN 1 ELSE 0 END), 0) AS total_failed,
                ROUND(AVG(sc.score_4), 2) AS semester_gpa
            FROM student_scores sc
            JOIN course_sections cs ON cs.id = sc.section_id
            GROUP BY sc.student_id, cs.semester_id
        """)
        )
        self.db.commit()

    def calculate_cumulative_gpa(self):
        self.db.execute(
            text("""
            UPDATE student_semester_stats sss
            SET cumulative_gpa = sub.cum_gpa
            FROM (
                SELECT
                    student_id,
                    semester_id,
                    ROUND(
                        AVG(score_4) OVER (
                            PARTITION BY student_id
                            ORDER BY semester_id
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                        ), 2
                    ) AS cum_gpa
                FROM (
                    SELECT
                        sc.student_id,
                        cs.semester_id,
                        sc.score_4
                    FROM student_scores sc
                    JOIN course_sections cs ON cs.id = sc.section_id
                ) t
            ) sub
            WHERE sss.student_id = sub.student_id
            AND sss.semester_id = sub.semester_id
        """)
        )
        self.db.commit()

    def _regenerate_warnings_from_db_rules(self) -> None:
        from app.application.use_cases.warnings.regenerate_academic_warnings import (
            RegenerateAcademicWarningsUseCase,
        )
        from app.infrastructure.database.repositories.academic_warning_repository_impl import (
            AcademicWarningRepositoryImpl,
        )
        from app.infrastructure.database.repositories.student_stat_repository_impl import (
            StudentStatRepositoryImpl,
        )
        from app.infrastructure.database.repositories.warning_rule_repository_impl import (
            WarningRuleRepositoryImpl,
        )

        usecase = RegenerateAcademicWarningsUseCase(
            WarningRuleRepositoryImpl(self.db),
            StudentStatRepositoryImpl(self.db),
            AcademicWarningRepositoryImpl(self.db),
        )
        usecase.execute()
