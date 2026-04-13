-- Database-first schema snapshot for Academic Warning Backend.
--
-- Apply with:
--   psql -U postgres -d academic_warning_db -f schema.sql
--
-- Notes:
-- - This schema covers the tables that are used directly by the backend code paths
--   (import scores, warning regeneration, ML prediction, auth/refresh tokens).
-- - If you already have an existing DB schema, you can skip applying this file and
--   instead run `alembic stamp head` to start tracking migrations.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Core reference tables
CREATE TABLE IF NOT EXISTS academic_years (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS faculties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS majors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    faculty_id UUID NOT NULL REFERENCES faculties(id) ON DELETE CASCADE,
    UNIQUE (name, faculty_id)
);

CREATE TABLE IF NOT EXISTS classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_code TEXT UNIQUE NOT NULL,
    major_id UUID NOT NULL REFERENCES majors(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE
);

DO $$
BEGIN
    CREATE TYPE gender_type AS ENUM ('male', 'female');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE student_status_type AS ENUM ('studying', 'dismissed');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_code TEXT UNIQUE NOT NULL,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    gender gender_type NOT NULL,
    date_of_birth DATE NULL,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
    status student_status_type NOT NULL DEFAULT 'studying',
    enrollment_year INT NOT NULL,
    created_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_students_student_code ON students (student_code);

CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    credits INT NOT NULL DEFAULT 3,
    faculty_id UUID NOT NULL REFERENCES faculties(id) ON DELETE CASCADE,
    UNIQUE (name, faculty_id)
);

CREATE TABLE IF NOT EXISTS semesters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    semester_name TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    start_date DATE NULL,
    UNIQUE (semester_name, academic_year_id)
);

CREATE TABLE IF NOT EXISTS course_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    semester_id UUID NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    section_code TEXT NOT NULL,
    UNIQUE (subject_id, semester_id, section_code)
);

-- Scores + enrollment
CREATE TABLE IF NOT EXISTS student_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES course_sections(id) ON DELETE CASCADE,
    score_10 NUMERIC(5,2) NULL,
    score_4 NUMERIC(4,2) NULL,
    letter_grade TEXT NULL,
    UNIQUE (student_id, section_id)
);

CREATE TABLE IF NOT EXISTS enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES course_sections(id) ON DELETE CASCADE,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, section_id)
);

-- Aggregated semester stats
CREATE TABLE IF NOT EXISTS student_semester_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    semester_id UUID NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    total_subjects INT NULL,
    total_failed INT NULL,
    semester_gpa NUMERIC(3,2) NULL,
    cumulative_gpa NUMERIC(3,2) NULL,
    created_at TIMESTAMPTZ NULL,
    UNIQUE (student_id, semester_id)
);

-- Warning rules (DB-configurable)
DO $$
BEGIN
    CREATE TYPE rule_type_enum AS ENUM ('fail_ratio', 'semester_gpa', 'cumulative_gpa');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE comparison_operator_enum AS ENUM ('<', '<=', '>', '>=', '=');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS warning_rule_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS warning_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_set_id UUID NOT NULL REFERENCES warning_rule_sets(id) ON DELETE CASCADE,
    rule_type rule_type_enum NOT NULL,
    min_year INT NOT NULL DEFAULT 1,
    max_year INT NOT NULL DEFAULT 10,
    threshold NUMERIC(4,2) NOT NULL,
    comparison_operator comparison_operator_enum NOT NULL DEFAULT '<',
    created_at TIMESTAMPTZ NULL
);

-- Academic warnings generated
DO $$
BEGIN
    CREATE TYPE warning_level_type AS ENUM ('normal', 'warning');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE warning_status_type AS ENUM ('open', 'closed', 'review');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS academic_warnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    semester_id UUID NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    total_subjects INT NULL,
    total_failed INT NULL,
    fail_ratio NUMERIC(5,2) NULL,
    semester_gpa NUMERIC(3,2) NULL,
    cumulative_gpa NUMERIC(3,2) NULL,
    warning_level warning_level_type NOT NULL DEFAULT 'normal',
    warning_reason TEXT NULL,
    warning_status warning_status_type NOT NULL DEFAULT 'open',
    warning_note TEXT NULL,
    rule_set_id UUID NULL REFERENCES warning_rule_sets(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NULL,
    UNIQUE (student_id, semester_id)
);

-- Auth tables (refresh token)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token TEXT UNIQUE NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Users (admin/faculty_manager)
DO $$
BEGIN
    CREATE TYPE user_role_type AS ENUM ('admin', 'faculty_manager');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role user_role_type NOT NULL,
    faculty_id UUID NULL REFERENCES faculties(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);

-- Notification logs (optional but used by admin email endpoint)
CREATE TABLE IF NOT EXISTS notification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NULL,
    semester_id UUID NULL,
    warning_id UUID NULL,
    message TEXT NOT NULL,
    sent_via TEXT NOT NULL,
    sent_at TIMESTAMPTZ NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

