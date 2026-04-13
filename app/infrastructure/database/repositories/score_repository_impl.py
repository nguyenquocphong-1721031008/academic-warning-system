from typing import List
from sqlalchemy.orm import Session
from psycopg2.extras import execute_values
from app.domain.repositories.score_repository import ScoreRepository
from app.domain.entities.score import Score


class ScoreRepositoryImpl(ScoreRepository):
    def __init__(self, db: Session):
        self.db = db

    def save_scores(self, scores: List[Score]) -> int:
        if not scores:
            return 0

        query = """
        INSERT INTO student_scores
        (
            student_id,
            section_id,
            score_10,
            score_4,
            letter_grade
        )
        VALUES %s
        ON CONFLICT (student_id, section_id) DO NOTHING
        """

        values = [
            (
                score.student_id,
                score.section_id,
                score.score_10,
                score.score_4,
                score.letter_grade,
            )
            for score in scores
        ]

        conn = self.db.connection().connection
        cur = conn.cursor()

        execute_values(cur, query, values, page_size=5000)

        conn.commit()
        cur.close()

        return len(values)
