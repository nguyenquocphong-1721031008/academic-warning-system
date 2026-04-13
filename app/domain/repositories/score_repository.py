from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.score import Score


class ScoreRepository(ABC):
    @abstractmethod
    def save_scores(self, scores: List[Score]) -> int: ...
